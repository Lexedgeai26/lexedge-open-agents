# LexEdge Legal Multi-Agent System - Implementation Plan
_Created: 2026-02-07_

## Overview

This document outlines the implementation plan to align LexEdge with the authoritative specification in `legal_agents_tools_prompt_library.md`. The goal is to create a comprehensive India-focused legal AI system with proper orchestration, practice-area specialization, and shared tools.

---

## 1. Gap Analysis

### Current State (Legacy Agents)
| Agent | Status | Notes |
|-------|--------|-------|
| LawyerAgent | Exists | General legal - needs refactoring |
| LegalDocsAgent | Exists | Document analysis - keep as utility |
| ContractAnalysisAgent | Exists | Enhance → Corporate & Commercial Lead |
| LegalResearchAgent | Exists | Enhance with India-specific tools |
| CaseManagementAgent | Exists | Keep for case tracking |
| ComplianceAgent | Exists | Keep for regulatory compliance |
| CaseIntakeAgent | Exists | Enhance → Intake & Router Agent |
| LegalCorrespondenceAgent | Exists | Keep for communications |

### Required State (11 Agents + 8 Shared Tools)

#### Orchestrators (3)
| Agent | Status | Priority |
|-------|--------|----------|
| Intake & Router Agent | Implemented | P0 |
| Legal Prompt Coach Agent | Implemented | P1 |
| Quality & Risk Gatekeeper Agent | Implemented | P0 |

#### Practice-Area Lead Agents (8)
| Agent | Status | Priority |
|-------|--------|----------|
| Criminal Law Lead Agent | Implemented | P0 |
| Civil Litigation Lead Agent | Implemented | P0 |
| Property Disputes Lead Agent | Implemented | P1 |
| Family & Divorce Lead Agent | Implemented | P1 |
| Corporate & Commercial Lead Agent | Implemented | P0 |
| Constitutional & Writs Lead Agent | Implemented | P1 |
| Taxation Lead Agent | Implemented | P1 |
| Intellectual Property Lead Agent | Implemented | P2 |

#### Shared Tools (8)
| Tool | Status | Priority |
|------|--------|----------|
| Statute & Section Mapping Tool | Implemented | P0 |
| Case Law Research Tool | Implemented | P0 |
| Citation Verification Tool | Implemented | P1 |
| Court-Ready Drafting Tool | Implemented | P0 |
| Document Analyzer Tool | Implemented | P1 |
| Argument Builder Tool | Implemented | P1 |
| Prompt Refinement Tool | Implemented | P1 |
| Quality & Risk Gatekeeper Tool | Implemented | P0 |

---

## 2. Architecture Design

### 2.1 Folder Structure
```
lexedge/
├── shared_tools/                    # NEW: Shared tool library
│   ├── __init__.py
│   ├── statute_mapper.py            # TOOL 1
│   ├── case_law_research.py         # TOOL 2
│   ├── citation_verifier.py         # TOOL 3
│   ├── court_drafting.py            # TOOL 4
│   ├── document_analyzer.py         # TOOL 5
│   ├── argument_builder.py          # TOOL 6
│   ├── prompt_refiner.py            # TOOL 7
│   └── quality_gatekeeper.py        # TOOL 8
│
├── orchestrators/                   # NEW: Orchestration layer
│   ├── __init__.py
│   ├── router_agent.py              # Intake & Router
│   ├── prompt_coach_agent.py        # Prompt Coach
│   └── gatekeeper_agent.py          # Quality Gatekeeper
│
├── practice_leads/                  # NEW: Practice-area leads
│   ├── __init__.py
│   ├── criminal/
│   │   ├── __init__.py
│   │   ├── criminal_lead_agent.py
│   │   └── criminal_tools.py        # Practice-specific tools
│   ├── civil/
│   │   ├── __init__.py
│   │   ├── civil_lead_agent.py
│   │   └── civil_tools.py
│   ├── property/
│   │   ├── __init__.py
│   │   ├── property_lead_agent.py
│   │   └── property_tools.py
│   ├── family/
│   │   ├── __init__.py
│   │   ├── family_lead_agent.py
│   │   └── family_tools.py
│   ├── corporate/
│   │   ├── __init__.py
│   │   ├── corporate_lead_agent.py
│   │   └── corporate_tools.py
│   ├── constitutional/
│   │   ├── __init__.py
│   │   ├── constitutional_lead_agent.py
│   │   └── constitutional_tools.py
│   ├── taxation/
│   │   ├── __init__.py
│   │   ├── taxation_lead_agent.py
│   │   └── taxation_tools.py
│   └── ip/
│       ├── __init__.py
│       ├── ip_lead_agent.py
│       └── ip_tools.py
│
├── prompts/                         # NEW: Canonical prompt library
│   ├── __init__.py
│   ├── system_prompts.py            # Global safety prompts
│   ├── tool_prompts.py              # Tool prompt templates
│   └── agent_prompts.py             # Agent instruction templates
│
├── models/                          # NEW: Data models
│   ├── __init__.py
│   └── case_packet.py               # Standard I/O contract
│
└── sub_agents/                      # EXISTING: Keep for utilities
    ├── lawyer/                      # Deprecate → use practice leads
    ├── legal_docs/                  # Keep as document utility
    ├── legal_research/              # Merge into shared_tools
    ├── case_management/             # Keep for case tracking
    ├── compliance/                  # Keep for regulatory
    ├── case_intake/                 # Merge into orchestrators/router
    ├── legal_correspondence/        # Keep for communications
    └── contract_analysis/           # Merge into practice_leads/corporate
```

