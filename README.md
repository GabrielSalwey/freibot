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
- ✅ PDF ingestion and intelligent chunking
- ✅ German-optimized embeddings
- ✅ Conversational interface via web UI
- ✅ Docker containerization
- ✅ In-process similarity search with Chroma
- ✅ Cost-efficient API usage (~3 cents per conversation)

## 🔥 The "Holy Shit" Moment

On July 15, 2025, what started as a learning experiment became reality. In a single afternoon session, Claude built our entire MVP - downloading PDFs, setting up Docker, creating the RAG pipeline, and deploying the web interface. Total cost: **€0.21** (18 cents for embeddings, 3 cents for testing). 

This wasn't just about saving money. It validated something bigger: AI-assisted development can make civic tech accessible to small groups of motivated citizens. You don't need a tech company or government budget to build tools that serve your community.

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
- **Backend**: Python 3.11, FastAPI, LangChain
- **Vector Database**: Chroma (local files)
- **LLMs**: Claude Haiku 3.5 (direct API), OpenAI text-embedding-3-small
- **Frontend**: HTML/JS/CSS (vanilla for now)
- **Infrastructure**: Docker, Docker Compose
- **Data Processing**: PyPDF2, langchain-community loaders

## 🏃 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- API Keys: Anthropic (Claude) and OpenAI

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/freibot.git
cd freibot
```

2. Create `.env` file:
```bash
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
```

3. Start the services:
```bash
docker-compose up -d
```

4. Access the web interface:
```
http://localhost:8000
```

### Development Setup

For local development without Docker:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python src/main.py
```

## 📊 Data Sources

Currently processing 17 comprehensive PDF reports from fritz.freiburg.de including:
- Demographic statistics
- Economic indicators
- Environmental data
- Social surveys
- Urban development metrics

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

## 🎓 Learning & Skills Development

This project serves as a practical learning ground for:
- **RAG Architecture**: Document chunking, embedding strategies, retrieval optimization
- **Vector Databases**: Similarity search, metadata filtering, performance tuning
- **Production ML**: Containerization, API design, cost optimization
- **German NLP**: Language-specific challenges, cultural context handling

## 📈 Roadmap

### Phase 1: Foundation (Current)
- [x] Basic RAG pipeline
- [x] Docker deployment
- [x] Web interface
- [ ] Source citations
- [ ] Chat memory
- [ ] Improved UI

### Phase 2: Expansion
- [ ] Additional data sources (news, events)
- [ ] Multi-language support
- [ ] Advanced analytics
- [ ] Mobile app
- [ ] User accounts and personalization

### Phase 3: Intelligence
- [ ] Form-filling assistance
- [ ] Proactive notifications
- [ ] Integration with city services
- [ ] Voice interface
- [ ] Predictive insights

### Phase 4: Scale
- [ ] Official partnership with Stadt Freiburg
- [ ] DSGVO-compliant sensitive data handling
- [ ] Open source framework for other cities
- [ ] Community-driven data validation

## 💰 Cost Efficiency

Current operational costs:
- Embedding generation: ~€0.18 per full dataset
- Query processing: ~€0.003 per interaction
- Infrastructure: Self-hosted on community resources

Our focus on efficiency ensures this remains accessible as a public good.

## 🏛️ Governance & Ethics

- **Privacy First**: DSGVO compliance, no personal data collection
- **Transparency**: Open source, documented decisions
- **Local Control**: German-hosted, community-operated
- **Accessibility**: Free for all citizens, multilingual support planned

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
- The open source community for amazing tools
- Freiburg citizens for inspiration and feedback
- Claude AI for development assistance (meta!)

---

**Built with ❤️ for Freiburg by Freiburgers**

*"Making our city's knowledge accessible to all - fast and for frei!"*