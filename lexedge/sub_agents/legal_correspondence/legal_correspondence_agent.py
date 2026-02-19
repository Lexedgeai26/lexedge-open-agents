from google.adk.agents import LlmAgent
from lexedge.config import LlmModel
from lexedge.sub_agents.legal_correspondence.legal_correspondence_tools import (
    draft_client_letter,
    draft_legal_notice,
    draft_demand_letter,
    draft_settlement_proposal
)

def legal_correspondence_instruction_provider(context) -> str:
    """Instruction provider for legal correspondence agent."""
    from lexedge.config import LEGAL_SETTINGS, get_legal_context_string
    from lexedge.context_manager import agent_context_manager
    
    case_data = agent_context_manager.get_context("CaseProfile").get("data", {})
    client_name = case_data.get("client_name") or "the client"
    legal_context = get_legal_context_string()
    
    return f"""You are the **Legal Correspondence Specialist**.
    Your objective is to draft professional legal correspondence for **{client_name}**.

    {legal_context}

    ### 📋 CORRESPONDENCE PROTOCOLS:
    1. **Client Letters**: Use `draft_client_letter` for client communications.
    2. **Legal Notices**: Use `draft_legal_notice` for formal legal notices.
    3. **Demand Letters**: Use `draft_demand_letter` for demand letters.
    4. **Settlement Proposals**: Use `draft_settlement_proposal` for settlement communications.
    
    ### 🎯 CORRESPONDENCE STANDARDS:
    - Professional, formal legal language
    - Clear and concise communication
    - Appropriate legal citations where needed
    - Proper formatting for jurisdiction: {LEGAL_SETTINGS['jurisdiction']}
    - Include appropriate disclaimers and confidentiality notices
    """


LegalCorrespondenceAgent = LlmAgent(
    name="LegalCorrespondenceAgent",
    model=LlmModel,
    description=(
        "Specialized agent for legal correspondence. Drafts client letters, legal notices, "
        "demand letters, and settlement proposals with professional legal formatting."
    ),
    instruction=legal_correspondence_instruction_provider,
    tools=[draft_client_letter, draft_legal_notice, draft_demand_letter, draft_settlement_proposal]
)