### 2.2 Agent Hierarchy
```
RootAgent (LexEdge Coordinator)
│
├── Orchestrators (always available)
│   ├── IntakeRouterAgent          # Routes to practice leads
│   ├── PromptCoachAgent           # Refines user prompts
│   └── QualityGatekeeperAgent     # Validates outputs
│
├── Practice-Area Leads (routed by IntakeRouter)
│   ├── CriminalLawLeadAgent
│   ├── CivilLitigationLeadAgent
│   ├── PropertyDisputesLeadAgent
│   ├── FamilyDivorceLeadAgent
│   ├── CorporateCommercialLeadAgent
│   ├── ConstitutionalWritsLeadAgent
│   ├── TaxationLeadAgent
│   └── IntellectualPropertyLeadAgent
│
└── Utility Agents (support functions)
    ├── CaseManagementAgent
    ├── ComplianceAgent
    └── LegalCorrespondenceAgent
```

### 2.3 Standard I/O Contract (Case Packet)
All agents will use this standardized structure:

```python
# models/case_packet.py
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class PracticeArea(Enum):
    CRIMINAL = "criminal"
    CIVIL = "civil"
    PROPERTY = "property"
    FAMILY = "family"
    CORPORATE = "corporate"
    CONSTITUTIONAL = "constitutional"
    TAX = "tax"
    IP = "ip"

class DeliverableType(Enum):
    DRAFT = "draft"
    RESEARCH_MEMO = "research_memo"
    ARGUMENTS = "arguments"
    CHECKLIST = "checklist"
    ANALYSIS = "analysis"

@dataclass
class CasePacket:
    jurisdiction: str = "India"
    forum: str = ""
    practice_area: PracticeArea = None
    parties: List[str] = field(default_factory=list)
    facts: List[str] = field(default_factory=list)
    documents: List[str] = field(default_factory=list)
    time_sensitivity: str = "standard"  # urgent | standard
    statutes: List[str] = field(default_factory=list)

@dataclass
class Deliverable:
    type: DeliverableType
    content: str

@dataclass
class Citations:
    verified: List[str] = field(default_factory=list)
    needs_verification: List[str] = field(default_factory=list)

@dataclass
class AgentResponse:
    case_packet: CasePacket
    deliverable: Deliverable
    citations: Citations
    risks: List[str] = field(default_factory=list)
    next_questions: List[str] = field(default_factory=list)
```

---

## 3. Implementation Phases

### Phase 1: Foundation (P0)
**Goal:** Core infrastructure and essential agents

#### 1.1 Create Shared Tools Library
- [x] `shared_tools/__init__.py`
- [x] `shared_tools/statute_mapper.py` - India law mapping (BNS/BNSS/BSA ↔ IPC/CrPC/IEA)
- [x] `shared_tools/case_law_research.py` - SC/HC case law search
- [x] `shared_tools/court_drafting.py` - Court-ready document generation
- [x] `shared_tools/quality_gatekeeper.py` - Output validation

