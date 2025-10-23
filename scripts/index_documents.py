"""
Freibot document indexing — PDF → embeddings (Qdrant + VoyageAI).

Processes PDFs in data/pdfs into embeddings and writes them to Qdrant
vectorstore with LLM-extracted metadata for filtering.

Run this before starting the API (api.py) if no vectorstore exists, or use
--mode append to add newly added PDFs without clearing existing data.
"""

import os
import sys
import time
import json
from pathlib import Path
from collections import deque
from dotenv import load_dotenv

from haystack import Pipeline
from haystack.components.converters import PyPDFToDocument
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack_integrations.components.embedders.voyage_embedders import VoyageDocumentEmbedder
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack.utils.auth import Secret

# Import metadata extractor
sys.path.insert(0, str(Path(__file__).parent))
from extract_metadata import extract_all_metadata

# Load environment variables
load_dotenv()

# ========== CONFIGURATION ==========
# Modify these settings to control indexing behavior

PDF_DIR = "data/pdfs"                          # Directory containing PDFs to index
QDRANT_HOST = "localhost"                     # Qdrant host
QDRANT_PORT = 6333                            # Qdrant port
QDRANT_COLLECTION = "freiburg_docs_v1"        # Collection name (must match api.py)
EMBEDDING_DIM = 1024                           # Voyage-3-large default dimension

# Chunking configuration
CHUNK_METHOD = "sentence"                      # "sentence", "word", or "passage"
CHUNK_SIZE = 4                                 # Number of units per chunk
CHUNK_OVERLAP = 1                              # Overlap between chunks
CHUNK_THRESHOLD = 0                            # Minimum chunk size

# Model configuration
EMBEDDING_MODEL = "voyage-3-large"             # Voyage embedding model (512-dim, int8)
INPUT_TYPE = "document"                        # Input type for embeddings

# Rate limiting (VoyageAI limits: 2000 RPM, 20M TPM)
MAX_REQUESTS_PER_MINUTE = 1800                 # Conservative: 90% of limit
MAX_TOKENS_PER_MINUTE = 15_000_000            # Conservative: 75% of limit
ESTIMATED_TOKENS_PER_PDF = 10000              # Rough estimate

# ========== END CONFIGURATION ==========


class SimpleRateLimiter:
    """Rate limiter for VoyageAI API calls"""
    def __init__(self, max_requests_per_minute=MAX_REQUESTS_PER_MINUTE, max_tokens_per_minute=MAX_TOKENS_PER_MINUTE):
        self.max_rpm = max_requests_per_minute  
        self.max_tpm = max_tokens_per_minute
        self.request_times = deque()
        self.token_usage = deque()
    
    def wait_if_needed(self, estimated_tokens=ESTIMATED_TOKENS_PER_PDF):
        """Wait if we would exceed rate limits"""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old entries
        while self.request_times and self.request_times[0] < minute_ago:
            self.request_times.popleft()
        while self.token_usage and self.token_usage[0][0] < minute_ago:
            self.token_usage.popleft()
        
        # Check RPM limit
        if len(self.request_times) >= self.max_rpm:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                print(f"  Rate limiting: waiting {sleep_time:.1f}s (RPM limit)")
                time.sleep(sleep_time)
                return self.wait_if_needed(estimated_tokens)
        
        # Check TPM limit
        current_tokens = sum(tokens for _, tokens in self.token_usage)
        if current_tokens + estimated_tokens > self.max_tpm:
            sleep_time = 60 - (now - self.token_usage[0][0])
            if sleep_time > 0:
                print(f"  Rate limiting: waiting {sleep_time:.1f}s (TPM limit)")
                time.sleep(sleep_time)
                return self.wait_if_needed(estimated_tokens)
        
        # Record this request
        self.request_times.append(now)
        self.token_usage.append((now, estimated_tokens))


from haystack import component
from typing import List
from haystack.dataclasses import Document

