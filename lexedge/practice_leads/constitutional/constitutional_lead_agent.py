"""Constitutional & Writs Lead Agent - Phase 2 Implementation"""
from google.adk.agents import LlmAgent
try:
    from lexedge.config import LlmModel
except ImportError:
    from ...config import LlmModel
from lexedge.prompts.agent_prompts import get_constitutional_lead_prompt
from lexedge.shared_tools import map_statute_sections, research_case_law, build_arguments, validate_output

ConstitutionalWritsLeadAgent = LlmAgent(
    name="ConstitutionalWritsLeadAgent",
    model=LlmModel,
    description="Constitutional & Writs Lead Agent. Handles writ petitions, PIL, habeas corpus, Art. 226/32 matters.",
    instruction=get_constitutional_lead_prompt,
    tools=[map_statute_sections, research_case_law, build_arguments, validate_output]
)
