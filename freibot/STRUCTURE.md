# Freibot Structure

## Overview

This document describes the new modular structure of Freibot v5.0.

## Directory Layout

```
freibot/
├── __init__.py              # Package root (version: 5.0.0)
├── api.py                   # FastAPI endpoints (lightweight orchestration)
├── cli.py                   # Command-line interface (lightweight orchestration)
│
├── backend/                 # RAG backend components
│   ├── __init__.py
│   ├── types.py            # Shared types (Document, Source, etc.)
│   ├── retrievers.py       # Query embedding & vector search
│   ├── rerankers.py        # Document reranking (future)
│   └── generators.py       # LLM generation & prompt building
│
├── document_processor/      # Document ingestion pipeline
│   ├── __init__.py
│   ├── types.py            # Pipeline types (RawDoc, Chunk, etc.)
│   ├── pipeline.py         # Orchestration (main entry point)
│   ├── scraper.py          # Web scraping (future)
│   ├── converter.py        # File format conversion (PDF→text)
│   ├── chunking.py         # Text chunking strategies
│   ├── metadata_generation.py  # Topic/entity extraction
│   └── indexing.py         # Embedding & ChromaDB writes
│
├── frontend/                # User interfaces
│   ├── __init__.py
│   ├── streamlit_app.py    # Streamlit web UI (future)
│   └── assets/             # Static files
│
├── data/                    # Data storage
│   ├── README.md
│   ├── vectorstore/        # ChromaDB storage
│   ├── files/              # Raw input files
│   └── processed_files/    # Processing artifacts
│
└── tests/                   # Test suite
    ├── __init__.py
    └── benchmarks/         # Performance benchmarks
        └── __init__.py
```

## Design Principles

### 1. Framework-Agnostic Contracts
- Backend modules use custom types, not Haystack-specific classes
- Easy to swap VoyageAI, ChromaDB, or OpenRouter for alternatives
- Clear boundaries between external dependencies and core logic

### 2. KISS & YAGNI
- `api.py` and `cli.py` are lightweight orchestrators
- Complex logic lives in domain modules (backend, document_processor)
- Only implement what's needed (all functions currently `raise NotImplementedError`)

### 3. Separation of Concerns
- **Backend**: Query-time RAG (retrieve → rerank → generate)
- **Document Processor**: Ingestion-time pipeline (scrape → convert → chunk → index)
- **API/CLI**: Thin coordination layers

### 4. Volunteer-Friendly
- Each module has clear docstring contracts (INPUTS, OUTPUTS, RESPONSIBILITIES, DEPENDENCIES, TODO)
- Shared types in `types.py` files for clarity
- Pipeline orchestration in `document_processor/pipeline.py` shows full flow

## Key Contracts

### Backend Flow
```
Query → retrievers.classify_query() → retrievers.retrieve_documents()
     → rerankers.rerank_documents() [optional]
     → generators.generate_answer()
     → Response
```

### Document Processing Flow
```
Files → pipeline.process_pdf_directory()
     → converter.convert_pdf()
     → chunking.chunk_documents()
     → metadata_generation.enrich_chunks() [optional]
     → indexing.embed_chunks()
     → indexing.write_to_store()
```

## Migration Path

### Current State (v4.0)
- `freibot.py` - 302 lines, everything in one file
- `scripts/index_documents.py` - separate indexing

### New State (v5.0)
- Modular structure with 21 files
- All contracts defined (NotImplementedError)
- Ready for incremental implementation

### Next Steps
1. Implement `backend/retrievers.py` (port from freibot.py)
2. Implement `backend/generators.py` (port from freibot.py)
3. Implement `document_processor/converter.py` (port from index_documents.py)
4. Implement `document_processor/chunking.py` (port from index_documents.py)
5. Implement `document_processor/indexing.py` (port from index_documents.py)
6. Implement `document_processor/pipeline.py` (orchestrate above)
7. Implement `api.py` (port from freibot.py endpoints)
8. Implement `cli.py` (port from scripts/cli.py)
9. Add tests
10. Deprecate old files

## Type Hierarchy

### Backend Types (`backend/types.py`)
- `Document` - Retrieved document with score
- `RankedDocument` - Document after reranking
- `Source` - Formatted source for API response
- `GenerationResult` - LLM output with sources
- `ConversationExchange` - Q&A history entry

### Document Processor Types (`document_processor/types.py`)
- `RawDocument` - Scraped/raw content
- `ConvertedDocument` - Extracted text from files
- `Chunk` - Text chunk ready for embedding
- `EnrichedChunk` - Chunk with metadata
- `IndexResult` - Indexing operation summary
- `ChunkMethod` - Literal type for chunking strategies

## Configuration

All configuration should be:
1. Explicit in function signatures (no hidden globals)
2. Overridable via environment variables
3. Documented in docstrings

Default values:
- Embedding model: `voyage-3-large`
- LLM model: `openai/gpt-4o-mini`
- Chunk method: `sentence`
- Chunk size: `4` sentences
- Chunk overlap: `1` sentence
- Collection: `freiburg_docs_v3large`

## Testing Strategy

### Unit Tests
- Test each module independently
- Mock external dependencies (APIs, databases)

### Integration Tests
- Test full pipeline flows
- Use test fixtures in `tests/fixtures/`

### Benchmarks
- Query latency
- Answer quality
- Retrieval effectiveness
- Regression tests

## Questions for Implementation

When implementing each module, consider:

1. **Error handling**: How to handle API failures gracefully?
2. **Logging**: What level of detail? Where to log?
3. **Validation**: Input validation strategy?
4. **Caching**: What to cache? Where?
5. **Rate limiting**: How to handle API limits?
6. **Progress**: How to report progress for long operations?

## Contributing

When implementing a module:

1. Read the contract docstring carefully
2. Implement function with proper types
3. Add docstring with examples if helpful
4. Write unit tests
5. Update this document if design changes
6. Keep functions under 50 lines (split if needed)

---

**Status**: Skeleton complete, ready for implementation
**Branch**: `restructure`
**Commit**: "Add restructured skeleton with contracts"