@component
class MetadataInjector:
    """Inject PDF-level metadata into all document chunks."""
    def __init__(self, metadata: dict):
        self.metadata = metadata
    
    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document]):
        """Add metadata to all documents."""
        for doc in documents:
            doc.meta.update(self.metadata)
        return {"documents": documents}

def build_index_pipeline(store, pdf_metadata=None):
    """Build Haystack pipeline for indexing PDFs with metadata."""
    p = Pipeline()
    
    # PDF converter
    p.add_component("pdf", PyPDFToDocument())
    
    # Document splitter with configurable chunking
    p.add_component("split", DocumentSplitter(
        split_by=CHUNK_METHOD,
        split_length=CHUNK_SIZE,
        split_overlap=CHUNK_OVERLAP,
        split_threshold=CHUNK_THRESHOLD
    ))
    
    # Metadata injector (if metadata provided)
    if pdf_metadata:
        p.add_component("inject_meta", MetadataInjector(metadata=pdf_metadata))
    
    # Voyage embedder
    p.add_component("embed", VoyageDocumentEmbedder(
        api_key=Secret.from_token(os.getenv("VOYAGE_API_KEY")),
        model=EMBEDDING_MODEL,
        input_type=INPUT_TYPE
    ))
    
    # Document writer
    p.add_component("write", DocumentWriter(document_store=store))
    
    # Connect pipeline
    p.connect("pdf", "split")
    if pdf_metadata:
        p.connect("split", "inject_meta")
        p.connect("inject_meta", "embed")
    else:
        p.connect("split", "embed")
    p.connect("embed", "write")
    
    return p


def clear_vectorstore(store):
    """Clear all documents from the vectorstore"""
    try:
        # Qdrant: delete collection and recreate
        store.delete_index()
        print(f"Cleared vectorstore (recreated collection)")
    except Exception as e:
        print(f"Note: Could not clear vectorstore (might be empty): {e}")