#### 1.2 Create Prompts Library
- [x] `prompts/__init__.py`
- [x] `prompts/system_prompts.py` - Global safety & professionalism
- [x] `prompts/tool_prompts.py` - Canonical tool templates
- [x] `prompts/agent_prompts.py` - Agent instructions

#### 1.3 Create Data Models
- [x] `models/__init__.py`
- [x] `models/case_packet.py` - Standard I/O contract

#### 1.4 Create Orchestrators
- [x] `orchestrators/__init__.py`
- [x] `orchestrators/router_agent.py` - Intake & routing
- [x] `orchestrators/gatekeeper_agent.py` - Quality validation

#### 1.5 Create Core Practice Leads
- [x] `practice_leads/criminal/` - Criminal Law Lead
- [x] `practice_leads/civil/` - Civil Litigation Lead
- [x] `practice_leads/corporate/` - Corporate & Commercial Lead

### Phase 2: Extended Practice Areas (P1)
**Goal:** Complete practice-area coverage

#### 2.1 Additional Practice Leads
- [x] `practice_leads/property/` - Property Disputes Lead
- [x] `practice_leads/family/` - Family & Divorce Lead
- [x] `practice_leads/constitutional/` - Constitutional & Writs Lead
- [x] `practice_leads/taxation/` - Taxation Lead

#### 2.2 Additional Shared Tools
- [x] `shared_tools/citation_verifier.py` - Citation validation
- [x] `shared_tools/document_analyzer.py` - Document analysis
- [x] `shared_tools/argument_builder.py` - Argument construction
- [x] `shared_tools/prompt_refiner.py` - Prompt improvement

#### 2.3 Prompt Coach Orchestrator
- [x] `orchestrators/prompt_coach_agent.py`

### Phase 3: Specialized Features (P2)
**Goal:** Advanced capabilities and mini-agents

#### 3.1 IP Practice Lead
- [ ] `practice_leads/ip/` - Intellectual Property Lead

#### 3.2 Mini-Agents (Optional)
- [ ] Bail Drafting Mini-Agent
- [ ] Quashing Strategy Mini-Agent
- [ ] Cross-Examination Mini-Agent
- [ ] Injunction Mini-Agent
- [ ] Trademark Opposition Mini-Agent

#### 3.3 Integration & Testing
- [ ] Update `root_agent.py` with new hierarchy
- [ ] Update `instruction_providers.py`
- [ ] Create test scenarios from spec
- [ ] Performance optimization

---

## 4. Shared Tools Specifications

### TOOL 1: Statute & Section Mapping Tool
**File:** `shared_tools/statute_mapper.py`

```python
def map_statute_sections(
    legal_issue: str,
    court_level: str,
    old_law_reference: str = None,
    tool_context: ToolContext = None
) -> str:
    """
    Map legal issues to applicable statutory provisions.
    Handles BNS/BNSS/BSA ↔ IPC/CrPC/IEA cross-mapping.

    Returns:
        - Section Mapping Table
        - Essential Ingredients
        - Procedural & Compliance Notes
        - Red Flags (limitation, jurisdiction)
    """
```

### TOOL 2: Case Law Research Tool
**File:** `shared_tools/case_law_research.py`

```python
def research_case_law(
    legal_issue: str,
    section: str,
    court_preference: str = "Both",  # SC / HC / Both
    year_range: str = "2014-2026",
    fact_similarity: str = None,
    tool_context: ToolContext = None
) -> str:
    """
    Search SC/HC case law for relevant precedents.

    Returns:
        - Case citations with court, year
        - Ratio decidendi
        - Factual applicability
        - Verification status
    """
```

### TOOL 3: Citation Verification Tool
**File:** `shared_tools/citation_verifier.py`

```python
def verify_citation(
    case_name: str,
    citation: str,
    court: str,
    tool_context: ToolContext = None
) -> str:
    """
    Validate case existence and citation accuracy.

    Returns:
        - Status: Verified / Needs Verification / Invalid
        - Correction / Notes
    """
```

### TOOL 4: Court-Ready Drafting Tool
**File:** `shared_tools/court_drafting.py`

