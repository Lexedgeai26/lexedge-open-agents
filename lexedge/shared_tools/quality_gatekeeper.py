"""
TOOL 8: Quality & Risk Gatekeeper Tool

Purpose: Final checks for jurisdiction, limitation, statute correctness,
weak points, unverifiable citations.
"""

import json
import logging
import re
from typing import List, Optional
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# Standard disclaimer text
STANDARD_DISCLAIMER = """
Note: This analysis/research is AI-assisted and for professional review. Verify all citations, sections, limitation, and jurisdiction on official sources (e.g., court websites, SCC/Manupatra) before relying on it.
"""


def validate_output(
    output: str,
    output_type: str = "analysis",
    practice_area: str = None,
    tool_context: ToolContext = None
) -> str:
    """
    Final quality and risk assessment of legal output.

    Args:
        output: The draft/research output to validate
        output_type: Type of output (draft/research_memo/arguments/analysis)
        practice_area: Practice area for specialized checks
        tool_context: ADK ToolContext

    Returns:
        JSON with status (READY/NEEDS REVIEW), risk notes, improvements
    """
    logger.info(f"[QUALITY_GATEKEEPER] Validating {output_type}...")

    result = {
        "response_type": "quality_assessment",
        "output_type": output_type,
        "overall_status": "NEEDS REVIEW",  # Default to cautious
        "checks_performed": [],
        "issues_found": [],
        "risk_notes": [],
        "suggested_improvements": [],
        "citation_status": {
            "citations_found": [],
            "unverified_citations": [],
            "potentially_invalid": []
        },
        "compliance_notes": [],
        "disclaimer_added": False,
        "final_disclaimer": STANDARD_DISCLAIMER.strip()
    }

    # Perform checks
    result = check_jurisdiction(result, output)
    result = check_statute_references(result, output)
    result = check_citations(result, output)
    result = check_limitation_concerns(result, output)
    result = check_completeness(result, output, output_type)
    result = check_formatting(result, output, output_type)

    # Practice-area specific checks
    if practice_area:
        result = check_practice_specific(result, output, practice_area)

    # Determine overall status
    critical_issues = [i for i in result["issues_found"] if i.get("severity") == "HIGH"]
    medium_issues = [i for i in result["issues_found"] if i.get("severity") == "MEDIUM"]

    if len(critical_issues) == 0 and len(medium_issues) <= 2:
        result["overall_status"] = "READY"
        result["status_note"] = "Output appears ready for professional review. Verify citations before use."
    else:
        result["overall_status"] = "NEEDS REVIEW"
        result["status_note"] = f"Found {len(critical_issues)} critical and {len(medium_issues)} medium issues. Review and address before use."

    return json.dumps(result, indent=2, ensure_ascii=False)


def check_jurisdiction(result: dict, output: str) -> dict:
    """Check for jurisdiction-related issues."""
    result["checks_performed"].append("Jurisdiction Check")
    output_lower = output.lower()

    # Check if jurisdiction is mentioned
    if not any(word in output_lower for word in ["india", "indian", "high court", "sessions", "district court", "supreme court"]):
        result["issues_found"].append({
            "type": "JURISDICTION",
            "message": "Jurisdiction not clearly specified. Ensure India/specific court is mentioned.",
            "severity": "MEDIUM"
        })

    # Check for foreign law references (might be intentional, but flag)
    foreign_refs = ["us law", "uk law", "american", "english law", "common law of england"]
    for ref in foreign_refs:
        if ref in output_lower:
            result["risk_notes"].append(f"Foreign law reference found: '{ref}'. Ensure applicability in Indian context.")

    return result


