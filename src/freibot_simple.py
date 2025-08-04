import os
from pathlib import Path
from typing import List, Dict, Any
import logging
from dataclasses import dataclass

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.schema import Document
import anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleClaude:
    """Simple Claude client for our RAG system"""
    
    def __init__(self, model: str = "claude-3-haiku-20240307", max_tokens: int = 2000):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model
        self.max_tokens = max_tokens
    
    def generate(self, prompt: str) -> str:
        """Generate response using Claude"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return f"Entschuldigung, es gab einen Fehler bei der Verarbeitung Ihrer Anfrage: {e}"

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
        self.embeddings = OpenAIEmbeddings(model=embeddings_model)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # Larger chunks for Claude's better context handling
            chunk_overlap=300,
            separators=["\n\n", "\n", " ", ""]
        )
        
    def extract_metadata_from_filename(self, filename: str) -> DocumentMetadata:
        """Extract metadata from PDF filename"""
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
            metadata = self.extract_metadata_from_filename(pdf_path.name)
            loader = PyPDFLoader(str(pdf_path))
            pages = loader.load()
            
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
    
    def create_vectorstore(self, documents: List[Document], persist_directory: str = "data/vectorstore") -> Chroma:
        """Create and persist vector store from documents"""
        logger.info("Creating vector store...")
        
        batch_size = 50
        vectorstore = None
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size} ({len(batch)} documents)")
            
            if vectorstore is None:
                vectorstore = Chroma.from_documents(
                    documents=batch,
                    embedding=self.embeddings,
                    persist_directory=persist_directory
                )
            else:
                vectorstore.add_documents(batch)
        
        logger.info(f"Vector store created with {len(documents)} documents")
        return vectorstore

class FreibotRAG:
    """Main RAG system for Freiburg questions using Claude"""
    
    def __init__(self, vectorstore_path: str = "data/vectorstore", claude_model: str = "claude-3-haiku-20240307"):
        self.vectorstore_path = vectorstore_path
        self.embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        self.claude = SimpleClaude(model=claude_model, max_tokens=2000)
        self.vectorstore = None
        
    def load_vectorstore(self) -> bool:
        """Load existing vector store"""
        try:
            self.vectorstore = Chroma(
                persist_directory=self.vectorstore_path,
                embedding_function=self.embeddings
            )
            logger.info("Vector store loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            return False
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """Ask a question about Freiburg data using Claude"""
        if not self.vectorstore:
            return {"error": "Vector store not loaded. Please run the ingestion process first."}
        
        try:
            # Retrieve relevant documents
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 8})
            docs = retriever.get_relevant_documents(question)
            
            # Build context from retrieved documents
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Claude-optimized German prompt
            claude_prompt = f"""Du bist ein Experte für Freiburg im Breisgau und hilfst Bürgern dabei, 
statistische Daten und Informationen über ihre Stadt zu verstehen.

Beantworte die folgende Frage basierend ausschließlich auf den bereitgestellten Dokumenten 
über Freiburg. Antworte präzise, sachlich und auf Deutsch.

Wichtige Hinweise:
- Nutze nur Informationen aus den bereitgestellten Quellen
- Gib konkrete Zahlen und Daten an, wenn verfügbar
- Erwähne die Quelle und das Jahr der Daten wenn möglich
- Falls die Information nicht in den Dokumenten steht, sage das ehrlich
- Strukturiere längere Antworten mit Aufzählungen oder Absätzen

KONTEXT AUS DEN FREIBURG-DOKUMENTEN:
{context}

FRAGE: {question}

Bitte antworte auf Deutsch und nutze die Informationen aus dem bereitgestellten Kontext."""
            
            # Get response from Claude
            answer = self.claude.generate(claude_prompt)
            
            # Extract source information
            sources = []
            for doc in docs:
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
                "answer": answer,
                "sources": sources,
                "question": question
            }
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            return {"error": f"Error processing question: {str(e)}"}

def main():
    """Main function to process documents and create vector store"""
    print("Freibot Document Processing Pipeline (Claude Edition)")
    print("=" * 60)
    
    # Check for API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return
        
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set")
        return
    
    processor = FreibotDocumentProcessor()
    
    print("\nProcessing PDF documents...")
    documents = processor.process_all_pdfs()
    
    if not documents:
        print("ERROR: No documents were processed successfully")
        return
    
    print("\nCreating vector store...")
    vectorstore = processor.create_vectorstore(documents)
    
    print("\nDocument processing complete!")
    print(f"Processed {len(documents)} document chunks")
    
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
        else:
            print(f"Test failed: {result['error']}")

if __name__ == "__main__":
    main()