```python
def draft_legal_document(
    document_type: str,
    court: str,
    parties: List[str],
    facts: List[str],
    relief: str,
    sections: List[str],
    cases: List[str] = None,
    tool_context: ToolContext = None
) -> str:
    """
    Generate court-ready legal documents.

    Document Types:
        - Anticipatory Bail Application
        - Regular Bail Application
        - Quashing Petition (482/528)
        - Writ Petition
        - Plaint / Written Statement
        - Injunction Application
        - Reply to Notice
        - Legal Notice
        - Appeal Memo
        - SLP Synopsis

    Returns:
        - Fully formatted legal draft with placeholders
    """
```

### TOOL 5: Document Analyzer Tool
**File:** `shared_tools/document_analyzer.py`

```python
def analyze_document(
    document_type: str,  # FIR / Order / Chargesheet / Agreement / Petition / Judgment
    document_content: str,
    tool_context: ToolContext = None
) -> str:
    """
    Analyze legal documents and extract insights.

    Returns:
        - Case Summary
        - Chronology Table
        - Legal Issues Identified
        - Strategic Observations
    """
```

### TOOL 6: Argument Builder Tool
**File:** `shared_tools/argument_builder.py`

```python
def build_arguments(
    side: str,  # Petitioner / Respondent / Accused / Complainant
    facts: List[str],
    issues: List[str],
    sections: List[str],
    cases: List[str] = None,
    tool_context: ToolContext = None
) -> str:
    """
    Construct legal arguments.

    Returns:
        - Written Arguments
        - Oral Submissions Outline
        - Anticipated Counter-Arguments
        - Rebuttals
    """
```

### TOOL 7: Prompt Refinement Tool
**File:** `shared_tools/prompt_refiner.py`

```python
def refine_prompt(
    raw_prompt: str,
    tool_context: ToolContext = None
) -> str:
    """
    Convert vague user prompts into structured legal requests.

    Returns:
        - Improved Prompt (facts + jurisdiction + relief + format)
        - Missing Information Checklist
    """
```

### TOOL 8: Quality & Risk Gatekeeper Tool
**File:** `shared_tools/quality_gatekeeper.py`

```python
def validate_output(
    output: str,
    tool_context: ToolContext = None
) -> str:
    """
    Final quality and risk assessment.

    Returns:
        - Status: READY / NEEDS REVIEW
        - Risk Notes
        - Suggested Improvements
        - Professional disclaimer
    """
```

---

## 5. Practice Lead Agent Specifications

### 5.1 Criminal Law Lead Agent
**Scope:** FIR/complaints, anticipatory/regular bail, quashing, discharge, remand, NI 138, revision, writs, cross-examination

**Tools:** statute_mapper, case_law_research, court_drafting, document_analyzer, argument_builder, citation_verifier, quality_gatekeeper

**Key Workflows:**
1. Bail Applications (anticipatory/regular)
2. Quashing Petitions (S.482 BNSS)
3. FIR Analysis & Defense Strategy
4. Cross-Examination Preparation
5. NI 138 (Cheque Bounce) Matters

### 5.2 Civil Litigation Lead Agent
**Scope:** Plaint/WS, injunctions (O39), appeals, execution, limitation, arbitration (S.8/9/11/34/36)

**Key Workflows:**
1. Suit Drafting (Plaint/Written Statement)
2. Injunction Applications
3. Limitation Analysis
4. Arbitration Proceedings
5. Execution Applications

### 5.3 Property Disputes Lead Agent
**Scope:** Title/possession, partition, specific performance, cancellation, lease vs license, mutation/revenue

**Key Workflows:**
1. Title Disputes
2. Partition Suits
3. Specific Performance
4. Eviction Matters
5. Revenue/Mutation Issues

### 5.4 Family & Divorce Lead Agent
**Scope:** Divorce (mutual/contested), maintenance (125/24/25), custody/guardianship, DV proceedings

**Key Workflows:**
1. Divorce Petitions (13/13B HMA)
2. Maintenance Applications
3. Custody/Guardianship
4. DV Act Proceedings
5. Settlement Negotiations

### 5.5 Corporate & Commercial Lead Agent
**Scope:** Contracts (NDA/MSA/SHA/SPA/SSA), employment, loan, leases, board resolutions, Companies Act, NCLT

**Key Workflows:**
1. Contract Drafting & Review
2. Due Diligence Checklists
3. Board Resolutions
4. NCLT Matters
5. Employment Agreements

