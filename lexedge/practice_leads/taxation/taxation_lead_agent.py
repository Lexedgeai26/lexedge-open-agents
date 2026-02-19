"""Taxation Lead Agent - Phase 2 Implementation"""
from google.adk.agents import LlmAgent
try:
    from lexedge.config import LlmModel
except ImportError:
    from ...config import LlmModel
from lexedge.prompts.agent_prompts import get_taxation_lead_prompt
from lexedge.shared_tools import map_statute_sections, research_case_law, analyze_document, validate_output

TaxationLeadAgent = LlmAgent(
    name="TaxationLeadAgent",
    model=LlmModel,
    description="Taxation Lead Agent. Handles IT notices, GST, appeals, stay applications, rectification matters.",
    instruction=get_taxation_lead_prompt,
    tools=[map_statute_sections, research_case_law, analyze_document, validate_output]
)
