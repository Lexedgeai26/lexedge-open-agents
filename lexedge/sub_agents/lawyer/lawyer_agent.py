from google.adk.agents import LlmAgent
from lexedge.config import LlmModel
from lexedge.sub_agents.lawyer.lawyer_tools import (
    legal_analysis_assessment,
    legal_specialty_query,
    get_case_data,
    analyze_legal_document
)
from lexedge.instruction_providers import lawyer_agent_instruction_provider

LawyerAgent = LlmAgent(
    name="LawyerAgent",
    model=LlmModel,
    description="The primary legal intelligence of LexEdge. Handles legal analysis, case strategy, specialist queries, and document review.",
    instruction=lawyer_agent_instruction_provider,
    tools=[
       legal_analysis_assessment,
       legal_specialty_query,
       get_case_data,
       analyze_legal_document
    ]   
)
