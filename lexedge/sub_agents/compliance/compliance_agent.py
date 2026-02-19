from google.adk.agents import LlmAgent
from lexedge.config import LlmModel
from lexedge.sub_agents.compliance.compliance_tools import (
    audit_compliance,
    research_regulations,
    assess_compliance_risks,
    review_policies
)
from lexedge.instruction_providers import compliance_instruction_provider


ComplianceAgent = LlmAgent(
    name="ComplianceAgent",
    model=LlmModel,
    description=(
        "Specialized agent for regulatory compliance. Audits compliance status, "
        "researches applicable regulations, and assesses compliance risks."
    ),
    instruction=compliance_instruction_provider,
    tools=[audit_compliance, research_regulations, assess_compliance_risks, review_policies]
)
