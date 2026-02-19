"""Intellectual Property Lead Agent - Phase 3 Implementation"""
from google.adk.agents import LlmAgent
try:
    from lexedge.config import LlmModel
except ImportError:
    from ...config import LlmModel
from lexedge.prompts.agent_prompts import get_ip_lead_prompt
from lexedge.shared_tools import map_statute_sections, research_case_law, analyze_document, validate_output

IntellectualPropertyLeadAgent = LlmAgent(
    name="IntellectualPropertyLeadAgent",
    model=LlmModel,
    description="IP Lead Agent. Handles trademarks, patents, copyrights, infringement, licensing matters.",
    instruction=get_ip_lead_prompt,
    tools=[map_statute_sections, research_case_law, analyze_document, validate_output]
)
