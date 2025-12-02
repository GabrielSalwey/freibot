"""
Shared types for document processor pipeline.

**INPUTS:**
    N/A (type definitions only)
    
**OUTPUTS:**
    N/A (type definitions only)

**RESPONSIBILITIES:**
    - Define data structures for document processing pipeline
    - Provide type consistency from scraping through indexing
    
**DEPENDENCIES:**
    - dataclasses (stdlib)
    - typing (stdlib)
    
**TODO:**
    - Add validation methods if needed
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Literal


ChunkMethod = Literal["sentence", "word", "passage", "semantic"]


@dataclass
class RawDocument:
    """Raw scraped document before processing."""
    content: str
    source_url: str
    scraped_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConvertedDocument:
    """Document after conversion from file format."""
    content: str
    source_path: str
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    """A chunk of document ready for embedding."""
    content: str
    source_path: str
    chunk_index: int
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnrichedChunk:
    """Chunk with extracted metadata."""
    content: str
    source_path: str
    chunk_index: int
    topics: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    date_references: List[str] = field(default_factory=list)
    stadtteile: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IndexResult:
    """Result of an indexing operation."""
    documents_indexed: int
    documents_failed: int
    total_chunks: int
    errors: List[Dict[str, str]] = field(default_factory=list)
