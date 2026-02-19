from google.adk.agents import LlmAgent
from lexedge.config import LlmModel
from lexedge.sub_agents.case_intake.case_intake_tools import (
    collect_client_info,
    check_conflicts,
    create_engagement_letter,
    create_case_profile
)
from lexedge.instruction_providers import case_intake_instruction_provider


CaseIntakeAgent = LlmAgent(
    name="CaseIntakeAgent",
    model=LlmModel,
    description=(
        "Specialized agent for case intake. Collects client information, performs conflict checks, "
        "creates engagement letters, and establishes case profiles."
    ),
    instruction=case_intake_instruction_provider,
    tools=[collect_client_info, check_conflicts, create_engagement_letter, create_case_profile]
)
