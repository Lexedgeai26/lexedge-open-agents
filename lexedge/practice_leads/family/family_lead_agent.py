"""Family & Divorce Lead Agent - Phase 2 Implementation"""
from google.adk.agents import LlmAgent
try:
    from lexedge.config import LlmModel
except ImportError:
    from ...config import LlmModel
from lexedge.prompts.agent_prompts import get_family_lead_prompt
from lexedge.shared_tools import map_statute_sections, research_case_law, analyze_document, validate_output

FamilyDivorceLeadAgent = LlmAgent(
    name="FamilyDivorceLeadAgent",
    model=LlmModel,
    description="Family & Divorce Lead Agent. Handles divorce, maintenance, custody, DV matters with technical precision.",
    instruction=get_family_lead_prompt,
    tools=[map_statute_sections, research_case_law, analyze_document, validate_output]
)
