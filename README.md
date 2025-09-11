# Freibot 🤖🔥
### An AI Assistant for Freiburg - Fast and for Frei

## 🌅 Vision

Building a scalable AI assistant that democratizes access to all Freiburg-specific knowledge - from city statistics and news to administrative procedures and local services. Our goal is to break down information barriers, especially for foreigners and underrepresented communities, making city data not just accessible but actionable through intelligent analysis and interpretation.

## 🎯 Project Mission

**Short-term**: Transform fritz.freiburg.de's comprehensive but inaccessible survey data into a conversational AI interface using Retrieval-Augmented Generation (RAG).

**Long-term**: Create a comprehensive digital assistant for Freiburg that can:
- Answer questions about city statistics, policies, and services
- Help with administrative procedures (Bürgeramt, KFZ-Zulassung, etc.)
- Analyze correlations and visualize data
- Provide multilingual support for international residents
- Eventually assist with paperwork and form completion

## 🚀 Current Status

**MVP Achieved**: Successfully built a working RAG system that ingests 17 PDF reports from Fritz Freiburg and provides accurate, conversational answers about city data.

**Live Features**:
- ✅ PDF ingestion and intelligent chunking (3776 documents indexed)
- ✅ German-optimized embeddings with VoyageAI (voyage-3-large, 512-dim, int8)
- ✅ Conversational web interface with privacy mode
- ✅ Simplified single-file architecture (279 lines)
- ✅ CLI tools for testing and interaction
- ✅ Session management and conversation history
- ✅ Dynamic document retrieval (0-3 docs based on query type)

## 💡 Why This Matters - Real World Impact

As a member of "Fröhliches Freiburg", I believe city policies should be grounded in evidence. But this goes beyond politics. Here's who we're building for:

**For Immigrants & International Students**: 
- "How do I register my car in Freiburg?" → Step-by-step KFZ-Zulassung guidance
- "Which Stadtteile are affordable for students?" → Real rent statistics by district
- Navigate German bureaucracy without perfect German skills

**For Journalists & Activists**:
- Quick fact-checking during city council meetings
- "What percentage of Vauban residents bike to work?" → Instant statistics with sources
- Evidence-based arguments for policy proposals

**For Local Businesses**:
- "Which districts have the most young families?" → Demographic insights for location planning
- "How has foot traffic changed in the Altstadt?" → Economic indicators for decision making

**For Every Freiburger**:
- "Why is my street being renovated again?" → Access to urban planning data
- "How does my district compare in terms of green space?" → Quality of life metrics
- Making democracy tangible through accessible information

## 🛠️ Technical Architecture

### Tech Stack
- **Backend**: Python 3.11+, FastAPI, Haystack 2.17
- **Vector Database**: ChromaDB (embedded, persistent local storage)
- **LLMs**: OpenRouter (gpt-4o-mini)
- **Embeddings**: VoyageAI voyage-3-large (512-dim, int8)
- **Frontend**: HTML/JS/CSS web interface (vanilla)
- **Infrastructure**: Single service, no Docker required
- **Data Processing**: PyPDF processing via Haystack components

### Architecture Principles
- **KISS & YAGNI**: Single-file main application (279 lines)
- **Direct component usage**: No abstractions over Haystack
- **Privacy-first**: Optional privacy mode, DSGVO-compliant logging
- **Organized scripts**: Separated CLI and testing tools

## 🏃 Quick Start

### Prerequisites
- Python 3.11+
- API Keys: VoyageAI (embeddings) and OpenRouter (LLM)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/freibot.git
cd freibot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
VOYAGE_API_KEY=your_voyage_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

4. Start the API server:
```bash
python api.py
# API runs at http://localhost:8001
```

5. Use the system:
```bash
# Start Chainlit frontend (in a separate terminal)
cd webapp
chainlit run chainlit_app.py
# Visit http://localhost:8000

# CLI tool
python scripts/cli.py ask "Wie viele Einwohner hat Freiburg?"
python scripts/cli.py interactive
python scripts/cli.py benchmark

# Direct API
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Lärmschutzverordnung Altstadt"}'
```

### Development Tools

```bash
# Run API tests
python scripts/test_api.py

# Test dynamic k selection
python scripts/test_dynamic_k.py

# Manual document indexing (if needed)
python scripts/index_documents.py

# Health check
python scripts/cli.py health

# Run tests via CLI wrapper (Windows-friendly)
python scripts/cli.py test [all|latency|quality|retrieval|behavior|regression]
```

### Features