### 5.6 Constitutional & Writs Lead Agent
**Scope:** Writs (226/32), PIL, interim relief, contempt, SLP outline

**Key Workflows:**
1. Writ Petitions (Art. 226/32)
2. PIL Drafting
3. Interim Relief Applications
4. Contempt Petitions
5. SLP Preparation

### 5.7 Taxation Lead Agent
**Scope:** IT notices (148/142(1)/156), GST SCN, appeals (CIT(A)/ITAT), stay, rectification (154), penalties

**Key Workflows:**
1. Notice Response (148/142)
2. Appeal Drafting
3. Stay Applications
4. Rectification (S.154)
5. GST Show Cause Replies

### 5.8 Intellectual Property Lead Agent
**Scope:** Trademarks (filing/opposition/reply), infringement, licensing/assignment, patent objections, copyright

**Key Workflows:**
1. TM Applications & Opposition
2. Infringement Analysis
3. Licensing Agreements
4. Patent Objections
5. Copyright Registration

---

## 6. Global System Prompts

### 6.1 Global Safety Prompt (All Agents)
```text
You are a Legal AI Sub-Agent.

You must:
1. Work strictly within the given jurisdiction (India unless specified).
2. Prefer Bharatiya Nyaya Sanhita (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS), and Bharatiya Sakshya Adhiniyam (BSA) where applicable.
3. Clearly flag:
   - Any assumption
   - Any statute/section mapping that is uncertain
   - Any citation that requires verification
4. Never invent case law, citations, or statutory provisions.
5. Use court-ready legal language and formatting.
6. Maintain professional neutrality.
7. Output must be suitable for review by a practicing lawyer.
8. Do not provide legal advice as a substitute for a lawyer; provide drafting and research assistance only.
```

### 6.2 Standard Disclaimer (Append to deliverables)
```text
Note: This draft/research is AI-assisted and for professional review. Verify all citations, sections, limitation, and jurisdiction on official sources (e.g., court websites, SCC/Manupatra) before filing or relying on it.
```

---

## 7. Configuration Updates

### 7.1 Update config.py
```python
LEGAL_SETTINGS = {
    "jurisdiction": "India",
    "country_of_practice": "India",
    "legal_system": "Common Law (India)",
    "primary_codes": ["BNS", "BNSS", "BSA"],
    "legacy_codes": ["IPC", "CrPC", "IEA"],
    "courts": [
        "Supreme Court of India",
        "High Court",
        "Sessions Court",
        "District Court",
        "Magistrate Court",
        "NCLT",
        "ITAT",
        "Consumer Forum"
    ],
    "practice_areas": [
        "criminal",
        "civil",
        "property",
        "family",
        "corporate",
        "constitutional",
        "tax",
        "ip"
    ]
}
```

### 7.2 Update root_agent.py
```python
from lexedge.orchestrators.router_agent import IntakeRouterAgent
from lexedge.orchestrators.gatekeeper_agent import QualityGatekeeperAgent
from lexedge.orchestrators.prompt_coach_agent import PromptCoachAgent

from lexedge.practice_leads.criminal import CriminalLawLeadAgent
from lexedge.practice_leads.civil import CivilLitigationLeadAgent
from lexedge.practice_leads.property import PropertyDisputesLeadAgent
from lexedge.practice_leads.family import FamilyDivorceLeadAgent
from lexedge.practice_leads.corporate import CorporateCommercialLeadAgent
from lexedge.practice_leads.constitutional import ConstitutionalWritsLeadAgent
from lexedge.practice_leads.taxation import TaxationLeadAgent
from lexedge.practice_leads.ip import IntellectualPropertyLeadAgent

# Keep utility agents
from lexedge.sub_agents.case_management.case_management_agent import CaseManagementAgent
from lexedge.sub_agents.compliance.compliance_agent import ComplianceAgent
from lexedge.sub_agents.legal_correspondence.legal_correspondence_agent import LegalCorrespondenceAgent

root_agent = LlmAgent(
    name="LexEdge",
    model=LlmModel,
    description="Central Legal AI Coordinator for India. Routes to specialized practice-area agents.",
    instruction=root_agent_instruction_provider,
    sub_agents=[
        # Orchestrators
        IntakeRouterAgent,
        QualityGatekeeperAgent,
        PromptCoachAgent,
        # Practice Leads
        CriminalLawLeadAgent,
        CivilLitigationLeadAgent,
        PropertyDisputesLeadAgent,
        FamilyDivorceLeadAgent,
        CorporateCommercialLeadAgent,
        ConstitutionalWritsLeadAgent,
        TaxationLeadAgent,
        IntellectualPropertyLeadAgent,
        # Utility Agents
        CaseManagementAgent,
        ComplianceAgent,
        LegalCorrespondenceAgent,
    ]
)
```

