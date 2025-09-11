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
