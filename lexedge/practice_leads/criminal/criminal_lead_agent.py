"""
Criminal Law Lead Agent

Specialized agent for criminal law matters in India.

Scope:
- FIR/Complaints
- Anticipatory Bail (S.482 BNSS / S.438 CrPC)
- Regular Bail (S.483 BNSS / S.439 CrPC)
- Quashing Petitions (S.528 BNSS / S.482 CrPC)
- Discharge Applications (S.251 BNSS)
- Remand/Custody matters
- NI Act Section 138 (Cheque Bounce)
- Revision/Appeals
- Cross-examination preparation
"""

from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext

try:
    from lexedge.config import LlmModel
except ImportError:
    from ...config import LlmModel

from lexedge.prompts.agent_prompts import get_criminal_lead_prompt
from lexedge.shared_tools import (
    map_statute_sections,
    research_case_law,
    verify_citation,
    analyze_document,
    build_arguments,
    validate_output
)


def criminal_instruction_provider(context: ReadonlyContext) -> str:
    """Dynamic instruction provider for criminal law lead agent."""
    return get_criminal_lead_prompt()





def analyze_fir(fir_content: str) -> str:
    """
    Analyze FIR content and provide strategic insights.

    Args:
        fir_content: Text content of the FIR

    Returns:
        JSON with FIR analysis and defense strategy
    """
    import json
    import re

    result = {
        "response_type": "fir_analysis",
        "summary": "",
        "sections_identified": [],
        "key_allegations": [],
        "weaknesses_in_fir": [],
        "defense_strategy": [],
        "bail_prospects": "",
        "quashing_potential": "",
        "immediate_actions": []
    }

    fir_lower = fir_content.lower()

    # Extract sections
    section_patterns = [
        r"(?:section|s\.|sec\.?)\s*(\d+[A-Z]?(?:/\d+)?)\s*(?:of\s+)?(?:BNS|IPC)",
        r"(?:BNS|IPC)\s*(?:Section)?\s*(\d+[A-Z]?)",
        r"u/s\s*(\d+[A-Z]?(?:/\d+)?)"
    ]

    for pattern in section_patterns:
        matches = re.findall(pattern, fir_content, re.IGNORECASE)
        result["sections_identified"].extend(matches)

    result["sections_identified"] = list(set(result["sections_identified"]))

    # Analyze for common issues
    if any(word in fir_lower for word in ["cheating", "fraud", "420", "318"]):
        result["key_allegations"].append("Cheating/Fraud allegations")
        result["weaknesses_in_fir"].append("Check if dishonest intention at inception is established")
        result["quashing_potential"] = "HIGH if dispute is civil in nature"

    if any(word in fir_lower for word in ["murder", "302", "103"]):
        result["key_allegations"].append("Murder allegations")
        result["bail_prospects"] = "Difficult - Non-bailable, non-compoundable"
        result["quashing_potential"] = "LOW unless clear abuse of process"

    if any(word in fir_lower for word in ["498a", "cruelty", "dowry"]):
        result["key_allegations"].append("Matrimonial cruelty allegations")
        result["weaknesses_in_fir"].append("Check for exaggeration and false implication of relatives")
        result["bail_prospects"] = "Moderate - Follow Arnesh Kumar guidelines"

    # Defense strategy
    result["defense_strategy"] = [
        "Obtain certified copy of FIR",
        "Analyze delay in lodging FIR (if any)",
        "Identify contradictions in allegations",
        "Gather alibi evidence if applicable",
        "Collect documentary evidence to counter allegations",
        "Identify witnesses for defense"
    ]

    # Immediate actions
    result["immediate_actions"] = [
        "File anticipatory bail if arrest apprehended",
        "Collect all relevant documents",
        "Prepare list of defense witnesses",
        "Consider joining investigation voluntarily"
    ]

    result["summary"] = f"FIR involves sections {', '.join(result['sections_identified'][:5])} with {len(result['key_allegations'])} key allegations identified."

    return json.dumps(result, indent=2, ensure_ascii=False)


CriminalLawLeadAgent = LlmAgent(
    name="CriminalLawLeadAgent",
    model=LlmModel,
    description=(
        "Criminal Law Lead Agent for India. Handles FIR/complaints, anticipatory bail, "
        "regular bail, quashing petitions, discharge applications, NI Act 138 matters, "
        "and criminal defense strategy. Uses BNS/BNSS/BSA (new codes) with IPC/CrPC cross-references."
    ),
    instruction=criminal_instruction_provider,
    tools=[
        analyze_fir,
        # Shared tools
        map_statute_sections,
        research_case_law,
        verify_citation,
        analyze_document,
        build_arguments,
        validate_output
    ]
)
