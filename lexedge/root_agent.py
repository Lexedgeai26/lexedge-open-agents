"""
LexEdge Root Agent

Central coordinator for the legal multi-agent system.
Routes to orchestrators and practice-area lead agents.

Agent Hierarchy:
├── Orchestrators
│   ├── IntakeRouterAgent (classifies and routes)
│   ├── QualityGatekeeperAgent (validates outputs)
│   └── PromptCoachAgent (refines prompts)
│
├── Practice-Area Leads
│   ├── CriminalLawLeadAgent
│   ├── CivilLitigationLeadAgent
│   ├── PropertyDisputesLeadAgent
│   ├── FamilyDivorceLeadAgent
│   ├── CorporateCommercialLeadAgent
│   ├── ConstitutionalWritsLeadAgent
│   ├── TaxationLeadAgent
│   └── IntellectualPropertyLeadAgent
│
└── Utility Agents (legacy, for backward compatibility)
    ├── CaseManagementAgent
    ├── ComplianceAgent
    └── LegalCorrespondenceAgent
"""

import datetime
import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext

# Use relative import for config
try:
    from lexedge.config import LlmModel
except ImportError:
    from .config import LlmModel

# Import Orchestrators
from .orchestrators import (
    IntakeRouterAgent,
    QualityGatekeeperAgent,
    PromptCoachAgent
)

# Import Practice-Area Lead Agents
from .practice_leads import (
    CriminalLawLeadAgent,
    CivilLitigationLeadAgent,
    PropertyDisputesLeadAgent,
    FamilyDivorceLeadAgent,
    CorporateCommercialLeadAgent,
    ConstitutionalWritsLeadAgent,
    TaxationLeadAgent,
    IntellectualPropertyLeadAgent
)

# Import Utility Agents (legacy, for backward compatibility)
from .sub_agents.case_management.case_management_agent import CaseManagementAgent
from .sub_agents.compliance.compliance_agent import ComplianceAgent
from .sub_agents.legal_correspondence.legal_correspondence_agent import LegalCorrespondenceAgent

# Import prompts
from .prompts.system_prompts import GLOBAL_SAFETY_PROMPT, JURISDICTION_PROMPT, RESPONSE_STYLE_PROMPT

load_dotenv()


def root_agent_instruction_provider(context: ReadonlyContext) -> str:
    """Dynamic instruction provider for the root agent."""
    return f"""{GLOBAL_SAFETY_PROMPT}

You are **LexEdge**, the Lead Legal AI Coordinator for India.

{JURISDICTION_PROMPT}

## DELEGATION PROTOCOLS

Route requests to the appropriate specialized agent:

### ORCHESTRATORS (for workflow management)
- **IntakeRouterAgent**: Use when classifying a new matter or unclear which practice area applies
- **PromptCoachAgent**: Use when user's request is vague and needs refinement
- **QualityGatekeeperAgent**: Use for final validation of any output before delivery

### PRACTICE-AREA LEADS (for substantive legal work)

| Practice Area | Agent | Use When |
|--------------|-------|----------|
| Criminal | **CriminalLawLeadAgent** | FIR analysis, bail strategy, quashing grounds, criminal defense |
| Civil | **CivilLitigationLeadAgent** | Strategic analysis of suits, injunctions, plaints, civil appeals |
| Property | **PropertyDisputesLeadAgent** | Analysis of title, partition, eviction, specific performance |
| Family | **FamilyDivorceLeadAgent** | Analysis of divorce, custody, maintenance, DV matters |
| Corporate | **CorporateCommercialLeadAgent** | Contract review, corporate governance analysis, NCLT strategy |
| Constitutional | **ConstitutionalWritsLeadAgent** | Analysis of writs, PIL grounds, Art. 226/32 strategy |
| Tax | **TaxationLeadAgent** | Analysis of IT notices, GST strategy, taxation appeals |
| IP | **IntellectualPropertyLeadAgent** | Analysis of trademarks, patents, copyrights, infringement |

### UTILITY AGENTS (for support functions)
- **CaseManagementAgent**: Case tracking, deadlines, timeline management
- **ComplianceAgent**: Regulatory compliance, GDPR, corporate compliance
- **LegalCorrespondenceAgent**: Client letters, legal notices, formal correspondence

## ROUTING LOGIC

1. **If request is vague**: Route to PromptCoachAgent for clarification
2. **If practice area is unclear**: Route to IntakeRouterAgent for classification
3. **If practice area is clear**: Route directly to the appropriate Practice Lead
4. **After output is generated**: Route to QualityGatekeeperAgent for validation

## INDIA-SPECIFIC NOTES

- Use BNS/BNSS/BSA (new criminal codes) for matters post July 2024
- Cross-reference old codes (IPC/CrPC/IEA) for clarity
- Flag all citations as needing verification

## DISCLAIMERS

Always remind users:
- AI-generated legal content requires professional review
- All citations must be verified on official sources
- This is technical research and strategy assistance, not legal advice
{RESPONSE_STYLE_PROMPT}
"""


root_agent = LlmAgent(
    name="LexEdge",
    model=LlmModel,
    description=(
        "LexEdge Legal AI Coordinator for India. Routes to specialized practice-area "
        "agents for criminal, civil, property, family, corporate, constitutional, tax, "
        "and IP matters. Uses BNS/BNSS/BSA (new codes) with IPC/CrPC cross-references."
    ),
    instruction=root_agent_instruction_provider,
    sub_agents=[
        # Orchestrators
        IntakeRouterAgent,
        QualityGatekeeperAgent,
        PromptCoachAgent,
        # Practice-Area Lead Agents
        CriminalLawLeadAgent,
        CivilLitigationLeadAgent,
        PropertyDisputesLeadAgent,
        FamilyDivorceLeadAgent,
        CorporateCommercialLeadAgent,
        ConstitutionalWritsLeadAgent,
        TaxationLeadAgent,
        IntellectualPropertyLeadAgent,
        # Utility Agents (legacy)
        CaseManagementAgent,
        ComplianceAgent,
        LegalCorrespondenceAgent,
    ],
    tools=[]
)
