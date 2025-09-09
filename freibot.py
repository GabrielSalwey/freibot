"""
Freibot - Minimal RAG system for Freiburg city data
Simplified single-file implementation using Haystack + VoyageAI + OpenRouter
"""

import os
import json
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses import ChatMessage
from haystack_integrations.components.embedders.voyage_embedders import VoyageTextEmbedder
from haystack_integrations.components.retrievers.chroma import ChromaEmbeddingRetriever
from haystack_integrations.components.generators.openrouter import OpenRouterChatGenerator
from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from haystack.utils.auth import Secret

# Import web interface
from web import get_web_interface

# Load environment variables
load_dotenv()

# Configuration
VOYAGE_MODEL = "voyage-3-large"
LLM_MODEL = "openai/gpt-5-mini"
VECTORSTORE_PATH = "./data/vectorstore"
COLLECTION_NAME = "freiburg_docs_v3large"

# Initialize ChromaDB store
store = ChromaDocumentStore(
    persist_path=VECTORSTORE_PATH,
    collection_name=COLLECTION_NAME
)

# Request model
class QuestionRequest(BaseModel):
    question: str
    privacy_mode: bool = False
    session_id: str = None

# Lifespan handler for startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize pipeline and check vectorstore on startup."""
    global rag_pipeline
    
    # Check API keys
    if not os.getenv("VOYAGE_API_KEY"):
        print("WARNING: VOYAGE_API_KEY not set")
    if not os.getenv("OPENROUTER_API_KEY"):
        print("WARNING: OPENROUTER_API_KEY not set")
    
    # Build pipeline
    print("Building RAG pipeline...")
    rag_pipeline = build_pipeline()
    
    # Check documents
    doc_count = store.count_documents()
    print(f"Documents in store: {doc_count}")
    
    if doc_count == 0:
        print("\nWARNING: No documents indexed!")
        print("Run: python scripts/index_documents.py")
    
    print("Ready!")
    
    yield  # Application runs here
    
    # Cleanup on shutdown (if needed)
    print("Shutting down...")

# Initialize FastAPI
app = FastAPI(title="Freibot", version="4.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Conversation history (session_id -> list of exchanges)
conversation_history = {}

# Global pipeline
rag_pipeline = None

def classify_query(question: str) -> tuple[bool, int]:
    """Determine if query needs retrieval and how many documents."""
    q_lower = question.lower().strip()
    
    # No retrieval: greetings, math, general knowledge
    if any(p in q_lower for p in ["hallo", "hi", "danke", "tschüss", "rechne", "was ist 2+2"]):
        if "freiburg" not in q_lower:
            return False, 0
    
    # Simple facts: 2 documents
    if any(p in q_lower for p in ["einwohner", "bürgermeister", "fläche"]):
        return True, 2
    
    # Complex queries: 3 documents
    return True, 3

def build_pipeline():
    """Build the RAG pipeline."""
    p = Pipeline()
    
    # Components
    p.add_component("embed", VoyageTextEmbedder(
        api_key=Secret.from_token(os.getenv("VOYAGE_API_KEY")),
        model=VOYAGE_MODEL,
        input_type="query"
    ))
    
    p.add_component("retrieve", ChromaEmbeddingRetriever(
        document_store=store,
        top_k=3
    ))
    
    template = """Du bist ein Assistent für Fragen zu Freiburg. Antworte basierend auf den Dokumenten.

Kontext:
{% for doc in documents %}
[{{ loop.index }}] {{ doc.content }}
---
{% endfor %}

Frage: {{ question }}

Antwort (auf Deutsch, mit Quellenangaben [1], [2] etc.):"""
    
    p.add_component("prompt", ChatPromptBuilder(
        template=[ChatMessage.from_user(template)]
    ))
    
    p.add_component("llm", OpenRouterChatGenerator(
        api_key=Secret.from_token(os.getenv("OPENROUTER_API_KEY")),
        model=LLM_MODEL,
        generation_kwargs={"temperature": 0.1, "max_tokens": 1000}
    ))
    
    # Connections
    p.connect("embed.embedding", "retrieve.query_embedding")
    p.connect("retrieve.documents", "prompt.documents")
    p.connect("prompt.prompt", "llm.messages")
    
    return p

def log_conversation(question: str, answer: str, success: bool):
    """Simple logging to file."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "answer": answer[:200],
        "success": success
    }
    
    with open("conversation_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


@app.post("/ask")
async def ask(request: QuestionRequest):
    """Answer a question using RAG."""
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    question = request.question.strip()
    if not question:
        return {"error": "Empty question", "answer": "", "sources": []}
    
    try:
        # Check if retrieval needed
        needs_retrieval, k = classify_query(question)
        
        if not needs_retrieval:
            # Direct answer without retrieval
            from haystack_integrations.components.generators.openrouter import OpenRouterChatGenerator
            
            generator = OpenRouterChatGenerator(
                api_key=Secret.from_token(os.getenv("OPENROUTER_API_KEY")),
                model=LLM_MODEL,
                generation_kwargs={"temperature": 0.1, "max_tokens": 500}
            )
            
            messages = [ChatMessage.from_user(f"Beantworte auf Deutsch: {question}")]
            result = generator.run(messages=messages)
            
            answer = result["replies"][0].text if result["replies"] else "Keine Antwort"
            sources = []
        else:
            # RAG pipeline
            retriever = rag_pipeline.get_component("retrieve")
            retriever.top_k = k
            
            result = rag_pipeline.run({
                "embed": {"text": question},
                "prompt": {"question": question}
            })
            
            # Extract answer
            answer = "Keine Antwort gefunden"
            if "llm" in result and result["llm"]["replies"]:
                answer = result["llm"]["replies"][0].text
            
            # Extract sources
            sources = []
            docs = result.get("retrieve", {}).get("documents", [])
            for i, doc in enumerate(docs[:k]):
                file_name = Path(doc.meta.get("file_path", "Unknown")).stem
                sources.append({
                    "id": i + 1,
                    "document": file_name.replace("_", " "),
                    "content": doc.content[:300] + "...",
                    "page": doc.meta.get("page_number")
                })
        
        # Update conversation history
        session_id = request.session_id or "default"
        if not request.privacy_mode:
            if session_id not in conversation_history:
                conversation_history[session_id] = []
            
            conversation_history[session_id].append({
                "question": question,
                "answer": answer,
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep last 10 exchanges
            conversation_history[session_id] = conversation_history[session_id][-10:]
        
        # Log (skip if privacy mode)
        if not request.privacy_mode:
            log_conversation(question, answer, True)
        
        return {
            "answer": answer,
            "sources": sources,
            "question": question
        }
        
    except Exception as e:
        print(f"Error: {e}")
        log_conversation(question, str(e), False)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "documents": store.count_documents(),
        "pipeline_ready": rag_pipeline is not None
    }

@app.get("/stats")
async def stats():
    """System statistics."""
    pdf_dir = Path("data/pdfs")
    pdf_count = len(list(pdf_dir.glob("*.pdf"))) if pdf_dir.exists() else 0
    
    return {
        "pdf_count": pdf_count,
        "chunk_count": store.count_documents(),
        "embedding_model": VOYAGE_MODEL,
        "llm_model": LLM_MODEL
    }

@app.post("/index")
async def index():
    """Trigger document indexing."""
    return {
        "message": "Please run: python scripts/index_documents.py",
        "current_docs": store.count_documents()
    }

@app.get("/", response_class=HTMLResponse)
async def web_interface():
    """Serve web interface."""
    return HTMLResponse(content=get_web_interface())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)