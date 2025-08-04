# Freibot Knowledge Base

## 🟢 Status: MVP Complete | Sprint: Source Citations
*Last verified: 2025-07-24 | Next update: When P0 complete*

## ⚡ Quick Start
```bash
# Setup
cd C:\freibot && copy .env.example .env  # Add API keys
docker-compose up -d                      # Start services
# http://localhost:8000                   # Web interface

# Test CLI
docker run --rm -v "${PWD}/data:/app/data" \
  -e OPENAI_API_KEY -e ANTHROPIC_API_KEY \
  freibot:latest python src/cli_claude.py -q "Wie viele Einwohner hat Freiburg?"
```

## 🎯 Active Sprint (P0)
1. **Source Citations** → `document_processor_claude.py`
   - [ ] Add PDF/page metadata to chunks during processing
   - [ ] Update response format: "According to [Klimaschutz_2023.pdf, p.15]..."
   - [ ] Make citations clickable in web interface
   
2. **Chat Memory** → `web_app_claude.py`
   - [ ] Implement FastAPI session management
   - [ ] Store conversation history in session
   - [ ] Pass full history to Claude API calls

3. **UI Polish** → `web_app_claude.py` + `/static`
   - [ ] Add Freiburg colors (#E30613 red, #FFFFFF white)
   - [ ] Create landing with example questions
   - [ ] Add typing indicators and loading states

## 🏗️ Architecture
```
[User] → FastAPI:8000 → LangChain RAG → Claude Haiku
                            ↓
                        Qdrant:6333
                            ↓
                    17 Fritz PDFs (embedded)
```

### Stack Details
- **LLM**: Claude Haiku 3.5 (claude-3-5-haiku-20241022)
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector DB**: Qdrant (Docker container)
- **Framework**: LangChain + FastAPI
- **Data**: 17 Fritz reports, 1500 char chunks, 8 chunk retrieval

### File Structure
```
C:\freibot/
├── docker-compose.yml      # Service orchestration
├── Dockerfile             # Python app container  
├── .env                   # API keys (git-ignored)
├── data/                  # Persistent storage
│   ├── pdfs/             # 17 Fritz reports
│   └── vectorstore/      # Qdrant embeddings
└── src/                   # Application code
    ├── cli_claude.py              # CLI interface
    ├── web_app_claude.py          # Web interface
    ├── document_processor_claude.py # RAG pipeline
    ├── freibot_simple.py          # Legacy core
    └── download_pdfs.py           # Data fetcher
```

## 💡 Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **LLM** | Claude Haiku | Superior German, $0.25/1M input (30x cheaper than GPT-3.5) |
| **Embeddings** | OpenAI text-3-small | Proven quality, minimal cost |
| **Vector DB** | Qdrant | Production-ready, Docker-native, persistent |
| **Chunk Size** | 1500 chars | Optimized for Claude's context window |
| **Retrieval** | 8 chunks | Balance between context and relevance |
| **Container** | Minimal Python 3.13 | No compilation deps, pure Python |

## 🔧 Troubleshooting

### Common Issues
```bash
# Qdrant connection failed
docker ps                      # Verify container running
docker logs freibot-qdrant     # Check for errors
docker-compose restart qdrant  # Force restart

# API key errors
echo %OPENAI_API_KEY%         # Windows: Verify set
echo $OPENAI_API_KEY          # Linux: Verify set
# Never commit keys! Use .env file

# Empty/poor responses
# 1. Check PDF parsing in processor logs
# 2. Verify embeddings created (data/vectorstore/)
# 3. Test with known good query
# 4. Review chunk size/overlap settings
```

### Manual Fallback
```bash
# If Docker fails
pip install -r requirements.txt
python src/cli_claude.py -q "Test question"
```

## 🚀 Deployment Options

### Local Docker
```bash
docker-compose up -d  # Current method
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: freibot
spec:
  template:
    spec:
      containers:
      - name: freibot
        image: freibot:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: freibot-secrets
              key: openai-key
```

### Alternative Build
```bash
docker buildx create --use
docker build --platform linux/amd64 -t freibot:latest .
```

## 📈 Roadmap

### P1 - Scalability (Next Sprint)
- **Auto-updates**: Cron job + `download_pdfs.py` for Fritz updates
- **Data expansion**: Scrape freiburg.de, add news sources  
- **Production deploy**: Migrate to bwCluster 3.0 (DSGVO compliant)

### P2 - Enhancement
- **German embeddings**: Test multilingual sentence transformers
- **Smart chunking**: Semantic splitting, preserve tables/lists
- **Professional UI**: React frontend, proper design system

### P3 - Advanced Features
- **Multi-language**: DE/EN/FR support
- **Voice interface**: Speech-to-text queries
- **Admin forms**: Help with city paperwork
- **Personalization**: User preferences, saved searches

## 💰 Cost Analysis
- **Initial setup**: $0.18 (embedding all PDFs)
- **Testing**: $0.03 (~17 test queries)
- **Total MVP**: $0.21
- **Production estimate**: <$5/month for moderate usage

## 📝 Changelog

### 2025-07-24: Production Containerization
- Simplified from 16 to 5 core files
- Docker Compose orchestration implemented
- Secrets externalized (no hardcoded keys)
- Minimal container deps (4 packages only)
- **Lesson**: Radical simplification improves maintainability

### 2025-07-15: Initial MVP (Gabe + Claude Desktop)
- Downloaded 17 Fritz PDFs
- Built RAG pipeline with LangChain
- Created CLI interface
- Discovered Claude superior for German
- **Lesson**: Start simple, iterate based on real usage

## 🤖 Development Principles
- **Simplicity First**: 5 files > 16 files
- **German-Local Focus**: DSGVO compliance, German optimization
- **Rapid Iteration**: Docker for consistency, quick feedback loops
- **Cost Awareness**: Track API usage, optimize chunk strategies

---
*Auto-generated by Claude on updates. Last sync: 2025-07-24*