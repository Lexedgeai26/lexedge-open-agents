# LexEdge – Open Legal Agents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-Powered-4285F4.svg)](https://google.github.io/adk-docs/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Lexedgeai26/lexedge-open-agents/blob/main/CONTRIBUTING.md)
[![GitHub Stars](https://img.shields.io/github/stars/Lexedgeai26/lexedge-open-agents?style=social)](https://github.com/Lexedgeai26/lexedge-open-agents)

**LexEdge – Open Legal Agents** is an open-source, multi-agent legal AI platform built with **Google ADK (Agent Development Kit)** and **Gemini** large language models. It delivers a full-stack legal intelligence console — from contract analysis and legal research to compliance auditing and case management — orchestrated by a suite of specialised legal AI agents.

> ⚖️ **Designed for legal teams, law firms, and legal-tech builders seeking open, extensible AI-assisted legal workflows.**

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🤖 **Multi-Agent Orchestration** | Specialised agents for Contract Analysis, Legal Research, Compliance, Case Management, and more — coordinated by a central Router Agent via Google ADK |
| 📄 **Document Intelligence** | Upload PDF, DOCX, or TXT — the active agent immediately analyses it without extra prompting |
| 🔍 **Legal Research** | Case law, statute lookup, citation verification, and precedent analysis |
| 📋 **Contract Review** | Clause-by-clause risk analysis, redlining suggestions, and obligation mapping |
| 🛡️ **Compliance Auditing** | Multi-framework compliance checks (GDPR, SOX, Indian BNS/BNSS/BSA, etc.) |
| ✉️ **Legal Correspondence** | Draft demand letters, legal notices, and client communications |
| ⚖️ **Indian Jurisdiction Focus** | Prefers Bharatiya Nyaya Sanhita (BNS), BNSS, and BSA for post-July 2024 matters |
| 🔒 **Quality Gatekeeper** | Every output passes through a jurisdiction, citation, and completeness review before delivery |
| 🎙️ **Voice Input** | WebSocket-based audio transcription for hands-free legal dictation |
| 🌐 **Real-Time WebSocket API** | Low-latency bidirectional communication between frontend and agent backend |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              React Frontend (Vite)               │
│   Chat UI · Document Upload · Role Selector      │
└────────────────────┬────────────────────────────┘
                     │ WebSocket
┌────────────────────▼────────────────────────────┐
│           FastAPI Backend (lexedge/api)          │
│   WebSocket Manager · Audio Transcription        │
└────────────────────┬────────────────────────────┘
                     │ Google ADK Runner
┌────────────────────▼────────────────────────────┐
│               Root Agent (Router)                │
│  Classifies intent → delegates to sub-agents     │
└──┬──────┬───────┬──────┬────────┬───────────────┘
   │      │       │      │        │
   ▼      ▼       ▼      ▼        ▼
Contract Legal  Comply  Case   Legal
Analysis Research Review Mgmt  Correspond.

           + Practice Lead Agents
   Civil · Criminal · Corporate · IP · Family
   Constitutional · Property · Taxation

           + Orchestrators
   QualityGatekeeperAgent · PromptCoachAgent
```

### Agent Registry

| Agent | Role |
|---|---|
| `RouterAgent` | Classifies intent and delegates to specialist |
| `ContractAnalysisAgent` | Contract review, risk, and redlining |
| `LegalResearchAgent` | Case law, statute, and precedent research |
| `ComplianceAgent` | Regulatory compliance audit |
| `CaseManagementAgent` | Deadline tracking and case workflow |
| `CaseIntakeAgent` | Client onboarding and case profiling |
| `LegalCorrespondenceAgent` | Letters, notices, demand letters |
| `LawyerAgent` | General legal analysis and strategy |
| `QualityGatekeeperAgent` | Output validation — jurisdiction, citations, completeness |
| Practice Lead Agents | 8 domain-specific leads (Civil, Criminal, Corporate, IP, etc.) |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **Node.js 18+**
- **Google API Key** (Gemini 1.5 Pro or compatible model)

### 📦 Installation

**1. Clone the repository**
```bash
git clone https://github.com/Lexedgeai26/lexedge-open-agents.git
cd lexedge-open-agents
```

**2. Set up the Python backend**
```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**3. Set up the React frontend**
```bash
cd frontend
npm install
cd ..
```

### ⚙️ Configuration

```bash
cp .env.example .env
```

Edit `.env` and provide your keys:

```env
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Model configuration (defaults shown)
LLM_MODEL=gemini-1.5-pro
LLM_TEMPERATURE=0.1

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=3334

# Optional: vLLM / LiteLLM endpoint for self-hosted models
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_API_KEY=your_key
```

### 🏃 Running

**Start the backend (API + WebSocket server)**
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 lexedge/api/app.py
```
→ Server starts at `http://localhost:3334`

**Start the frontend (dev mode)**
```bash
cd frontend
npm run dev
```
→ UI available at `http://localhost:5173`

---

## 📁 Project Structure

```
lexedge-open-agents/
├── lexedge/
│   ├── api/                   # FastAPI app, WebSocket endpoints
│   ├── agent_runner.py        # Core ADK runner and response pipeline
│   ├── root_agent.py          # Main routing agent
│   ├── main_agent.py          # Entry point agent
│   ├── sub_agents/            # Specialist agents
│   │   ├── contract_analysis/
│   │   ├── legal_research/
│   │   ├── compliance/
│   │   ├── case_management/
│   │   ├── case_intake/
│   │   ├── legal_correspondence/
│   │   ├── lawyer/
│   │   └── legal_docs/
│   ├── practice_leads/        # Domain-specific lead agents
│   │   ├── civil/
│   │   ├── criminal/
│   │   ├── corporate/
│   │   ├── ip/
│   │   ├── family/
│   │   ├── constitutional/
│   │   ├── property/
│   │   └── taxation/
│   ├── orchestrators/         # QualityGatekeeper, PromptCoach, Router
│   ├── shared_tools/          # Tools shared across agents
│   │   ├── document_analyzer.py
│   │   ├── case_law_research.py
│   │   ├── citation_verifier.py
│   │   ├── statute_mapper.py
│   │   ├── court_drafting.py
│   │   ├── argument_builder.py
│   │   └── quality_gatekeeper.py
│   ├── prompts/               # System, agent, and tool prompts
│   ├── session/               # Session and context management
│   └── utils/                 # Helpers, formatters, audio
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx   # Main chat UI
│   │   │   └── ResponseCards.jsx   # Structured response cards
│   │   └── App.jsx                 # Landing page
│   └── index.html
├── docs/                      # Documentation
├── samples/                   # Sample legal documents for testing
├── requirements.txt
└── README.md
```

---

## 🛠️ Adding a New Agent

1. Create a folder under `lexedge/sub_agents/your_agent/`
2. Implement `your_agent.py` using `google.adk.agents.LlmAgent`
3. Register it in `lexedge/root_agent.py` sub-agent list
4. Add it to `BOOTSTRAP_COMMANDS` in `frontend/src/components/ChatInterface.jsx`

See `lexedge/sub_agents/legal_research/` as a reference implementation.

---

## 🗺️ Roadmap

- [ ] RAG integration with Milvus / Pinecone for precedent search
- [ ] Multi-jurisdiction support (US, UK, EU, India)
- [ ] Courtroom-ready document generation (plaints, petitions, replies)
- [ ] Electron desktop app
- [ ] LangFuse / observability integration
- [ ] Offline mode with local LLM (Ollama)

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Fork → branch → commit → PR
git checkout -b feature/my-new-agent
git commit -m "feat: add InsolvencyAgent"
git push origin feature/my-new-agent
```

---

## ⚠️ Disclaimer

LexEdge Open Legal Agents is an **AI research and productivity tool**. It is **not a substitute for a licensed lawyer**. All outputs must be reviewed by a qualified legal professional before reliance. Citation verification on official databases (SCC Online, Manupatra, Indian Kanoon) is mandatory.

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🏢 Developed by

**[LexEdge Lab](https://www.lexedge.ai/)** — Building open legal intelligence infrastructure.

> *"Law should be accessible, not arcane."*
