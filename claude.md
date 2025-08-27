# CLAUDE.md - Freibot Project Context

## Project Overview
**Mission**: Transform fritz.freiburg.de PDFs into conversational Q&A for Freiburg citizens  
**Why**: Democratize city data access, especially for foreigners and underrepresented groups  
**Status**: MVP Complete | German RAG system with 17 PDFs indexed

## Architecture
```
PDFs → PyPDFLoader (line 111) → Pages with metadata (line 117-126) 
→ RecursiveCharacterTextSplitter (line 129) → Chunks (1500 chars)
→ OpenAIEmbeddings → Chroma vectorstore (data/vectorstore)

Query → Retrieve (K=8 chunks) → Claude Haiku direct API → German response
```

## Core Files
- `src/document_processor_claude.py`
  - `process_pdf()` - Extracts text and adds metadata (line 104)
  - `process_all_pdfs()` - Batch processes PDFs (line 138)
  - `ask_question()` - RAG query pipeline (line 259)
  
- `src/web_app_claude.py`
  - FastAPI app with `/ask` endpoint
  - `_optimize_conversation_history()` - Smart context window management (line 32)
  - Serves HTML UI on port 8000
  
- `src/cli_claude.py`
  - `interactive_mode()` - REPL for testing queries
  - `process_documents()` - Rebuild vector store command

## Project Structure
```
C:\Users\gabir\Projects\freibot\
├── src/                    # Application code
├── data/
│   ├── pdfs/              # 17 Fritz Freiburg PDFs
│   └── vectorstore/       # Chroma persistent storage
├── docker-compose.yml     # Single service deployment
├── .env                   # OPENAI_API_KEY, ANTHROPIC_API_KEY
└── venv/                  # Python 3.11 environment
```

## Commands
```bash
# Start services
cd C:\Users\gabir\Projects\freibot
docker-compose up -d              # Web UI: http://localhost:8000

# Test query
python src/cli_claude.py -q "Wie viele Einwohner hat Freiburg?"

# Rebuild index
python convert_to_chroma.py

# Check services
docker ps                         # Should show freibot-api container
docker logs freibot-api          # Debug API issues
```

## Current Capabilities
✅ **Working**:
- PDF text extraction with page numbers
- German-optimized chunking and retrieval
- Web interface with conversation history
- CLI for testing single queries
- Metadata extraction (year, doc type, source)

❌ **Not Working**:
- Source citations in responses (metadata exists but not displayed)
- Session persistence (memory resets on page reload)
- Table/chart extraction from PDFs
- Multi-language support

## Workflow
1. **Plan**: Understand the codebase state before changing
2. **Implement**: Make focused changes to specific functions
3. **Test**: `python src/cli_claude.py -q "test query"` 
4. **Document**: Update this file if architecture changes

---
*Working Directory: C:\Users\gabir\Projects\freibot | Vector DB: Chroma local files | Web: localhost:8000*