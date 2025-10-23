"""
Freibot API — RAG with Qdrant + metadata filtering
Endpoints: /ask, /health, /stats
"""

import os
import json
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses import ChatMessage
from haystack_integrations.components.embedders.voyage_embedders import VoyageTextEmbedder
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from haystack_integrations.components.generators.openrouter import OpenRouterChatGenerator
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack.utils.auth import Secret

# Import centralized configuration
from config import (
    VOYAGE_MODEL,
    VOYAGE_INPUT_TYPE_QUERY,
    EMBEDDING_DIM,
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_COLLECTION,
    LLM_MODEL
)

# Load environment variables
load_dotenv()

# Allow Chainlit (localhost:8000) by default; override with ALLOWED_ORIGINS env (comma-separated)
_default_origins = "http://localhost:8000,http://127.0.0.1:8000"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", _default_origins).split(",")

# Initialize Qdrant store with error handling
try:
    store = QdrantDocumentStore(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        index=QDRANT_COLLECTION,
        embedding_dim=EMBEDDING_DIM,
        recreate_index=False,
        return_embedding=False,
    )
    STORE_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Failed to initialize Qdrant: {e}")
    store = None
    STORE_AVAILABLE = False

# Request/response models
class AskRequest(BaseModel):
    question: str
    privacy_mode: bool = False
    session_id: Optional[str] = None
    top_k: Optional[int] = None  # optional override

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
    if STORE_AVAILABLE:
        doc_count = store.count_documents()
        print(f"Documents in store: {doc_count}")
        if doc_count == 0:
            print("\nWARNING: No documents indexed!")
            print("Run: python scripts/index_documents.py")
    else:
        print("\nWARNING: Vectorstore not available - running in fallback mode")

    print("Ready!")
    yield  # Application runs here

    # Cleanup on shutdown (if needed)
    print("Shutting down...")