- Dynamic retrieval: Automatically selects 0–3 documents based on query type
- Session management: Keeps the last 10 exchanges per session_id
- Privacy mode: Optional, disables logging
- German-optimized retrieval and prompts
- Source citations: Returns relevant document excerpts with each answer

### Performance

- Startup: ~30 seconds (including vectorstore init)
- Simple queries: ~5–10 seconds
- Complex queries: ~15–20 seconds
- Documents indexed: 3,776 from 17 PDFs

### Troubleshooting

- Windows encoding: Use a UTF-8 terminal; the CLI wraps stdout/stderr as UTF-8
- Rate limiting: VoyageAI may throttle without a payment method; the system includes basic protections
- Memory usage: ChromaDB keeps embeddings in memory (~2GB for 3,776 chunks)
- Deprecation warnings: FastAPI on_event warnings are expected and harmless

## 📊 Data Sources

Currently processing 17 comprehensive PDF reports from fritz.freiburg.de including:
- Demographic statistics and population data
- Economic indicators and employment surveys
- Environmental data and sustainability metrics
- Social surveys and citizen satisfaction
- Urban development and transportation metrics

**Total indexed**: 3776 document chunks optimized for German text retrieval

**Future data sources**:
- City council protocols
- Local news archives
- Administrative databases
- Real-time transit data
- Event calendars

## 🔍 Example Queries

- "Wie viele Menschen leben in Freiburg-Vauban?"
- "Was sind die häufigsten Beschwerden der Bürger?"
- "Zeige mir die Entwicklung der Mietpreise in den letzten 5 Jahren"
- "Welche Stadtteile haben die höchste Zufriedenheit mit dem ÖPNV?"
- "Wie ist die Arbeitslosenquote in Freiburg?"

## 📈 Roadmap

### Phase 1: Foundation ✅ (Current)
- [x] Basic RAG pipeline with Haystack
- [x] Web interface with privacy mode
- [x] CLI tools for testing and interaction
- [x] Simplified architecture (279 lines)
- [x] German-optimized retrieval
- [ ] Improved source citations
- [ ] Semantic chunking
- [ ] Response time optimization

### Phase 2: Expansion
- [ ] Additional data sources (news, events)
- [ ] Multi-language support (English, French)
- [ ] Advanced analytics and data visualization
- [ ] Mobile-responsive interface
- [ ] User accounts and personalization

### Phase 3: Intelligence
- [ ] Form-filling assistance
- [ ] Proactive notifications
- [ ] Integration with city services APIs
- [ ] Voice interface
- [ ] Predictive insights

### Phase 4: Scale
- [ ] Official partnership with Stadt Freiburg
- [ ] DSGVO-compliant sensitive data handling
- [ ] Open source framework for other cities
- [ ] Community-driven data validation

## 🏗️ Project Structure

```
freibot/
├── api.py                    # API server (single source of truth)
├── freibot.py                # Deprecated shim (forwards to api.py)
├── webapp/
│   └── chainlit_app.py      # Chainlit frontend (calls API over HTTP)
├── scripts/
│   ├── cli.py               # CLI tool for testing (HTTP client)
│   ├── index_documents.py   # Document indexing
│   ├── test_api.py          # API tests
│   ├── test_dynamic_k.py    # Dynamic k tests
│   └── test_chainlit.py     # Liveness test for Chainlit + API
├── data/
│   ├── pdfs/                # 17 Fritz Freiburg PDFs
│   └── vectorstore/         # ChromaDB storage
├── requirements.txt         # Python dependencies
├── .env                     # API keys
└── QUICKSTART.md           # Deprecated (merged into README)
```

Deprecated:
- freibot.py — kept as a shim to forward to api.py for compatibility

## 👥 Team & Community

**Project Lead**: Gabriel (Gabe)
- Master in Biology, focusing on AI alignment and civic tech
- Member of Fröhliches Freiburg and EA Freiburg

**Contributors**:
- Darius: Physics/CS, Quantum ML background

**Community Partners**:
- Fröhliches Freiburg
- Effective Altruism Freiburg
- (Seeking: Stadt Freiburg Amt für Digitales)

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

- Fritz Freiburg for comprehensive city data
- The Haystack community for excellent RAG tools
- VoyageAI and OpenRouter for accessible AI APIs
- Freiburg citizens for inspiration and feedback
- Claude AI for development assistance (meta!)

---

**Built with ❤️ for Freiburg by Freiburgers**

*"Making our city's knowledge accessible to all - fast and for frei!"*