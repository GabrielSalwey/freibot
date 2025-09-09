# Freibot Quickstart Guide

Freiburg city data Q&A system using Haystack + VoyageAI + OpenRouter.

## Prerequisites

- Python 3.11+ (tested with 3.13)
- API Keys:
  - VoyageAI API key (for embeddings)
  - OpenRouter API key (for LLM)

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API keys in .env:**
   ```
   VOYAGE_API_KEY=your_voyage_api_key
   OPENROUTER_API_KEY=your_openrouter_api_key
   ```

3. **Add PDFs to data/pdfs/ directory** (17 Fritz Freiburg PDFs included)

## Usage

### Start the Server

```bash
python freibot.py
# Server runs at http://localhost:8001
# Auto-indexes PDFs on startup (3776 documents)
```

### Using the CLI Tool

```bash
# Ask a single question
python scripts/cli.py ask "Wie viele Einwohner hat Freiburg?"

# Interactive Q&A mode
python scripts/cli.py interactive

# Run benchmark queries
python scripts/cli.py benchmark

# Check API health
python scripts/cli.py health

# Manually trigger indexing
python scripts/cli.py index
```

### Direct API Usage

```bash
# Health check
curl http://localhost:8001/health

# Ask a question
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Lärmschutzverordnung Altstadt"}'

# Ask with session context
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Was ist das?", "session_id": "user123"}'

# Privacy mode (uses weaker models, no logging)
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Meine Frage", "privacy_mode": true}'

# Manual indexing
curl -X POST http://localhost:8001/index
```

## Features

- **Dynamic retrieval**: Automatically determines how many documents to retrieve (0-10) based on query type
- **Session management**: Maintains conversation context with session_id
- **Privacy mode**: Uses weaker models and disables logging for sensitive queries
- **German-optimized**: Tuned for German compound words and administrative terminology
- **Source citations**: Returns relevant document excerpts with each answer

## Performance

- **Startup**: ~30 seconds (indexing if needed)
- **Simple queries**: 5-10 seconds
- **Complex queries**: 15-20 seconds
- **Documents indexed**: 3776 from 17 PDFs

## Troubleshooting

### Windows Encoding Issues
The CLI tool includes UTF-8 encoding fixes. If you see encoding errors, ensure your terminal supports UTF-8.

### Rate Limiting
VoyageAI requires a payment method for >3 requests per minute. The system includes rate limiting protection.

### Memory Usage
ChromaDB keeps embeddings in memory. With 3776 documents, expect ~2GB RAM usage.

### Deprecation Warnings
FastAPI on_event warnings are expected and don't affect functionality.

## Architecture

- **freibot.py** (279 lines): Simplified RAG system with single pipeline
- **web.py** (292 lines): HTML/CSS/JavaScript web interface
- **scripts/cli.py** (224 lines): CLI tool for testing and interaction
- **scripts/index_documents.py** (289 lines): Document processing and indexing
- **scripts/test_api.py**: API test suite
- **data/vectorstore/**: Persistent ChromaDB storage
- **data/pdfs/**: Source PDF documents (17 Fritz Freiburg reports)

## Recent Improvements (v4.0)

✅ **Simplified Architecture**: Reduced main file from 823 to 279 lines (66% reduction)
✅ **Separated Concerns**: Web interface moved to dedicated file
✅ **Organized Scripts**: All tools moved to scripts/ folder
✅ **Windows Encoding**: Fixed UTF-8 issues in CLI
✅ **Removed Complexity**: Eliminated streaming and duplicate pipeline builders

## Remaining Issues

1. Response times can be slow (15-20s) for complex queries
2. Deprecation warnings from FastAPI on_event (non-breaking)
3. Telemetry errors from Haystack (doesn't affect functionality)
4. Using gpt-4o-mini instead of Claude as originally intended