---

## 8. Testing Strategy

### 8.1 Smoke Test Scenarios (from spec)
1. **Criminal:** Anticipatory bail (false implication, property dispute motive)
2. **Criminal:** Quashing FIR (commercial dispute, mediation settlement)
3. **Civil:** Temporary injunction to restrain alienation
4. **Property:** Specific performance with readiness & willingness
5. **Family:** 13B mutual consent + custody/maintenance terms
6. **Corporate:** NDA + invention assignment clause set
7. **Constitutional:** 226 writ for illegal detention (habeas corpus)
8. **Tax:** Reply to 148 reassessment notice with timeline analysis
9. **GST:** SCN for ITC reversal with doc checklist
10. **IP:** Opposition reply for TM objection under S.9/S.11

### 8.2 Test File Structure
```
lexedge/tests/
├── test_shared_tools.py
├── test_orchestrators.py
├── test_practice_leads/
│   ├── test_criminal_lead.py
│   ├── test_civil_lead.py
│   └── ...
└── test_integration.py
```

---

## 9. Migration Strategy

### 9.1 Deprecation Plan
| Current Agent | Action | Target |
|--------------|--------|--------|
| LawyerAgent | Deprecate | Use practice leads |
| CaseIntakeAgent | Merge | IntakeRouterAgent |
| ContractAnalysisAgent | Merge | CorporateCommercialLeadAgent |
| LegalResearchAgent | Tools to shared_tools | Keep as utility |

### 9.2 Backward Compatibility
- Keep existing API endpoints working during transition
- Add feature flags to toggle between old and new agent hierarchy
- Document breaking changes

---

## 10. Implementation Checklist

### Phase 1 Checklist
- [x] Create `shared_tools/` directory and `__init__.py`
- [x] Implement `statute_mapper.py` with BNS/BNSS/BSA mapping
- [x] Implement `case_law_research.py` for India courts
- [x] Implement `court_drafting.py` with Indian court formats
- [x] Implement `quality_gatekeeper.py`
- [x] Create `prompts/` directory with system prompts
- [x] Create `models/case_packet.py`
- [x] Create `orchestrators/router_agent.py`
- [x] Create `orchestrators/gatekeeper_agent.py`
- [x] Create `practice_leads/criminal/`
- [x] Create `practice_leads/civil/`
- [x] Create `practice_leads/corporate/`
- [x] Update `root_agent.py`
- [x] Update `instruction_providers.py`
- [ ] Run smoke tests 1-3

### Phase 2 Checklist
- [x] Create `practice_leads/property/`
- [x] Create `practice_leads/family/`
- [x] Create `practice_leads/constitutional/`
- [x] Create `practice_leads/taxation/`
- [x] Implement remaining shared tools
- [x] Create `orchestrators/prompt_coach_agent.py`
- [ ] Run smoke tests 4-9

### Phase 3 Checklist
- [x] Create `practice_leads/ip/`
- [ ] Implement mini-agents (optional)
- [ ] Full integration testing
- [ ] Performance optimization
- [ ] Documentation update
- [ ] Run all smoke tests

---

## 11. Notes & Considerations

### 11.1 India-Specific Requirements
- BNS replaced IPC (effective July 2024)
- BNSS replaced CrPC (effective July 2024)
- BSA replaced IEA (effective July 2024)
- Must support cross-mapping between old and new codes
- Court formats vary by state (some standardization needed)

### 11.2 Citation Handling
- All citations should be flagged as "Needs Verification" by default
- Never invent case law
- Provide verification sources (SCC, Manupatra, Indian Kanoon)

### 11.3 Drafting Standards
- Follow court-specific formatting
- Use proper legal terminology
- Include placeholders for missing information
- Add verification clauses and disclaimers

---

_End of Implementation Plan_
