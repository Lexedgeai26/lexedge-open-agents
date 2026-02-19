"""
TOOL 3: Citation Verification Tool

Purpose: Validate case existence and citation accuracy;
mark Verified / Needs Verification / Invalid.
"""

import json
import logging
import re
from typing import Optional
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# Known valid citation patterns
CITATION_PATTERNS = {
    "scc": r"\(\d{4}\)\s*\d+\s*SCC\s*\d+",  # (2020) 5 SCC 1
    "air": r"AIR\s*\d{4}\s*(SC|[A-Za-z]+)\s*\d+",  # AIR 2020 SC 1234
    "scr": r"\(\d{4}\)\s*\d+\s*SCR\s*\d+",  # (2020) 1 SCR 123
    "scc_supp": r"\d{4}\s*Supp\s*\(\d+\)\s*SCC\s*\d+",  # 1992 Supp (1) SCC 335
    "scale": r"\(\d{4}\)\s*\d+\s*SCALE\s*\d+",  # (2020) 1 SCALE 123
    "cri_lj": r"\d{4}\s*Cri\.?\s*L\.?J\.?\s*\d+",  # 2020 Cri LJ 1234
    "all_er": r"\[\d{4}\]\s*\d+\s*All\s*E\.?R\.?\s*\d+",  # [2020] 1 All ER 123
}

# Known landmark cases for quick verification
VERIFIED_CITATIONS = {
    "(2020) 5 scc 1": "Sushila Aggarwal v. State (NCT of Delhi)",
    "(2014) 2 scc 1": "Lalita Kumari v. Govt. of U.P.",
    "(2014) 8 scc 273": "Arnesh Kumar v. State of Bihar",
    "1992 supp (1) scc 335": "State of Haryana v. Bhajan Lal",
    "(2011) 1 scc 694": "Siddharam Satlingappa Mhetre v. State of Maharashtra",
    "(1980) 2 scc 565": "Gurbaksh Singh Sibbia v. State of Punjab",
    "(2012) 9 scc 460": "Amit Kapoor v. Ramesh Chander",
    "(2006) 6 scc 736": "Indian Oil Corporation v. NEPC India Ltd.",
    "(2000) 4 scc 168": "Hridaya Ranjan Prasad Verma v. State of Bihar",
    "(2016) 7 scc 221": "Subramanian Swamy v. Union of India",
    "(2021) 4 scc 1": "Tofan Singh v. State of Tamil Nadu",
    "(2014) 9 scc 129": "Dashrath Rupsingh Rathod v. State of Maharashtra",
    "(2018) 1 scc 560": "Meters and Instruments Pvt. Ltd. v. Kanchan Mehta",
    "(1997) 3 scc 261": "L. Chandra Kumar v. Union of India",
    "air 1950 sc 124": "Romesh Thappar v. State of Madras",
    "(2017) 8 scc 446": "Rajesh Sharma v. State of U.P.",
    "(2018) 10 scc 443": "Social Action Forum v. Union of India",
}