def check_statute_references(result: dict, output: str) -> dict:
    """Check statute references for correctness."""
    result["checks_performed"].append("Statute Reference Check")

    # Check for old vs new code references
    old_codes = ["ipc", "crpc", "indian penal code", "code of criminal procedure", "indian evidence act", "iea"]
    new_codes = ["bns", "bnss", "bsa", "bharatiya nyaya sanhita", "bharatiya nagarik suraksha sanhita", "bharatiya sakshya adhiniyam"]

    output_lower = output.lower()

    has_old = any(code in output_lower for code in old_codes)
    has_new = any(code in output_lower for code in new_codes)

    if has_old and not has_new:
        result["risk_notes"].append("Document uses old criminal codes (IPC/CrPC/IEA). Consider updating to BNS/BNSS/BSA for matters post July 2024.")
        result["suggested_improvements"].append("Add cross-references to new codes (BNS/BNSS/BSA) for completeness.")

    if has_new:
        result["compliance_notes"].append("Document references new criminal codes (BNS/BNSS/BSA) - Good.")

    # Check for section number validity (basic pattern check)
    section_patterns = re.findall(r"(?:section|s\.|sec\.?)\s*(\d+[A-Z]?(?:/\d+)?)", output, re.IGNORECASE)
    for section in section_patterns:
        try:
            num = int(re.match(r"(\d+)", section).group(1))
            if num > 600:  # Most Indian codes don't exceed this
                result["issues_found"].append({
                    "type": "STATUTE",
                    "message": f"Section {section} seems unusually high. Verify correctness.",
                    "severity": "LOW"
                })
        except:
            pass

    return result


def check_citations(result: dict, output: str) -> dict:
    """Check citations for format and flag for verification."""
    result["checks_performed"].append("Citation Check")

    # Find citation patterns
    citation_patterns = [
        r"\(\d{4}\)\s*\d+\s*SCC\s*\d+",  # (2020) 5 SCC 1
        r"AIR\s*\d{4}\s*\w+\s*\d+",  # AIR 2020 SC 1234
        r"\d{4}\s*Supp\s*\(\d+\)\s*SCC\s*\d+",  # 1992 Supp (1) SCC 335
        r"\[\d{4}\]\s*\d+\s*SCR\s*\d+",  # [2020] 1 SCR 123
    ]

    citations_found = []
    for pattern in citation_patterns:
        matches = re.findall(pattern, output, re.IGNORECASE)
        citations_found.extend(matches)

    result["citation_status"]["citations_found"] = list(set(citations_found))

    if citations_found:
        result["citation_status"]["unverified_citations"] = citations_found
        result["risk_notes"].append(f"Found {len(citations_found)} citation(s). ALL REQUIRE INDEPENDENT VERIFICATION.")
        result["suggested_improvements"].append("Verify all citations on SCC Online, Manupatra, or Indian Kanoon before filing.")

    # Check for case name patterns that might be hallucinated
    case_patterns = re.findall(r"([A-Z][a-zA-Z]+\s+(?:v\.|vs\.?|versus)\s+[A-Z][a-zA-Z\s]+)", output)
    for case in case_patterns:
        result["citation_status"]["unverified_citations"].append(case.strip())

    # Flag if no citations in legal research
    if "research" in str(result.get("output_type", "")).lower() and not citations_found:
        result["issues_found"].append({
            "type": "CITATION",
            "message": "No citations found in research output. Add relevant case law references.",
            "severity": "MEDIUM"
        })

    return result


def check_limitation_concerns(result: dict, output: str) -> dict:
    """Check for limitation period concerns."""
    result["checks_performed"].append("Limitation Check")
    output_lower = output.lower()

    # Keywords that suggest limitation might be relevant
    limitation_keywords = ["limitation", "time bar", "delay", "laches", "prescribed period", "statute of limitation"]

    if any(kw in output_lower for kw in limitation_keywords):
        result["risk_notes"].append("Document mentions limitation. VERIFY: Ensure filing is within limitation period.")

    # Check for specific limitation-related concerns
    if "delay" in output_lower:
        if "explained" not in output_lower and "condone" not in output_lower:
            result["suggested_improvements"].append("If there is delay, add explanation for condonation of delay.")

    return result