# Initialize FastAPI
app = FastAPI(title="Freibot", version="4.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Conversation history (session_id -> list of exchanges)
conversation_history: Dict[str, Any] = {}

# Global pipeline
rag_pipeline: Optional[Pipeline] = None

def classify_query(question: str) -> tuple[bool, int]:
    """Determine if query needs retrieval and how many documents.
    Rationale: k ∈ {0,2,3} balances latency and answer quality.
    """
    q_lower = question.lower().strip()

    # If it's not about Freiburg (and not explicitly the Sozialbericht), don't retrieve
    if "freiburg" not in q_lower and "sozialbericht" not in q_lower:
        return False, 0

    # No retrieval: greetings/math even if Freiburg mentioned? keep small exceptions
    if any(p in q_lower for p in ["hallo", "hi", "danke", "tschüss", "was ist 2+2", "2+2"]):
        return False, 0

    # Simple facts: 2 documents (synonyms included)
    if any(p in q_lower for p in [
        "einwohner", "bürgermeister", "buergermeister",
        "fläche", "flaeche", "größe", "groesse", "groß", "gross",
        "arbeitslosenquote", "wie alt", "alter", "gründung", "gruendung", "gründungsjahr"
    ]):
        return True, 2

    # Domain triggers for full retrieval (when focused on Freiburg or Sozialbericht)
    domain_full_triggers = [
        "sozialbericht", "bezirk", "bezirke", "stadtteil", "stadtteile",
        "arbeitslosigkeit", "zufriedenheit", "entwicklung", "vergleich", "vergleiche",
    ]
    if any(t in q_lower for t in domain_full_triggers):
        return True, 3

    # Default for Freiburg-related queries
    return True, 3

def build_pipeline() -> Pipeline:
    """Build the RAG pipeline."""
    p = Pipeline()

    # Components
    p.add_component("embed", VoyageTextEmbedder(
        api_key=Secret.from_token(os.getenv("VOYAGE_API_KEY")),
        model=VOYAGE_MODEL,
        input_type=VOYAGE_INPUT_TYPE_QUERY
    ))

    p.add_component("retrieve", QdrantEmbeddingRetriever(
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
        template=[ChatMessage.from_user(template)],
        required_variables=["documents", "question"]
    ))

    p.add_component("llm", OpenRouterChatGenerator(
        api_key=Secret.from_token(os.getenv("OPENROUTER_API_KEY")),
        model=LLM_MODEL,
        generation_kwargs={"temperature": 0.1}
    ))

    # Connections
    p.connect("embed.embedding", "retrieve.query_embedding")
    p.connect("retrieve.documents", "prompt.documents")
    p.connect("prompt.prompt", "llm.messages")

    return p

def extract_filters_from_query(question: str, llm) -> dict:
    """
    Use LLM to extract metadata filters from natural language query.
    Returns Qdrant filter dict or empty dict.
    """
    # Quick check: does query mention years/filters?
    if not any(word in question.lower() for word in ["2024", "2023", "2022", "2021", "2020", "2025", "jahr", "bericht", "wahl", "nur", "sozialbericht", "statistik"]):
        return {}
    
    prompt = f"""Analysiere diese Frage und extrahiere Filter für eine Dokumentensuche.

Frage: "{question}"

Verfügbare Filter:
- year (Integer): z.B. 2024, 2023
- document_type (String): "wahlbericht", "sozialbericht", "statistik", "studie", "sonstiges"

Gib NUR die Filter als JSON zurück, z.B.:
{{"year": 2024}}
oder
{{"year": 2024, "document_type": "sozialbericht"}}
oder
{{}}  (wenn keine Filter erkennbar)

Antwort (nur JSON):"""

    try:
        messages = [ChatMessage.from_user(prompt)]
        result = llm.run(messages=messages)
        response = result["replies"][0].text.strip()
        
        # Parse JSON
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        
        filters = json.loads(response.strip())
        
        # Convert to Qdrant filter format
        qdrant_filters = {}
        if "year" in filters and filters["year"]:
            qdrant_filters["year"] = filters["year"]
        if "document_type" in filters and filters["document_type"]:
            qdrant_filters["document_type"] = filters["document_type"]
        
        return qdrant_filters
    except Exception as e:
        print(f"Filter extraction failed: {e}")
        return {}

def log_conversation(question: str, answer: str, success: bool):
    """Simple logging to file."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "answer": answer[:200],
        "success": success
    }

    os.makedirs("logs", exist_ok=True)
    with open("logs/conversation_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

@app.post("/ask")
async def ask(request: AskRequest):
    """Answer a question using RAG."""
    if not rag_pipeline:
        raise HTTPException(status_code=503, detail="System not initialized")

    question = request.question.strip()
    if not question:
        return {"error": "Empty question", "answer": "", "sources": []}

    try:
        # Determine retrieval policy
        needs_retrieval, k_default = classify_query(question)
        k = request.top_k if request.top_k is not None else k_default

        if not needs_retrieval or not STORE_AVAILABLE or k == 0:
            # Direct answer without retrieval (reuse pipeline component)
            llm_component = rag_pipeline.get_component("llm") if rag_pipeline else None

            if llm_component:
                messages = [ChatMessage.from_user(f"Beantworte auf Deutsch: {question}")]
                result = llm_component.run(messages=messages)
                answer = result["replies"][0].text if result["replies"] else "Keine Antwort"
            else:
                answer = "System nicht verfügbar. Bitte versuchen Sie es später erneut."
            sources = []
        else:
            # Extract filters from query using LLM
            llm_component = rag_pipeline.get_component("llm")
            filters = extract_filters_from_query(question, llm_component)
            
            # RAG pipeline for answer
            retriever = rag_pipeline.get_component("retrieve")
            retriever.top_k = k
            if filters:
                retriever.filters = filters
                print(f"Applying filters: {filters}")

            result = rag_pipeline.run({
                "embed": {"text": question},
                "prompt": {"question": question}
            })

            # Extract answer
            answer = "Keine Antwort gefunden"
            if "llm" in result and result["llm"]["replies"]:
                answer = result["llm"]["replies"][0].text

            # Extract sources from pipeline result first (avoid extra embed/retrieve for latency)
            docs = []
            try:
                docs = result.get("retrieve", {}).get("documents", []) or []
            except Exception:
                docs = []

            # Fallback: direct retriever call if pipeline outputs don't include documents
            if not docs:
                try:
                    embed_component = rag_pipeline.get_component("embed")
                    emb_res = embed_component.run(text=question)
                    query_emb = emb_res.get("embedding")
                    ret_res = retriever.run(query_embedding=query_emb)
                    docs = ret_res.get("documents", [])
                except Exception:
                    docs = []

            sources = []
            for i, doc in enumerate(docs[:k]):
                file_name = Path(doc.meta.get("file_path", "Unknown")).stem
                content_text = getattr(doc, "text", None) or getattr(doc, "content", "")
                sources.append({
                    "id": i + 1,
                    "document": doc.meta.get("title", file_name.replace("_", " ")),
                    "content": (content_text[:300] + "...") if content_text else "",
                    "year": doc.meta.get("year"),
                    "type": doc.meta.get("document_type"),
                    "page": doc.meta.get("page_number")
                })

        # Update conversation history (skip in privacy mode)
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

            # Log
            log_conversation(question, answer, True)

        return {
            "answer": answer,
            "sources": sources,
            "meta": {
                "retrieval_k": k if needs_retrieval else 0,
                "filters_applied": filters if (needs_retrieval and 'filters' in locals()) else {},
                "embedding_model": f"{VOYAGE_MODEL} (512-dim, int8)",
                "llm_model": LLM_MODEL
            }
        }

    except Exception as e:
        print(f"Error: {e}")
        if not request.privacy_mode:
            log_conversation(question, str(e), False)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check."""
    doc_count = store.count_documents() if STORE_AVAILABLE else 0
    embeddings_available = bool(os.getenv("VOYAGE_API_KEY"))
    llm_available = bool(os.getenv("OPENROUTER_API_KEY"))
    return {
        "status": "healthy" if STORE_AVAILABLE else "degraded",
        "documents": doc_count,
        "pipeline_ready": rag_pipeline is not None,
        "vectorstore_available": STORE_AVAILABLE,
        "embeddings_available": embeddings_available,
        "llm_available": llm_available
    }

@app.get("/stats")
async def stats():
    """System statistics."""
    pdf_dir = Path("data/pdfs")
    pdf_count = len(list(pdf_dir.glob("*.pdf"))) if pdf_dir.exists() else 0
    chunk_count = store.count_documents() if STORE_AVAILABLE else 0

    return {
        "pdf_count": pdf_count,
        "chunk_count": chunk_count,
        "embedding_model": f"{VOYAGE_MODEL} (512-dim, int8)",
        "llm_model": LLM_MODEL,
        "vectorstore_available": STORE_AVAILABLE
    }

@app.post("/index")
async def index():
    """Trigger document indexing."""
    current_docs = store.count_documents() if STORE_AVAILABLE else 0
    return {
        "message": "Please run: python scripts/index_documents.py",
        "current_docs": current_docs,
        "vectorstore_available": STORE_AVAILABLE
    }

class DebugRetrieveRequest(BaseModel):
    question: str
    top_k: int = 3

@app.post("/debug/retrieve")
async def debug_retrieve(req: DebugRetrieveRequest):
    """Debug endpoint: run only embedding + retriever and return top docs.
    This helps diagnose retrieval issues independently of prompting/LLM.
    """
    if not rag_pipeline or not STORE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Pipeline or vectorstore not available")
    try:
        # Embed the query
        embed_component = rag_pipeline.get_component("embed")
        emb_res = embed_component.run(text=req.question)
        query_emb = emb_res.get("embedding")

        # Run retriever with override k
        retriever = rag_pipeline.get_component("retrieve")
        retriever.top_k = req.top_k
        ret_res = retriever.run(query_embedding=query_emb)
        docs = ret_res.get("documents", [])

        # Prepare minimal debug info
        out = []
        for i, d in enumerate(docs, 1):
            # Access text/content safely across haystack versions
            content = getattr(d, "text", None) or getattr(d, "content", "")
            out.append({
                "rank": i,
                "id": getattr(d, "id", None),
                "content_preview": (content[:200] + "...") if content else "",
                "meta": d.meta
            })
        return {"count": len(out), "docs": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
