import os
from pathlib import Path
from typing import List, Dict, Any
import logging
from dataclasses import dataclass

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain.llms.base import LLM
from qdrant_client import QdrantClient
import anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeLLM(LLM):
    """Custom LangChain wrapper for Claude"""
    model: str = "claude-3-haiku-20240307"
    max_tokens: int = 1000
    claude_client: Any = None
    
    def __init__(self, model: str = "claude-3-haiku-20240307", max_tokens: int = 1000, **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.max_tokens = max_tokens
        self.claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    def _call(self, prompt: str, stop=None) -> str:
        """Call Claude API"""
        try:
            response = self.claude_client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return f"Entschuldigung, es gab einen Fehler bei der Verarbeitung Ihrer Anfrage: {e}"
    
    @property
    def _llm_type(self) -> str:
        return "claude"

@dataclass
class DocumentMetadata:
    """Metadata for processed documents"""
    filename: str
    title: str
    document_type: str
    year: str
    source: str = "fritz.freiburg.de"

class FreibotDocumentProcessor:
    """Process PDF documents for the Freibot RAG system with Claude support"""
    
    def __init__(self, pdf_directory: str = "data/pdfs", embeddings_model: str = "text-embedding-ada-002"):
        self.pdf_directory = Path(pdf_directory)
        # For now, we still use OpenAI embeddings as they're excellent and cost-effective
        # Later we could switch to local German embeddings
        self.embeddings = OpenAIEmbeddings(model=embeddings_model)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # Larger chunks for Claude's better context handling
            chunk_overlap=300,
            separators=["\n\n", "\n", " ", ""]
        )
        
    def extract_metadata_from_filename(self, filename: str) -> DocumentMetadata:
        """Extract metadata from PDF filename"""
        # Try to extract year and document type
        name_parts = filename.replace('.pdf', '').split('_')
        
        # Look for year (4 digits)
        year = "unknown"
        for part in name_parts:
            if part.isdigit() and len(part) == 4:
                year = part
                break
        
        # Determine document type
        filename_lower = filename.lower()
        if "wahl" in filename_lower:
            doc_type = "Wahlanalyse"
        elif "umfrage" in filename_lower:
            doc_type = "Bürgerumfrage"
        elif "sozialbericht" in filename_lower:
            doc_type = "Sozialbericht"
        elif "jahrbuch" in filename_lower or "jahresbericht" in filename_lower:
            doc_type = "Statistischer Bericht"
        elif "atlas" in filename_lower:
            doc_type = "Stadtbezirksatlas"
        else:
            doc_type = "Statistischer Bericht"
        
        return DocumentMetadata(
            filename=filename,
            title=filename.replace('.pdf', '').replace('_', ' '),
            document_type=doc_type,
            year=year
        )
    
    def process_pdf(self, pdf_path: Path) -> List[Document]:
        """Process a single PDF file into LangChain documents"""
        logger.info(f"Processing PDF: {pdf_path.name}")
        
        try:
            # Extract metadata
            metadata = self.extract_metadata_from_filename(pdf_path.name)
            
            # Load PDF
            loader = PyPDFLoader(str(pdf_path))
            pages = loader.load()
            
            # Enhance metadata for each page
            enhanced_pages = []
            for i, page in enumerate(pages):
                page.metadata.update({
                    'filename': metadata.filename,
                    'title': metadata.title,
                    'document_type': metadata.document_type,
                    'year': metadata.year,
                    'source': metadata.source,
                    'page_number': i + 1,
                    'total_pages': len(pages)
                })
                enhanced_pages.append(page)
            
            # Split into chunks
            documents = self.text_splitter.split_documents(enhanced_pages)
            
            logger.info(f"Created {len(documents)} chunks from {pdf_path.name}")
            return documents
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}")
            return []
    
    def process_all_pdfs(self) -> List[Document]:
        """Process all PDFs in the directory"""
        all_documents = []
        
        pdf_files = list(self.pdf_directory.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_path in pdf_files:
            documents = self.process_pdf(pdf_path)
            all_documents.extend(documents)
        
        logger.info(f"Total documents created: {len(all_documents)}")
        return all_documents
    
    def create_vectorstore(self, documents: List[Document], persist_directory: str = "data/vectorstore") -> Qdrant:
        """Create and persist vector store from documents"""
        logger.info("Creating vector store...")
        
        # Connect to Qdrant
        client = QdrantClient(host="qdrant", port=6333)
        collection_name = "freibot"
        
        # Create vectorstore with all documents
        vectorstore = Qdrant.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name=collection_name,
            url="http://qdrant:6333"
        )
        
        logger.info(f"Vector store created with {len(documents)} documents")
        return vectorstore

