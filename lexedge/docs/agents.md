# LexEdge: Legal Multi-Agent System Specification

**Comprehensive Agent & Orchestration Specification for Legal AI**

---

## 1. System Overview

LexEdge is a modular, agentic legal intelligence system designed to analyze legal documents (contracts, filings, statutes), maintain case context, and dynamically route tasks to **specialized legal agents** based on the workflow requirements (drafting, research, compliance, etc.).

### Core Design Principles

* **Workflow-Driven Orchestration**: Tasks are routed based on legal processes.
* **Specialty-Scoped Reasoning**: Agents focus on specific tasks to ensure depth.
* **Jurisdiction-First (India)**: Defaults to Indian law (BNS/BNSS/BSA) but configurable.
* **Premium Response Templates**: Uses structured HTML cards for complex legal data.
* **Human-in-the-Loop**: Designed to assist licensed professionals, not replace them.

---

## 2. Core Agent Roles

### 2.1 LexEdge Root Agent (The Orchestrator)

**Purpose**
Acts as the **single point of interaction** and the **context memory layer**. It identifies intent and delegates to specialized sub-agents.

**Key Skills**
- Case context management (`CaseProfile`).
- Longitudinal memory through `agent_context_manager`.
- Intent routing (Identifying if the user needs research, drafting, or analysis).
- Quality control and consistency.

**Owns Data (`CaseProfile`)**
```json
{
  "case_packet": {
    "jurisdiction": "India",
    "case_name": "Kumar vs. State",
    "practice_area": "Criminal",
    "parties": ["Petitioner", "Respondent"],
    "facts": ["chronological bullet points"],
    "statutes": ["BNS 101", "BNSS 482"]
  }
}
```

---

## 3. Specialized Sub-Agents

Each sub-agent follows a **strict contract** within the Google ADK framework.

### 3.1 Lawyer Agent (Senior Advisory)
- **Focus**: Strategy, legal opinions, and complex analysis.
- **Key Tools**: `legal_analysis_assessment`, `legal_specialty_query`.

### 3.2 Legal Docs Agent (Documentation Specialist)
- **Focus**: Analyzing uploaded documents, summarizing filings, and extraction.
- **Key Tools**: `analyze_legal_document`, `generate_legal_summary`.

### 3.3 Contract Analysis Agent (Transactional)
- **Focus**: NDA, MSA, SPA review and risk assessment.
- **Key Tools**: `review_contract`.

### 3.4 Legal Research Agent (Statutory & Case Law)
- **Focus**: Indian codes (BNS/BNSS/BSA) and Supreme Court/High Court precedents.
- **Key Tools**: `search_case_law`, `search_statutes`, `verify_citations`.

### 3.5 Case Management Agent (Workflow)
- **Focus**: Deadlines, task lists, and case timelines.
- **Key Tools**: `track_deadlines`, `manage_tasks`.

---

## 4. Operational Protocols

### 4.1 India-First Jurisdiction
- Default preference for **Bharatiya Nyaya Sanhita (BNS)** and other new criminal codes.
- Must provide cross-mapping from IPC/CrPC/IEA where necessary.

### 4.2 Professional Tone
- Agents must use **third-person, professional language**.
- Avoid first-person pronouns ("I", "me"). Use "The counsel identifies..." or "The profile indicates...".

---

## 5. Extensibility

New legal specialists can be added by:
1. Creating a package in `lexedge/sub_agents/`.
2. Defining domain-specific tools (e.g., `tax_tools.py`).
3. Adding an instruction provider in `lexedge/instruction_providers.py`.

---
**Maintained by LexEdge Advanced Architecture Team**
