"""
Generators module for Freibot.

**INPUTS:**
    - question: str - User question in German
    - context: List[Document] - Retrieved/reranked documents
    - conversation_history: Optional[List[ConversationExchange]] - Previous exchanges
    
**OUTPUTS:**
    - GenerationResult - Answer with formatted sources

**RESPONSIBILITIES:**
    - Build prompts with context and question
    - Generate answers via OpenRouter (gpt-4o-mini)
    - Format responses with source citations [1], [2], etc.
    
**DEPENDENCIES:**
    - OpenRouter API (LLM)
    
**TODO:**
    - Add streaming response support
    - Implement conversation memory
    - Support multiple LLM backends
"""

from typing import List, Optional

from .types import Document, Source, GenerationResult, ConversationExchange


def build_prompt(
    question: str,
    documents: List[Document],
    conversation_history: Optional[List[ConversationExchange]] = None
) -> str:
    """
    Build a prompt with context and question.
    
    Args:
        question: User question
        documents: Retrieved documents for context
        conversation_history: Optional previous exchanges
        
    Returns:
        Formatted prompt string
    """
    raise NotImplementedError


def generate_answer(
    question: str,
    context: List[Document],
    model: str = "openai/gpt-4o-mini",
    temperature: float = 0.1,
    max_tokens: int = 1000
) -> GenerationResult:
    """
    Generate an answer using the LLM.
    
    Args:
        question: User question
        context: Retrieved documents
        model: OpenRouter model identifier
        temperature: Sampling temperature
        max_tokens: Maximum response length
        
    Returns:
        Generated answer string
    """
    raise NotImplementedError


def generate_without_context(
    question: str,
    model: str = "openai/gpt-4o-mini"
) -> str:
    """
    Generate a direct answer without document retrieval.
    
    Used for greetings, general knowledge, or when vectorstore unavailable.
    
    Args:
        question: User question
        model: OpenRouter model identifier
        
    Returns:
        Generated answer string
    """
    raise NotImplementedError


def format_sources(documents: List[Document]) -> List[Source]:
    """
    Format source documents for API response.
    
    Args:
        documents: Retrieved documents
        
    Returns:
        List of formatted source dictionaries
    """
    raise NotImplementedError
