from google.adk.agents import LlmAgent
from lexedge.config import LlmModel
from lexedge.sub_agents.legal_research.legal_research_tools import (
    search_case_law,
    search_statutes,
    analyze_legal_issue,
    verify_citations
)
from lexedge.instruction_providers import legal_research_instruction_provider


LegalResearchAgent = LlmAgent(
    name="LegalResearchAgent",
    model=LlmModel,
    description=(
        "Specialized agent for legal research. Searches case law, statutes, regulations, "
        "and provides comprehensive legal analysis with proper citations."
    ),
    instruction=legal_research_instruction_provider,
    tools=[search_case_law, search_statutes, analyze_legal_issue, verify_citations]
)
