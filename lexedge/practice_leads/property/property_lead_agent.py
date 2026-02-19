"""Property Disputes Lead Agent - Phase 2 Implementation"""
from google.adk.agents import LlmAgent
try:
    from lexedge.config import LlmModel
except ImportError:
    from ...config import LlmModel
from lexedge.prompts.agent_prompts import get_property_lead_prompt
from lexedge.shared_tools import map_statute_sections, research_case_law, analyze_document, validate_output

PropertyDisputesLeadAgent = LlmAgent(
    name="PropertyDisputesLeadAgent",
    model=LlmModel,
    description="Property Disputes Lead Agent. Handles title, possession, partition, specific performance, eviction matters.",
    instruction=get_property_lead_prompt,
    tools=[map_statute_sections, research_case_law, analyze_document, validate_output]
)