def index_pdfs(mode="full"):
    """
    Index PDFs into Qdrant vectorstore with metadata
    
    Args:
        mode: "full" (clear and reindex) or "append" (add new documents)
    """
    print("=" * 60)
    print("Freibot Document Indexing (Qdrant + Metadata)")
    print("=" * 60)
    
    # Check environment
    if not os.getenv("VOYAGE_API_KEY"):
        print("ERROR: VOYAGE_API_KEY not set in .env file")
        return False
    if not os.getenv("OPENROUTER_API_KEY"):
        print("ERROR: OPENROUTER_API_KEY not set (needed for metadata extraction)")
        return False
    
    # Initialize Qdrant
    print(f"\nInitializing Qdrant:")
    print(f"  Host: {QDRANT_HOST}:{QDRANT_PORT}")
    print(f"  Collection: {QDRANT_COLLECTION}")
    
    store = QdrantDocumentStore(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        index=QDRANT_COLLECTION,
        embedding_dim=EMBEDDING_DIM,
        recreate_index=(mode == "full"),
        return_embedding=False,
        wait_result_from_api=True,
    )
    
    # Check current state
    existing_docs = store.count_documents()
    print(f"  Existing documents: {existing_docs}")
    
    # Handle mode
    if mode == "full" and existing_docs > 0:
        print(f"\nFull reindex mode - clearing {existing_docs} existing documents...")
        clear_vectorstore(store)
        existing_docs = 0
    elif mode == "append":
        print(f"\nAppend mode - keeping {existing_docs} existing documents")
    
    # Find PDFs
    pdf_dir = Path(PDF_DIR)
    if not pdf_dir.exists():
        print(f"\nERROR: PDF directory not found: {pdf_dir}")
        return False
    
    pdfs = list(pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"\nNo PDFs found in {pdf_dir}")
        return False
    
    print(f"\nFound {len(pdfs)} PDFs to process")
    
    # Extract metadata first
    print(f"\n{'='*60}")
    print("Phase 1: Metadata Extraction (LLM)")
    print('='*60)
    
    # Load cached metadata if exists
    metadata_cache_path = Path("data/metadata_cache.json")
    if metadata_cache_path.exists():
        print(f"Loading cached metadata from {metadata_cache_path}")
        with open(metadata_cache_path, "r", encoding="utf-8") as f:
            metadata_map = json.load(f)
        print(f"Loaded metadata for {len(metadata_map)} PDFs")
    else:
        print("No cached metadata found, extracting...")
        metadata_map = extract_all_metadata(pdf_dir)
    
    # Display configuration
    print(f"\n{'='*60}")
    print("Phase 2: Embedding & Indexing")
    print('='*60)
    print(f"Chunking: {CHUNK_METHOD}, size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}")
    print(f"Model: {EMBEDDING_MODEL} ({EMBEDDING_DIM}-dim)")
    
    # Initialize rate limiter
    rate_limiter = SimpleRateLimiter()
    
    # Process PDFs
    print(f"\nProcessing PDFs:")
    print("-" * 40)
    
    indexed = 0
    errors = []
    
    for i, pdf in enumerate(pdfs, 1):
        print(f"\n[{i}/{len(pdfs)}] {pdf.name}")
        
        # Get metadata for this PDF
        pdf_metadata = metadata_map.get(pdf.name, {})
        print(f"  Metadata: year={pdf_metadata.get('year')}, type={pdf_metadata.get('document_type')}")
        
        try:
            # Rate limiting
            rate_limiter.wait_if_needed(ESTIMATED_TOKENS_PER_PDF)
            
            # Build pipeline with this PDF's metadata
            pipeline = build_index_pipeline(store, pdf_metadata)
            
            # Index the PDF
            print(f"  Indexing...", end="", flush=True)
            result = pipeline.run({"pdf": {"sources": [pdf]}})
            
            # Check result
            if "write" in result and "documents_written" in result["write"]:
                docs_written = result["write"]["documents_written"]
                print(f" OK ({docs_written} chunks)")
                indexed += 1
            else:
                print(f" OK")
                indexed += 1
                
        except Exception as e:
            print(f" FAILED")
            print(f"  Error: {e}")
            errors.append({"file": pdf.name, "error": str(e)})
            
            # If rate limit error, suggest solution
            if "rate" in str(e).lower():
                print("\n  Tip: Add payment method to VoyageAI for higher limits")
                print("       or wait and run script again to continue")
                break
    
    # Summary
    print("\n" + "=" * 60)
    print("Indexing Complete")
    print("=" * 60)
    print(f"  Successfully indexed: {indexed}/{len(pdfs)} PDFs")
    print(f"  Total documents in store: {store.count_documents()}")
    
    if errors:
        print(f"\n  Errors encountered: {len(errors)}")
        for error in errors[:5]:  # Show first 5 errors
            print(f"    - {error['file']}: {error['error'][:50]}...")
    
    print(f"\nQdrant ready at: {QDRANT_HOST}:{QDRANT_PORT}")
    print(f"  Web UI: http://localhost:6333/dashboard")
    print(f"\n  Run 'python api.py' to start the API server")
    
    return indexed > 0


def main():
    """Main entry point"""
    import argparse
    
    global PDF_DIR
    
    parser = argparse.ArgumentParser(description="Index PDFs for Freibot RAG system")
    parser.add_argument(
        "--mode", 
        choices=["full", "append"], 
        default="full",
        help="Indexing mode: 'full' clears existing data, 'append' adds to it"
    )
    parser.add_argument(
        "--pdf-dir",
        default=PDF_DIR,
        help=f"Directory containing PDFs (default: {PDF_DIR})"
    )
    
    args = parser.parse_args()
    
    # Override PDF_DIR if specified
    if args.pdf_dir != PDF_DIR:
        PDF_DIR = args.pdf_dir
        print(f"Using PDF directory: {PDF_DIR}")
    
    # Run indexing
    success = index_pdfs(mode=args.mode)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()