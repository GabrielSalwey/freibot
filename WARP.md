# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Common Development Commands

### Starting the Application
```bash
# Legacy FastAPI Interface
python freibot.py
# Server runs at http://localhost:8001

# Modern Chainlit Interface (with streaming)
cd webapp
chainlit run chainlit_app.py
# App runs at http://localhost:8000

# Start with custom port
PORT=8002 python freibot.py
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with required API keys
echo "VOYAGE_API_KEY=your_voyage_api_key" > .env
echo "OPENROUTER_API_KEY=your_openrouter_api_key" >> .env
```

### CLI Tools
```bash
# Ask a question via CLI
python scripts/cli.py ask "Wie viele Einwohner hat Freiburg?"

# Interactive Q&A mode
python scripts/cli.py interactive

# Health check all systems
python scripts/cli.py health

# Run benchmark queries
python scripts/cli.py benchmark

# Manual document indexing (if needed)
python scripts/cli.py index
python scripts/index_documents.py
```

### Testing
```bash
# Run all tests
python scripts/cli.py test

# Run specific test categories
python scripts/cli.py test behavior    # API functionality tests
python scripts/cli.py test latency     # Performance timing tests
python scripts/cli.py test quality     # Answer quality validation
python scripts/cli.py test retrieval   # RAG retrieval effectiveness
python scripts/cli.py test regression  # Regression prevention tests

# Direct pytest execution
pytest tests/ -v
pytest tests/test_behavior.py -v -s
```

### API Testing
```bash
# Health check
curl http://localhost:8001/health

# Ask question via API
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Lärmschutzverordnung Altstadt"}'

# With session context
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Was ist das?", "session_id": "user123"}'

# Privacy mode (no logging)
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Meine Frage", "privacy_mode": true}'
```

## High-Level Architecture

### Core System Design
**Freibot** is a simplified RAG (Retrieval-Augmented Generation) system specifically built for Freiburg city data. The architecture follows KISS principles with a single-file main application (279 lines) that combines:

- **Document Processing**: PDF ingestion from Fritz Freiburg reports
- **Vector Search**: ChromaDB with VoyageAI embeddings for German text
- **LLM Generation**: OpenRouter (gpt-4o-mini) for conversational responses
- **Dual Interface Options**:
  - **Legacy**: FastAPI server with vanilla HTML/JS/CSS frontend
  - **Modern**: Chainlit webapp with streaming responses and 50k token context

### Key Components

#### 1. Main Application (`freibot.py`)
- **Pipeline Architecture**: Haystack-based RAG pipeline with embedder → retriever → prompt builder → LLM
- **Dynamic Retrieval**: Intelligent query classification determines document count (0-3) based on query complexity
- **Session Management**: Conversation history with 10-exchange memory per session
- **Privacy Mode**: Optional mode that disables logging and uses weaker models

#### 2. Chainlit Webapp (`webapp/chainlit_app.py`)
- **Modern UI**: Real-time token streaming with simulated effect
- **Same Pipeline**: Reuses Haystack components from main app
- **Enhanced UX**: 50k token context management
- **Privacy Support**: OpenRouter privacy flags integration

#### 3. Document Store (`data/vectorstore/`)
- **ChromaDB**: Embedded, persistent local vector database
- **German Optimization**: VoyageAI voyage-3-large embeddings tuned for German compound words
- **Document Structure**: 3776 indexed chunks from 17 Fritz Freiburg PDF reports
- **Chunking Strategy**: Semantic chunking with metadata preservation

#### 4. CLI System (`scripts/cli.py`)
- **TestClient Class**: Reusable client that wraps API calls for testing
- **Multi-mode Interface**: Support for single questions, interactive mode, and batch benchmarking
- **Health Monitoring**: Comprehensive checks for API, vectorstore, OpenRouter, and VoyageAI
- **Windows Compatibility**: UTF-8 encoding fixes for proper German text handling

#### 5. Testing Framework (`tests/`)
- **Pytest Integration**: Professional test structure with fixtures and parametrization
- **Test Categories**: Organized into latency, quality, retrieval, behavior, and regression tests
- **Quality Tiers**: Three-tier quality validation (structural → content → semantic)
- **Performance Monitoring**: TTFT (Time to First Token) and component latency breakdown