class FreibotRAG:
    """Main RAG system for Freiburg questions using Claude"""
    
    def __init__(self, vectorstore_path: str = "data/vectorstore", claude_model: str = "claude-3-haiku-20240307"):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        self.llm = ClaudeLLM(model=claude_model, max_tokens=2000)
        self.client = QdrantClient(host="qdrant", port=6333)
        self.collection_name = "freibot"
        self.vectorstore = None
        self.qa_chain = None
        
    def load_vectorstore(self) -> bool:
        """Load existing vector store"""
        try:
            # Connect to existing Qdrant collection
            self.vectorstore = Qdrant(
                client=self.client,
                collection_name=self.collection_name,
                embeddings=self.embeddings
            )
            
            # Create QA chain with more retrieval for Claude's better context handling
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 8}  # More context for Claude
                ),
                return_source_documents=True
            )
            
            logger.info("Vector store loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            return False
    
    def ask_question_with_history(self, question: str, history: List) -> Dict[str, Any]:
        """Ask question with optimized context management"""
        if not self.qa_chain:
            return {"error": "Vector store not loaded"}
        
        try:
            # Get relevant docs with adaptive retrieval
            docs = self._get_adaptive_context(question, len(history))
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Build conversation context (max 8k tokens)
            conversation_context = self._build_conversation_context(history)
            
            # Token-optimized prompt
            claude_prompt = f"""Freiburg-Experte. Beantworte basierend auf Dokumenten und Gesprächskontext.

{conversation_context}

DOKUMENTE:
{context[:6000]}  

FRAGE: {question}

Antworte präzise auf Deutsch. Nenne Quellen und Jahr."""
            
            response = self.llm._call(claude_prompt)
            
            return {
                "answer": response,
                "sources": self._extract_sources(docs),
                "question": question
            }
            
        except Exception as e:
            logger.error(f"Error with history: {e}")
            return {"error": str(e)}
    
    def _get_adaptive_context(self, question: str, history_length: int) -> List:
        """Adaptive retrieval: fewer docs for longer conversations"""
        k = max(4, 8 - (history_length // 4))  # 8→4 docs as history grows
        return self.vectorstore.similarity_search(question, k=k)
    
    def _build_conversation_context(self, history: List) -> str:
        """Build efficient conversation context"""
        if len(history) <= 1:
            return ""
        
        context = "GESPRÄCH:\n"
        for msg in history[:-1]:  # Exclude current question
            role = "F" if msg.role == "user" else "A"
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            context += f"{role}: {content}\n"
        
        return context[:2000]  # Hard limit
    
    def _extract_sources(self, docs) -> List[Dict[str, Any]]:
        """Extract unique source metadata"""
        sources = []
        seen = set()
        
        for doc in docs:
            key = (doc.metadata.get("filename", ""), doc.metadata.get("page_number", ""))
            if key not in seen:
                sources.append({
                    "title": doc.metadata.get("title", "Unknown"),
                    "document_type": doc.metadata.get("document_type", "Unknown"), 
                    "year": doc.metadata.get("year", "Unknown"),
                    "page": doc.metadata.get("page_number", "Unknown"),
                    "filename": doc.metadata.get("filename", "Unknown")
                })
                seen.add(key)
        
        return sources[:5]  # Max 5 sources
        """Ask a question about Freiburg data using Claude"""
        if not self.qa_chain:
            return {
                "error": "Vector store not loaded. Please run the ingestion process first."
            }
        
        try:
            # Claude-optimized German prompt
            claude_prompt = f"""Du bist ein Experte für Freiburg im Breisgau und hilfst Bürgern dabei, 
            statistische Daten und Informationen über ihre Stadt zu verstehen.

            Beantworte die folgende Frage basierend ausschließlich auf den bereitgestellten Dokumenten 
            über Freiburg. Antworte präzise, sachlich und auf Deutsch.

            Wichtige Hinweise:
            - Nutze nur Informationen aus den bereitgestellten Quellen
            - Gib konkrete Zahlen und Daten an, wenn verfügbar
            - Erwähne die Quelle und das Jahr der Daten
            - Falls die Information nicht in den Dokumenten steht, sage das ehrlich
            - Strukturiere längere Antworten mit Aufzählungen oder Absätzen

            Frage: {question}

            Bitte antworte auf Deutsch und zitiere die verwendeten Quellen."""
            
            result = self.qa_chain({"query": claude_prompt})
            
            # Extract source information
            sources = []
            for doc in result.get("source_documents", []):
                source_info = {
                    "title": doc.metadata.get("title", "Unknown"),
                    "document_type": doc.metadata.get("document_type", "Unknown"),
                    "year": doc.metadata.get("year", "Unknown"),
                    "page": doc.metadata.get("page_number", "Unknown"),
                    "filename": doc.metadata.get("filename", "Unknown")
                }
                if source_info not in sources:
                    sources.append(source_info)
            
            return {
                "answer": result["result"],
                "sources": sources,
                "question": question
            }
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            return {
                "error": f"Error processing question: {str(e)}"
            }

def main():
    """Main function to process documents and create vector store"""
    print("Freibot Document Processing Pipeline (Claude Edition)")
    print("=" * 60)
    
    # Check for API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set your Anthropic API key in the .env file")
        return
        
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set")  
        print("Note: We still need OpenAI for embeddings (very cheap)")
        print("Please set your OpenAI API key in the .env file")
        return
    
    # Initialize processor
    processor = FreibotDocumentProcessor()
    
    # Process all PDFs
    print("\nProcessing PDF documents...")
    documents = processor.process_all_pdfs()
    
    if not documents:
        print("ERROR: No documents were processed successfully")
        return
    
    # Create vector store
    print("\nCreating vector store...")
    vectorstore = processor.create_vectorstore(documents)
    
    print("\nDocument processing complete!")
    print(f"Processed {len(documents)} document chunks")
    print("You can now run the RAG system to ask questions about Freiburg")
    
    # Test the system with Claude
    print("\nTesting the RAG system with Claude...")
    rag = FreibotRAG()
    if rag.load_vectorstore():
        test_question = "Wie viele Einwohner hat Freiburg und wie hat sich die Bevölkerung entwickelt?"
        print(f"\nTest Question: {test_question}")
        print("Claude is thinking...")
        
        result = rag.ask_question(test_question)
        
        if "error" not in result:
            print(f"\nClaude's Answer: {result['answer']}")
            print(f"\nSources: {len(result['sources'])} documents")
            for i, source in enumerate(result['sources'][:3], 1):  # Show first 3 sources
                print(f"  {i}. {source['title']} ({source['year']}) - {source['document_type']}")
        else:
            print(f"Test failed: {result['error']}")

if __name__ == "__main__":
    main()
