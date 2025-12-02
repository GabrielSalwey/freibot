"""
Pipeline orchestration for Freibot document processing.

**INPUTS:**
    - source: str or List[str] - File paths or URLs to process
    - config: dict - Pipeline configuration (chunking params, embedding model, etc.)
    
**OUTPUTS:**
    - IndexResult - Summary of indexing operation

**RESPONSIBILITIES:**
    - Orchestrate full document processing pipeline
    - Coordinate: scraping → conversion → chunking → metadata → indexing
    - Handle errors and provide progress feedback
    - Support both file-based and web-based sources
    
**DEPENDENCIES:**
    - All document_processor modules
    
**TODO:**
    - Add progress callbacks for CLI/API
    - Support resumable indexing
    - Add dry-run mode
"""

from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from .types import (
    RawDocument,
    ConvertedDocument,
    Chunk,
    EnrichedChunk,
    IndexResult,
    ChunkMethod
)


def process_pdf_directory(
    pdf_dir: str,
    store_path: str = "./data/vectorstore",
    collection: str = "freiburg_docs_v3large",
    mode: str = "full",
    chunk_method: ChunkMethod = "sentence",
    chunk_size: int = 4,
    chunk_overlap: int = 1,
    enrich_metadata: bool = False
) -> IndexResult:
    """
    Process all PDFs in a directory through full pipeline.
    
    This is the main entry point for the current MVP workflow.
    
    Args:
        pdf_dir: Directory containing PDF files
        store_path: Path to ChromaDB
        collection: Collection name
        mode: "full" (clear first) or "append"
        chunk_method: Chunking strategy
        chunk_size: Size parameter for chunking
        chunk_overlap: Overlap between chunks
        enrich_metadata: Whether to run metadata enrichment
        
    Returns:
        IndexResult with summary
    """
    raise NotImplementedError


def process_single_file(
    file_path: str,
    store_path: str = "./data/vectorstore",
    collection: str = "freiburg_docs_v3large",
    chunk_method: ChunkMethod = "sentence",
    chunk_size: int = 4,
    chunk_overlap: int = 1
) -> IndexResult:
    """
    Process a single file through the pipeline.
    
    Args:
        file_path: Path to file (PDF, HTML, TXT, etc.)
        store_path: Path to ChromaDB
        collection: Collection name
        chunk_method: Chunking strategy
        chunk_size: Size parameter for chunking
        chunk_overlap: Overlap between chunks
        
    Returns:
        IndexResult with summary
    """
    raise NotImplementedError


def process_urls(
    urls: List[str],
    store_path: str = "./data/vectorstore",
    collection: str = "freiburg_docs_v3large"
) -> IndexResult:
    """
    Scrape and process URLs through the pipeline.
    
    Future feature for web scraping.
    
    Args:
        urls: List of URLs to scrape
        store_path: Path to ChromaDB
        collection: Collection name
        
    Returns:
        IndexResult with summary
    """
    raise NotImplementedError


def build_pipeline_config(
    chunk_method: ChunkMethod = "sentence",
    chunk_size: int = 4,
    chunk_overlap: int = 1,
    embedding_model: str = "voyage-3-large",
    enrich_metadata: bool = False
) -> Dict[str, Any]:
    """
    Build a pipeline configuration dict.
    
    Args:
        chunk_method: Chunking strategy
        chunk_size: Size parameter
        chunk_overlap: Overlap parameter
        embedding_model: VoyageAI model
        enrich_metadata: Whether to enrich metadata
        
    Returns:
        Configuration dict
    """
    raise NotImplementedError