### Data Flow
1. **Query Classification**: Incoming questions analyzed for retrieval needs and complexity
2. **Document Retrieval**: Vector search in ChromaDB using VoyageAI embeddings (if needed)
3. **Context Building**: Retrieved documents formatted into German prompt template
4. **LLM Generation**: OpenRouter processes context and generates German responses
5. **Response Assembly**: Answer combined with source citations and metadata

### Key Technical Decisions

#### Simplicity Over Complexity
- Single-file main application eliminates unnecessary abstractions
- Direct Haystack component usage without custom wrappers
- Embedded ChromaDB avoids external database dependencies
- Vanilla web interface requires no build process

#### German Language Optimization
- VoyageAI voyage-3-large specifically chosen for German text understanding
- Custom prompt templates with German instructions and source citation format
- UTF-8 handling throughout the system for proper umlauts (ä, ö, ü, ß)
- Query classification tuned for German administrative terminology

#### Privacy and Compliance
- Optional privacy mode disables conversation logging
- DSGVO-compliant logging with truncated content
- Local-only vector storage with no cloud dependencies
- Session-based memory management with automatic cleanup

### Performance Characteristics
- **Cold Start**: ~30 seconds (including vectorstore initialization)
- **Simple Queries**: 5-10 seconds response time
- **Complex Queries**: 15-20 seconds with document retrieval
- **Memory Usage**: ~2GB RAM for full document embeddings
- **Concurrent Users**: Stateless design supports multiple simultaneous sessions

### Integration Points
- **API Endpoints**: RESTful FastAPI interface for external integrations
- **Web Interface**: Responsive HTML interface at root path
- **CLI Tools**: Command-line access for automation and testing
- **Logging**: JSON Lines format for conversation analytics
- **Monitoring**: Health and stats endpoints for system monitoring

## Development Notes

### Environment Requirements
- Python 3.11+ (tested with 3.13)
- VoyageAI API key (embeddings)
- OpenRouter API key (LLM)
- Minimum 4GB RAM recommended
- UTF-8 terminal support for German text

### Common Issues
- **Rate Limiting**: VoyageAI requires payment method for >3 requests/minute
- **Memory Usage**: ChromaDB keeps embeddings in memory; expect ~2GB usage
- **Windows Encoding**: CLI includes fixes for UTF-8 terminal output
- **Deprecation Warnings**: FastAPI on_event warnings are expected and non-breaking

### Extension Points
- **Additional Data Sources**: New PDF documents can be added to `data/pdfs/`
- **Language Support**: Prompt templates can be modified for multilingual support
- **LLM Models**: OpenRouter model can be changed via environment variable
- **Embedding Models**: VoyageAI model configurable in main application
- **Web Interface**: Frontend located in `web_app/web.py` for customization
- **Chainlit Interface**: Modern UI in `webapp/chainlit_app.py`

## Development Principles (Critical)

### Core Philosophy - KISS & YAGNI
- **50-line rule**: If a module exceeds 50 lines, question if it can be simpler
- **Functional over OOP**: Pure functions preferred over classes
- **Data-oriented**: Simple dicts/lists over complex dataclasses
- **Direct Framework Usage**: No wrapper classes around Haystack components
- **Documentation**: Comments for "why" not "what"

### Critical Anti-Patterns to Avoid

1. **DON'T create abstractions before you need them**
   - Bad: Creating wrapper classes around framework components
   - Good: Direct Haystack usage until complexity demands abstraction

2. **DON'T use dataclasses for simple configs**
   - Bad: 165 lines of config management with nested objects
   - Good: Simple dict/env vars (20 lines total)

3. **DON'T separate concerns prematurely**
   - Bad: Split into api.py, rag.py, config.py before proving concept
   - Good: Single file until complexity demands splitting

4. **DON'T over-engineer error handling**
   - Bad: Custom validation methods everywhere
   - Good: Let failures bubble up with context

### Valuable Patterns to Preserve

**Rate limiting for API calls:**
```python
class SimpleRateLimiter:
    def __init__(self, max_requests=10, window_seconds=60):
        self.requests = deque()
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
```

**Session management (simple dict):**
```python
sessions: Dict[str, List[Dict]] = {}
if len(sessions[session_id]) > 10:
    sessions[session_id] = sessions[session_id][-10:]
```

**German-optimized chunking:**
```python
separators = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " "]
```
