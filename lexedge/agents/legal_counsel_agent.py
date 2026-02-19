"""
LegalCounselAgent - Single sub-agent that handles all legal work.

Uses Python Ollama SDK tools to call Ollama for actual legal responses.
The root agent (gpt-oss via ADK/LiteLlm) delegates here for all legal tasks.
"""

from google.adk.agents import LlmAgent

try:
    from lexedge.config import LlmModel
except ImportError:
    from ..config import LlmModel

from .legal_counsel_tools import legal_query, draft_document, analyze_document
from lexedge.prompts.prompt_loader import load_prompt


LegalCounselAgent = LlmAgent(
    name="LegalCounselAgent",
    model=LlmModel,
    description=(
        "Handles all legal queries, drafting, and document analysis for India. "
        "Covers criminal, civil, property, family, corporate, constitutional, "
        "taxation, and IP matters. Uses specialized tools to provide detailed, "
        "court-ready legal guidance."
    ),
    instruction=load_prompt("agents/legal_counsel_agent.txt"),
    tools=[legal_query, draft_document, analyze_document],
    sub_agents=[],
)