def verify_citation(
    case_name: str,
    citation: str,
    court: str = "Supreme Court",
    tool_context: ToolContext = None
) -> str:
    """
    Validate case existence and citation accuracy.

    Args:
        case_name: Name of the case (e.g., "Lalita Kumari v. Govt. of U.P.")
        citation: Citation provided (e.g., "(2014) 2 SCC 1")
        court: Court name (e.g., "Supreme Court", "Delhi High Court")
        tool_context: ADK ToolContext

    Returns:
        JSON with verification status, corrections, and notes
    """
    logger.info(f"[CITATION_VERIFIER] Verifying: {case_name} - {citation}")

    result = {
        "response_type": "citation_verification",
        "case_name": case_name,
        "citation_provided": citation,
        "court": court,
        "status": "NEEDS VERIFICATION",
        "format_check": "Unknown",
        "suggestions": [],
        "verification_sources": [
            "SCC Online (scconline.com)",
            "Manupatra (manupatra.com)",
            "Indian Kanoon (indiankanoon.org)",
            "Supreme Court website (sci.gov.in)"
        ],
        "disclaimer": "AI cannot verify case existence. Always verify on official sources."
    }

    # Normalize citation for comparison
    citation_normalized = citation.lower().strip()
    citation_normalized = re.sub(r'\s+', ' ', citation_normalized)

    # Check citation format
    format_valid = False
    detected_format = None

    for format_name, pattern in CITATION_PATTERNS.items():
        if re.search(pattern, citation, re.IGNORECASE):
            format_valid = True
            detected_format = format_name
            break

    if format_valid:
        result["format_check"] = f"Valid format detected: {detected_format.upper()}"
    else:
        result["format_check"] = "Non-standard format - verify manually"
        result["suggestions"].append("Citation format may be non-standard. Check for typos.")

    # Check against known verified citations
    if citation_normalized in VERIFIED_CITATIONS:
        verified_case = VERIFIED_CITATIONS[citation_normalized]
        result["status"] = "LIKELY VALID"
        result["verified_case_name"] = verified_case

        # Check if case name matches
        if case_name.lower().strip() in verified_case.lower() or verified_case.lower() in case_name.lower():
            result["case_name_match"] = "MATCH"
        else:
            result["case_name_match"] = "PARTIAL/MISMATCH"
            result["suggestions"].append(f"Case name in database: {verified_case}")
    else:
        result["status"] = "NEEDS VERIFICATION"
        result["suggestions"].append("Citation not found in landmark cases database.")
        result["suggestions"].append("This does not mean it's invalid - verify on official sources.")

    # Extract year from citation for sanity check
    year_match = re.search(r'\b(19|20)\d{2}\b', citation)
    if year_match:
        year = int(year_match.group())
        result["year_extracted"] = year

        # Basic sanity checks
        if year > 2026:
            result["suggestions"].append(f"Warning: Year {year} is in the future. Please verify.")
            result["status"] = "SUSPICIOUS"
        elif year < 1950:
            result["suggestions"].append("Note: Pre-independence citation. Verify carefully.")

    # Court-specific checks
    court_lower = court.lower()
    if "supreme" in court_lower:
        if "scc" not in citation_normalized and "air" not in citation_normalized and "scr" not in citation_normalized:
            result["suggestions"].append("Supreme Court cases typically cited in SCC/AIR/SCR format.")
    elif "high court" in court_lower:
        # HC citations vary by state
        result["suggestions"].append("High Court citations vary by state. Check state-specific reporters.")

    # Add verification instructions
    result["verification_steps"] = [
        f"1. Search '{case_name}' on SCC Online or Indian Kanoon",
        f"2. Verify citation format matches: {citation}",
        "3. Confirm court, year, and parties match",
        "4. Check for any subsequent history (overruled, distinguished)",
        "5. Download official copy for record"
    ]

    return json.dumps(result, indent=2, ensure_ascii=False)


def check_citation_format(citation: str) -> dict:
    """Check if citation follows standard format."""
    for format_name, pattern in CITATION_PATTERNS.items():
        if re.search(pattern, citation, re.IGNORECASE):
            return {"valid": True, "format": format_name}
    return {"valid": False, "format": "unknown"}


def extract_citation_components(citation: str) -> dict:
    """Extract year, volume, reporter, page from citation."""
    components = {
        "year": None,
        "volume": None,
        "reporter": None,
        "page": None
    }

    # Try SCC format: (2020) 5 SCC 1
    scc_match = re.match(r'\((\d{4})\)\s*(\d+)\s*(SCC)\s*(\d+)', citation, re.IGNORECASE)
    if scc_match:
        components["year"] = int(scc_match.group(1))
        components["volume"] = int(scc_match.group(2))
        components["reporter"] = scc_match.group(3)
        components["page"] = int(scc_match.group(4))
        return components

    # Try AIR format: AIR 2020 SC 1234
    air_match = re.match(r'AIR\s*(\d{4})\s*(\w+)\s*(\d+)', citation, re.IGNORECASE)
    if air_match:
        components["year"] = int(air_match.group(1))
        components["reporter"] = f"AIR {air_match.group(2)}"
        components["page"] = int(air_match.group(3))
        return components

    return components
