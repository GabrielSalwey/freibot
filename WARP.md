# WARP Guide (Freibot)

A concise guide for working with this repo in Warp.

## Quick Commands

```bash
# Start API server (http://localhost:8001)
python api.py

# Start Chainlit UI (http://localhost:8000)
cd webapp
chainlit run chainlit_app.py

# CLI examples
python scripts/cli.py ask "Wie viele Einwohner hat Freiburg?" --top-k 3
python scripts/cli.py interactive
python scripts/cli.py health --json
python scripts/cli.py test [all|latency|quality|retrieval|behavior|regression] -v
```

## Tests (in-process)
- Tests run in-process against the FastAPI app using fastapi.testclient.TestClient.
- You do NOT need to run the server to execute tests.
- Some tests will be skipped automatically if prerequisites are missing.

Commands:
```bash
# All tests
pytest scripts/tests -v -s

# Specific suite
pytest scripts/tests/test_behavior.py -v -s

# Via CLI wrapper (Windows-friendly)
python scripts/cli.py test behavior -v
```

Prerequisites for full coverage:
- .env with VOYAGE_API_KEY and OPENROUTER_API_KEY
- Indexed vectorstore:
  python scripts/index_documents.py

Skip behavior:
- If embeddings or documents are missing, retrieval-heavy tests are auto-skipped.

## API Snippets

```bash
# Health
curl http://localhost:8001/health

# Ask (with optional session and privacy mode)
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Lärmschutzverordnung Altstadt", "session_id": "user123", "privacy_mode": false}'
```

## Notes
- FREIBOT_API_BASE can point the CLI/Chainlit to a remote API (default http://localhost:8001)
- Retrieval is dynamic (0–3). Override per request with `--top-k N` or `{ "top_k": N }`

## Architecture (at a glance)
- FastAPI app in `api.py` using Haystack 2.17 + Voyage embeddings + Chroma vectorstore
- Frontend: Chainlit (`webapp/chainlit_app.py`) talks to API over HTTP
- Scripts in `scripts/` for indexing and tests

# Code Style Requirements

### Core Principles

* **KISS & YAGNI**: Every line must justify its existence. No premature abstractions.
* **50-line rule**: If a module exceeds 50 lines, question if it can be simpler.
* **Data-oriented**: Simple dicts/lists over complex dataclasses when possible.
* **Naming**: Be descriptive but, more importantly, keep the code short.
* **Direct Haystack Usage**: Use Haystack components directly where possible instead of wrapper classes.
* **Documentation**: Inline comments for "why", not "what".

### Target Architecture Examples

**Direct Haystack usage**

```python
# GOOD: Direct Haystack usage - indexing.py (entire file)
from haystack import Pipeline
from haystack.components.preprocessors import DocumentSplitter
from haystack_integrations.components.embedders.voyage_embedders import VoyageDocumentEmbedder
from haystack_integrations.document_stores.chroma import ChromaDocumentStore
import os

# Direct setup, no classes
store = ChromaDocumentStore(persist_path="./data/vectorstore")

# Build pipeline directly
index_pipeline = Pipeline()
index_pipeline.add_component("splitter", DocumentSplitter(split_length=500))
index_pipeline.add_component(
    "embedder",
    VoyageDocumentEmbedder(api_key=os.getenv("VOYAGE_API_KEY"), model="voyage-3-large"),
)
index_pipeline.add_component("writer", DocumentWriter(store))
index_pipeline.connect("splitter", "embedder")
index_pipeline.connect("embedder", "writer")

# Run it
def index_pdfs(pdf_paths):
    for pdf in pdf_paths:
        index_pipeline.run({"splitter": {"sources": [pdf]}})

# BAD:
class FreibotRAG:
    def __init__(self, config: ConfigClass):
        self._init_document_store()
        self._init_pipelines()
        # 50 more lines of abstraction...
```
