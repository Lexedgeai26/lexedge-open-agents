from google.adk.agents import LlmAgent
from lexedge.config import LlmModel
from lexedge.instruction_providers import contract_analysis_instruction_provider


ContractAnalysisAgent = LlmAgent(
    name="ContractAnalysisAgent",
    model=LlmModel,
    description=(
        "Specialized agent for contract analysis. Reviews, analyzes, and drafts contracts "
        "with comprehensive risk assessment and clause-by-clause review."
    ),
    instruction=contract_analysis_instruction_provider,
    tools=[]
)
