from google.adk.agents import LlmAgent
from lexedge.config import LlmModel
from lexedge.sub_agents.case_management.case_management_tools import (
    track_deadlines,
    generate_case_timeline,
    manage_case_tasks,
    update_case_status
)
from lexedge.instruction_providers import case_management_instruction_provider


CaseManagementAgent = LlmAgent(
    name="CaseManagementAgent",
    model=LlmModel,
    description=(
        "Specialized agent for case management. Tracks deadlines, manages case workflow, "
        "monitors filings, and maintains case timelines."
    ),
    instruction=case_management_instruction_provider,
    tools=[track_deadlines, generate_case_timeline, manage_case_tasks, update_case_status]
)
