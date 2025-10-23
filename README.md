# Freibot 🤖

### KI-Sprachassistent für Freiburg – Transparent, Offen, Für Alle

## 🌅 Vision

Ein KI-Sprachassistent für digitale Veröffentlichungen der Stadt Freiburg, der verständlichen und barrierefreien Zugang zu politischen Informationen ermöglicht. Demokratisierung von Stadtdaten durch Open Source – für Bürger:innen, Vereine, Parteien, Journalist:innen und Stadträt:innen.

## 🎯 Mission

**Kurzfristig**: FRITZ-Statistikdaten (fritz.freiburg.de) über RAG-System zugänglich machen.

**Mittelfristig**: Integration weiterer Open-Data-Plattformen:

- **RIS** (Rats- und Bürgerinformationssystem)
- **FreiGIS** (Geodaten-Portal)
- **Amtsblatt** (E-Paper)
- **Kataster** (Wärme, Flächennutzung)

**Langfristig**: Vollständiger Informationsassistent für Verwaltung und Bürger:innen mit Faktenchecker-Funktion für politische Aussagen.

## 🚀 Status (Oktober 2025)

**✅ Migration abgeschlossen**: ChromaDB → Qdrant mit Metadaten-Filterung

**Live Features**:

- ✅ Qdrant-Vektordatenbank (Docker, production-ready, localhost:6333)
- ✅ 2713 Dokumente mit Metadaten (Jahr, Typ, Titel, Topics)
- ✅ Natürlichsprachige Filter ("2024 Sozialbericht", "nur Wahlberichte")
- ✅ LLM-basierte Metadaten-Extraktion (17 PDFs: 7 Wahlberichte, 8 Statistiken, 1 Sozialbericht, 2018-2025)
- ✅ German-optimized embeddings (VoyageAI voyage-3-large, 1024-dim)
- ✅ Chainlit Web-Interface + CLI
- ✅ Enhanced Citations (Jahr, Typ, Titel in Quellenangaben)

## 💡 Warum Freibot?

**Problem**: Freiburg hat mehrere Open-Data-Plattformen (FRITZ, RIS, FreiGIS), aber keine zentrale Möglichkeit, einem Chatbot Fragen zu stellen. Bürgeranfragen müssen manuell beantwortet werden – das bindet Zeit und Ressourcen.

**Lösung**: Technische, quelloffene KI-Lösung von ehrenamtlichen IT-Expert:innen.

**Nutzen für**:

- **Bürger:innen**: Barrierefreier Zugang zu Stadtdaten ohne E-Mail/Telefon
- **OB-Kandidat:innen & Parteien**: Recherche-Tool für Wahlkampf (OB-Wahl Juni 2026)
- **Journalist:innen**: Faktenchecker für politische Aussagen
- **Verwaltung**: Entlastung durch automatisierte Auskünfte
- **Stadträt:innen & NGOs**: Schneller Zugriff auf Beschlüsse und Statistiken

**Open Government**: Freiburg hat 2014 Open-Data-Strategie beschlossen. Freibot setzt diese um – inspiriert von **KI Parla** (City Lab Berlin).

## 🛠️ Technical Architecture

### Tech Stack

- **Backend**: Python 3.11+, FastAPI, Haystack 2.17
- **Vector Database**: Qdrant (Docker, localhost:6333)
- **LLMs**: OpenRouter (gpt-4o-mini) für Chat + Metadaten-Extraktion
- **Embeddings**: VoyageAI voyage-3-large (1024-dim)
- **Frontend**: Chainlit Web-Interface
- **Infrastructure**: Docker (Qdrant), Python (App)
- **Metadata**: LLM-powered extraction (Jahr, Typ, Topics)

### Architecture Principles

- **KISS & YAGNI**: Direkte Haystack-Komponenten, keine Abstraktionen
- **Open Source**: Inspiriert von KI Parla (City Lab Berlin)
- **Privacy-first**: Privacy Mode, DSGVO-konform
- **Production-ready**: Qdrant statt ChromaDB für Skalierbarkeit

## 🏃 Quick Start

### Prerequisites

- Python 3.11+
- Docker (für Qdrant)
- API Keys: VoyageAI, OpenRouter

### Installation

1. **Clone und Install**:
   
   ```bash
   git clone https://github.com/yourusername/freibot.git
   cd freibot
   pip install -r requirements.txt
   ```

2. **Start Qdrant** (Docker):
   
   ```bash
   docker-compose up -d
   ```

3. **Create `.env`**:
   
   ```bash
   VOYAGE_API_KEY=your_key
   OPENROUTER_API_KEY=your_key
   ```

4. **Index documents** (nur beim ersten Mal):
   
   ```bash
   python scripts/index_documents.py
   ```

5. **Run**:
   
   ```bash
   # API (localhost:8001)
   python api.py
   ```

# Chainlit UI (localhost:8000)

cd webapp && chainlit run chainlit_app.py

# CLI

