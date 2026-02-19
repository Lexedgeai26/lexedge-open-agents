"""
Quality & Risk Gatekeeper Agent

Orchestrator that validates outputs before delivery.
Ensures jurisdiction correctness, statute accuracy, and citation verification.
"""

from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext

try:
    from lexedge.config import LlmModel
except ImportError:
    from ..config import LlmModel

from lexedge.prompts.agent_prompts import get_gatekeeper_agent_prompt
from lexedge.shared_tools import validate_output, verify_citation


def gatekeeper_instruction_provider(context: ReadonlyContext) -> str:
    """Dynamic instruction provider for gatekeeper agent."""
    return get_gatekeeper_agent_prompt()


def final_review(output: str, output_type: str = "analysis", practice_area: str = None) -> str:
    """
    Perform final quality review on output.

    Args:
        output: The draft/research output to review
        output_type: Type of output (analysis, research_memo, arguments, etc.)
        practice_area: Practice area for specialized checks

    Returns:
        JSON with review results and recommendations
    """
    import json
    import re

    result = {
        "response_type": "final_review",
        "output_type": output_type,
        "overall_status": "NEEDS REVIEW",
        "checks": [],
        "issues": [],
        "recommendations": [],
        "disclaimer_present": False
    }

    output_lower = output.lower()

    # Check 1: Jurisdiction
    if "india" in output_lower or "indian" in output_lower:
        result["checks"].append({"check": "Jurisdiction", "status": "PASS", "note": "India jurisdiction confirmed"})
    else:
        result["checks"].append({"check": "Jurisdiction", "status": "WARNING", "note": "Jurisdiction not explicitly mentioned"})
        result["issues"].append("Consider adding explicit jurisdiction reference")

    # Check 2: New codes usage
    has_new_codes = any(code in output_lower for code in ["bns", "bnss", "bsa"])
    has_old_codes = any(code in output_lower for code in ["ipc", "crpc", "iea"])

    if has_new_codes:
        result["checks"].append({"check": "New Codes", "status": "PASS", "note": "BNS/BNSS/BSA references found"})
    elif has_old_codes:
        result["checks"].append({"check": "New Codes", "status": "WARNING", "note": "Only old codes (IPC/CrPC/IEA) found"})
        result["recommendations"].append("Update to BNS/BNSS/BSA for matters post July 2024")

    # Check 3: Citations
    citation_patterns = [
        r"\(\d{4}\)\s*\d+\s*SCC\s*\d+",
        r"AIR\s*\d{4}\s*\w+\s*\d+",
    ]

    citations_found = []
    for pattern in citation_patterns:
        citations_found.extend(re.findall(pattern, output, re.IGNORECASE))

    if citations_found:
        result["checks"].append({
            "check": "Citations",
            "status": "WARNING",
            "note": f"Found {len(citations_found)} citations - ALL NEED VERIFICATION"
        })
        result["citations_to_verify"] = citations_found
    else:
        result["checks"].append({"check": "Citations", "status": "INFO", "note": "No formal citations found"})

    # Check 4: Placeholders
    placeholders = re.findall(r"\[[A-Z\s]+\]", output)
    if placeholders:
        unique_placeholders = list(set(placeholders))
        result["checks"].append({
            "check": "Placeholders",
            "status": "INFO",
            "note": f"Found {len(unique_placeholders)} placeholder(s) to fill"
        })
        result["placeholders"] = unique_placeholders



    # Check 6: Disclaimer
    if "ai-assisted" in output_lower or "professional review" in output_lower or "verify" in output_lower:
        result["disclaimer_present"] = True
        result["checks"].append({"check": "Disclaimer", "status": "PASS", "note": "Disclaimer present"})
    else:
        result["checks"].append({"check": "Disclaimer", "status": "FAIL", "note": "No disclaimer found"})
        result["recommendations"].append("Add standard disclaimer about AI-assisted output")

    # Determine overall status
    fails = sum(1 for c in result["checks"] if c["status"] == "FAIL")
    warnings = sum(1 for c in result["checks"] if c["status"] == "WARNING")

    if fails == 0 and warnings <= 2:
        result["overall_status"] = "READY"
        result["summary"] = "Output is ready for professional review"
    else:
        result["overall_status"] = "NEEDS REVIEW"
        result["summary"] = f"Found {fails} issues and {warnings} warnings. Review before use."

    return json.dumps(result, indent=2)


def add_disclaimer(output: str) -> str:
    """
    Disclaimer injection is disabled — disclaimer is now handled at the UI layer.

    Previously this appended the standard AI disclaimer to every output, which
    caused it to appear in the user-facing chat. The disclaimer is now shown
    via the UI footer instead.
    """
    import json
    result = {
        "response_type": "disclaimer_added",
        "disclaimer_was_missing": False,
        "output": output
    }
    return json.dumps(result, indent=2)


QualityGatekeeperAgent = LlmAgent(
    name="QualityGatekeeperAgent",
    model=LlmModel,
    description=(
        "Quality & Risk Gatekeeper Agent. Validates legal outputs before delivery. "
        "Checks jurisdiction, statute accuracy, citations, and completeness. "
        "Use this agent for final review of any legal document or research."
    ),
    instruction=gatekeeper_instruction_provider,
    tools=[
        final_review,
        add_disclaimer,
        validate_output,
        verify_citation
    ]
)
