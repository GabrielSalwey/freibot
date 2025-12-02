"""
Shared types for Freibot backend.

**INPUTS:**
    N/A (type definitions only)
    
**OUTPUTS:**
    N/A (type definitions only)

**RESPONSIBILITIES:**
    - Define framework-agnostic data structures
    - Provide consistent types across backend modules
    
**DEPENDENCIES:**
    - dataclasses (stdlib)
    - typing (stdlib)
    
**TODO:**
    - Add validation methods if needed
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class Document:
    """Retrieved document with content and metadata."""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


@dataclass
class RankedDocument:
    """Document with reranking score."""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    initial_score: float = 0.0
    rerank_score: float = 0.0


@dataclass
class Source:
    """Formatted source for API response."""
    id: int
    document: str
    content: str
    page: Optional[int] = None


@dataclass
class GenerationResult:
    """Result from LLM generation."""
    answer: str
    sources: List[Source] = field(default_factory=list)


@dataclass
class ConversationExchange:
    """Single Q&A exchange in conversation history."""
    question: str
    answer: str
    timestamp: str
