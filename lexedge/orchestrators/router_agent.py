"""
Intake & Router Agent

Orchestrator that classifies practice area, identifies forum,
and routes to appropriate lead agents.
"""

from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext

try:
    from lexedge.config import LlmModel
except ImportError:
    from ..config import LlmModel

from lexedge.prompts.agent_prompts import get_router_agent_prompt
from lexedge.shared_tools import refine_prompt, map_statute_sections


def router_instruction_provider(context: ReadonlyContext) -> str:
    """Dynamic instruction provider for router agent."""
    return get_router_agent_prompt()


# Router-specific tools
def classify_practice_area(query: str, facts: str = None) -> str:
    """
    Classify the legal matter into a practice area.

    Args:
        query: User's legal query or request
        facts: Optional facts of the case

    Returns:
        JSON with classification result
    """
    import json

    query_lower = (query + " " + (facts or "")).lower()

    # Classification logic
    if any(word in query_lower for word in ["fir", "bail", "arrest", "criminal", "accused", "quash", "482", "528", "murder", "theft", "cheating", "498a"]):
        area = "criminal"
        agents = ["CriminalLawLeadAgent"]

    elif any(word in query_lower for word in ["divorce", "maintenance", "custody", "marriage", "alimony", "domestic violence", "498a"]):
        area = "family"
        agents = ["FamilyDivorceLeadAgent"]
        if "498a" in query_lower or "criminal" in query_lower:
            agents.append("CriminalLawLeadAgent")

    elif any(word in query_lower for word in ["property", "land", "title", "possession", "partition", "eviction", "tenant", "landlord"]):
        area = "property"
        agents = ["PropertyDisputesLeadAgent"]

    elif any(word in query_lower for word in ["contract", "agreement", "nda", "corporate", "company", "shareholder", "director", "nclt"]):
        area = "corporate"
        agents = ["CorporateCommercialLeadAgent"]

    elif any(word in query_lower for word in ["tax", "income tax", "gst", "148", "assessment", "itat", "cit"]):
        area = "tax"
        agents = ["TaxationLeadAgent"]

    elif any(word in query_lower for word in ["trademark", "patent", "copyright", "ip", "infringement", "design"]):
        area = "ip"
        agents = ["IntellectualPropertyLeadAgent"]

    elif any(word in query_lower for word in ["writ", "habeas", "mandamus", "226", "32", "fundamental right", "constitutional", "pil"]):
        area = "constitutional"
        agents = ["ConstitutionalWritsLeadAgent"]

    elif any(word in query_lower for word in ["suit", "injunction", "plaint", "civil", "recovery", "money", "damages"]):
        area = "civil"
        agents = ["CivilLitigationLeadAgent"]

    else:
        area = "general"
        agents = ["CriminalLawLeadAgent", "CivilLitigationLeadAgent"]

    # Determine urgency
    urgency = "urgent" if any(word in query_lower for word in ["urgent", "immediate", "today", "tomorrow", "hearing", "arrest"]) else "standard"

    # Identify forum hints
    forum = ""
    if "supreme" in query_lower or "slp" in query_lower:
        forum = "Supreme Court of India"
    elif "high court" in query_lower or "hc" in query_lower:
        forum = "High Court"
    elif "sessions" in query_lower:
        forum = "Sessions Court"
    elif "district" in query_lower:
        forum = "District Court"
    elif "nclt" in query_lower:
        forum = "NCLT"
    elif "itat" in query_lower:
        forum = "ITAT"

    result = {
        "response_type": "classification",
        "practice_area": area,
        "primary_agent": agents[0],
        "secondary_agents": agents[1:] if len(agents) > 1 else [],
        "urgency": urgency,
        "forum": forum,
        "routing_notes": f"Classified as {area} matter. Routing to {agents[0]}."
    }

    return json.dumps(result, indent=2)


def create_case_packet_tool(
    practice_area: str,
    parties: str,
    facts: str,
    relief: str,
    forum: str = "",
    statutes: str = ""
) -> str:
    """
    Create a structured case packet for handoff.

    Args:
        practice_area: Classified practice area
        parties: Comma-separated party names
        facts: Key facts of the case
        relief: Relief sought
        forum: Court/forum if known
        statutes: Applicable statutes

    Returns:
        JSON case packet
    """
    import json
    from datetime import datetime

    party_list = [p.strip() for p in parties.split(",") if p.strip()]
    fact_list = [f.strip() for f in facts.split(".") if f.strip()]
    statute_list = [s.strip() for s in statutes.split(",") if s.strip()]

    case_packet = {
        "jurisdiction": "India",
        "forum": forum,
        "practice_area": practice_area,
        "parties": party_list,
        "petitioner": party_list[0] if party_list else "",
        "respondent": party_list[1] if len(party_list) > 1 else "State",
        "facts": fact_list,
        "relief_sought": relief,
        "statutes": statute_list,
        "time_sensitivity": "standard",
        "created_at": datetime.now().isoformat()
    }

    return json.dumps(case_packet, indent=2)


IntakeRouterAgent = LlmAgent(
    name="IntakeRouterAgent",
    model=LlmModel,
    description=(
        "Intake & Router Agent. Classifies legal matters by practice area, "
        "identifies forum, and routes to appropriate lead agents. "
        "Use this agent to determine which specialized agent should handle a query."
    ),
    instruction=router_instruction_provider,
    tools=[
        classify_practice_area,
        create_case_packet_tool,
        refine_prompt
    ]
)