python scripts/cli.py ask "Was sagt der 2024 Sozialbericht?"

```
### Features

- **Metadata filtering**: "2024 Sozialbericht", "nur Wahlberichte" auto-filter by year/type
- **Dynamic retrieval**: 0-3 docs based on query complexity
- **Enhanced citations**: Year, type, title in source references
- **Session management**: Last 10 exchanges per session
- **Privacy mode**: Optional logging disable

### Performance

- Startup: ~10s (Qdrant connection)
- Queries: 5-15s (filtered queries faster)
- Indexed: 2713 documents from 17 PDFs

### Troubleshooting

- **Qdrant not running**: `docker ps` to check, restart with command above
- **No documents**: Run `python scripts/index_documents.py`
- **Rate limits**: VoyageAI throttling handled by indexer

## 📊 Datenquellen

### ✅ Aktuell: FRITZ (fritz.freiburg.de)
17 PDFs (2018-2025):
- 7 Wahlberichte
- 8 Statistiken
- 1 Sozialbericht
- 1 Sonstige

**Indexed**: 2713 Dokumente mit Metadaten (Jahr, Typ, Titel, Topics)

### 🔜 Geplante Integration
| Plattform | Beschreibung |
|-----------|-------------|
| **RIS** | Rats- und Bürgerinformationssystem (Gemeinderatsprotokolle) |
| **FreiGIS** | Geodaten-Portal (Stadtpläne, Flurstücke) |
| **Amtsblatt** | E-Paper (amtliche Bekanntmachungen) |
| **Beteiligungshaushalt** | Bürgerbeteiligung am Haushalt |
| **Kataster** | Wärmekataster, Flächennutzung |

## 🔍 Example Queries

- "Was sagt der 2024 Sozialbericht?" (auto-filters by year)
- "Zeige nur Wahlberichte von 2024" (filters by year + type)
- "Wie viele Menschen leben in Freiburg-Vauban?"
- "Welche Stadtteile haben die höchste Zufriedenheit mit dem ÖPNV?"
- "Entwicklung der Mietpreise in den letzten 5 Jahren"

## 📈 Roadmap

### Phase 1: Foundation ✅
- [x] RAG pipeline (Haystack + Qdrant)
- [x] Metadata extraction & filtering
- [x] Web interface with privacy mode
- [x] CLI tools
- [x] Enhanced citations (year, type, title)

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
├── webapp/
│   └── chainlit_app.py      # Chainlit frontend (calls API over HTTP)
├── scripts/
│   ├── cli.py               # CLI tool (ask/interactive/health/test)
│   ├── index_documents.py   # Document indexing
│   ├── test_chainlit.py     # Liveness test for Chainlit + API
│   └── tests/               # Pytest suite (in-process)
│       ├── __init__.py
│       ├── test_behavior.py
│       ├── test_latency.py
│       ├── test_quality.py
│       └── test_retrieval.py
├── data/
│   ├── pdfs/                # 17 Fritz Freiburg PDFs
│   ├── metadata_cache.json  # LLM-extracted metadata
│   └── (Qdrant storage in Docker volume)
├── requirements.txt         # Python dependencies
├── .env                     # API keys
└── WARP.md                  # Warp quick guide

```
Deprecated:
- freibot.py — kept as a shim to forward to api.py for compatibility

## 👥 Team & Community

**Projektsprecherin**: Valerie Tabea Schult
- OB-Kandidatin 2026 Freiburg im Breisgau
- 📧 valerieschult@gmail.com
- 🌐 [www.oberbuergermeisterin-freiburg.de](http://www.oberbuergermeisterin-freiburg.de)

**Organisator**: Joshua Allgeier
- 📧 joshua.allgeier@froehlichesfreiburg.de
- 📞 +49 1578 7601990

**Ehrenamtliche Entwickler:innen** (Stand Oktober 2025):
- Gabriel (Lead Dev) – Master in Biology, AI alignment & civic tech
- Darius – Physics/CS, Quantum ML
- Nico
- Robert
- Waldemar
- **Du?** – Melde dich bei Joshua!

**Ort**: Haus des Engagements, Rehlingstraße 9, 79117 Freiburg (hybrid)

**Community Partners**:
- Fröhliches Freiburg
- Effective Altruism Freiburg
- (Ziel: Kooperation mit Stadt Freiburg / DIGIT)

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

## 🙏 Danksagungen

- **KI Parla** (City Lab Berlin) – Open-Source-Vorbild
- **FRITZ Freiburg** – Offene Stadtdaten
- **Haystack Community** – RAG-Framework
- **VoyageAI & OpenRouter** – AI APIs
- **Valerie Tabea Schult** – Projekt-Initiatorin
- Alle ehrenamtlichen Entwickler:innen

---

**Mit ❤️ entwickelt von Freiburger:innen für Freiburg**

*"Datentransparenz für alle – offen, zugänglich, demokratisch."*

**OB-Wahl Juni 2026** – Freibot als Recherche-Tool und Faktenchecker
```
