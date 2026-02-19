"""
Friendly names for LexEdge Legal AI agents.
"""

AGENT_NAMES = {
    # Legal Specialists
    "LawyerAgent": "LexEdge Counsel",
    "LegalDocsAgent": "LexEdge Documents",
    "ContractAnalysisAgent": "LexEdge Contracts",
    "LegalResearchAgent": "LexEdge Research",
    "CaseManagementAgent": "LexEdge Case Manager",
    "ComplianceAgent": "LexEdge Compliance",
    "CaseIntakeAgent": "LexEdge Intake",
    "LegalCorrespondenceAgent": "LexEdge Correspondence",
    
    # Legal Specialty Areas
    "CorporateLawAgent": "LexEdge Corporate",
    "IPLawAgent": "LexEdge IP",
    "TaxLawAgent": "LexEdge Tax",
    "ImmigrationAgent": "LexEdge Immigration",
    "EmploymentLawAgent": "LexEdge Employment",
    "RealEstateLawAgent": "LexEdge Real Estate",
    "LitigationAgent": "LexEdge Litigation",
    "FamilyLawAgent": "LexEdge Family",
    "CriminalLawAgent": "LexEdge Criminal",
    "BankruptcyAgent": "LexEdge Bankruptcy",
    
    # Core Agents
    "GeneralAgent": "LexEdge Assistant",
    "ClientAssistantAgent": "LexEdge Client Services",
    
    # Orchestrators
    "RootAgent": "LexEdge",
    "LegalRouterAgent": "LexEdge Router",
    "RouterAgent": "LexEdge Router"
}

def get_agent_friendly_name(agent_id: str) -> str:
    """Get a friendly name for an agent ID."""
    if not agent_id:
        return "LexEdge"
    
    # Handle both tool names and agent names
    name = agent_id
    if name.endswith("Agent"):
        pass
    elif "legal" in name.lower() or "law" in name.lower():
        # Map tool to legal specialist if we can detect it
        pass
        
    return AGENT_NAMES.get(name, name)