def check_completeness(result: dict, output: str, output_type: str) -> dict:
    """Check for completeness of document."""
    result["checks_performed"].append("Completeness Check")
    output_lower = output.lower()

    if output_type == "analysis":
        # Essential components for legal analysis
        required_components = {
            "strategic_assessment": ["strategic", "strategy", "assessment"],
            "statutory_compliance": ["section", "statute", "compliance", "law"],
            "procedural_roadmap": ["procedure", "procedural", "steps", "roadmap"]
        }

        for component, keywords in required_components.items():
            if not any(kw in output_lower for kw in keywords):
                result["issues_found"].append({
                    "type": "COMPLETENESS",
                    "message": f"Missing analysis component: {component.replace('_', ' ').title()}",
                    "severity": "MEDIUM"
                })

        # Check for placeholders that need to be filled
        placeholders = re.findall(r"\[[A-Z\s]+\]", output)
        if placeholders:
            unique_placeholders = list(set(placeholders))
            result["risk_notes"].append(f"Found {len(unique_placeholders)} placeholder(s) that need to be filled: {', '.join(unique_placeholders[:5])}")

    return result


def check_formatting(result: dict, output: str, output_type: str) -> dict:
    """Check formatting standards."""
    result["checks_performed"].append("Formatting Check")

    if output_type == "analysis":
        # Check line length (very long lines might indicate formatting issues)
        lines = output.split("\n")
        long_lines = [i for i, line in enumerate(lines) if len(line) > 300]
        if long_lines:
            result["suggested_improvements"].append("Some paragraphs are very long. Consider breaking into smaller paragraphs for readability.")

        # Check for numbered paragraphs
        if not re.search(r"^\d+\.", output, re.MULTILINE):
            result["suggested_improvements"].append("Consider using numbered paragraphs for clarity.")

    return result


def check_practice_specific(result: dict, output: str, practice_area: str) -> dict:
    """Perform practice-area specific checks."""
    result["checks_performed"].append(f"Practice-Specific Check ({practice_area})")
    output_lower = output.lower()
    pa_lower = practice_area.lower()

    if "criminal" in pa_lower:
        # Criminal law specific checks
        if "bail" in output_lower:
            if "antecedent" not in output_lower:
                result["suggested_improvements"].append("Consider addressing criminal antecedents (if clean).")
            if "roots in society" not in output_lower and "deep roots" not in output_lower:
                result["suggested_improvements"].append("Consider mentioning deep roots in society for bail matters.")

        if "quash" in output_lower:
            if "bhajan lal" not in output_lower:
                result["suggested_improvements"].append("Consider citing Bhajan Lal guidelines for quashing petition.")

    elif "family" in pa_lower:
        # Family law specific checks
        if "custody" in output_lower:
            if "welfare" not in output_lower and "best interest" not in output_lower:
                result["risk_notes"].append("Custody matters: Paramount consideration should be child's welfare/best interest.")

        if "maintenance" in output_lower:
            if "income" not in output_lower:
                result["suggested_improvements"].append("Maintenance: Include details of income and financial capacity.")

    elif "property" in pa_lower:
        # Property law specific checks
        if "title" not in output_lower and "possession" not in output_lower:
            result["suggested_improvements"].append("Property matters: Clarify title and possession status.")

    elif "corporate" in pa_lower or "commercial" in pa_lower:
        # Corporate/Commercial specific checks
        if "jurisdiction" not in output_lower:
            result["suggested_improvements"].append("Commercial matters: Specify governing law and jurisdiction clause.")

        if "arbitration" in output_lower:
            result["compliance_notes"].append("Arbitration clause present - verify compliance with Arbitration Act provisions.")

    return result


def add_disclaimer(output: str) -> str:
    """Disclaimer injection is disabled — handled at the UI layer instead."""
    # Previously this appended a disclaimer string to every response.
    # This caused the disclaimer to leak into user-facing chat messages.
    # The disclaimer is now surfaced via the UI footer, not injected into LLM output.
    return output
