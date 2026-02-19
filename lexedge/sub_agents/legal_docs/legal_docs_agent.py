from google.adk.agents import LlmAgent
from lexedge.config import LlmModel
from lexedge.sub_agents.legal_docs.legal_docs_tools import (
    analyze_legal_document,
    generate_legal_summary,
    review_contract,
    draft_legal_document
)
from lexedge.instruction_providers import legal_docs_instruction_provider


LegalDocsAgent = LlmAgent(
    name="LegalDocsAgent",
    model=LlmModel,
    description=(
        "Specialized agent for legal documentation. Analyzes contracts, agreements, "
        "legal filings, and generates structured legal summaries."
    ),
    instruction=legal_docs_instruction_provider,
    tools=[analyze_legal_document, generate_legal_summary, review_contract, draft_legal_document]
)
