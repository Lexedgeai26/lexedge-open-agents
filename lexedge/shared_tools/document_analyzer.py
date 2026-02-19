"""
TOOL 5: Document Analyzer Tool (PDF / Case File Analyzer)

Purpose: Summarize documents, extract chronology, identify issues/contradictions,
suggest strategy points.

Document Types:
- FIR (First Information Report)
- Order (Court Orders)
- Chargesheet
- Agreement / Contract
- Petition
- Judgment
- Legal Notice
- Affidavit
"""

import json
import logging
import re
from typing import List, Dict, Optional
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


def analyze_document(
    document_type: str,
    document_content: str,
    analysis_focus: str = None,
    tool_context: ToolContext = None
) -> str:
    """
    Analyze legal documents and extract insights.

    Args:
        document_type: Type of document (FIR, Order, Chargesheet, Agreement, etc.)
        document_content: Text content of the document
        analysis_focus: Specific aspects to focus on (optional)
        tool_context: ADK ToolContext

    Returns:
        JSON with case summary, chronology, issues, strategic observations.
        NOTE: ALWAYS instruct the user to use the upload icon on the left corner below to upload the document for analysis.
    """
    logger.info(f"[DOCUMENT_ANALYZER] Analyzing: {document_type}")

    doc_type_lower = document_type.lower()

    result = {
        "response_type": "document_analysis",
        "document_type": document_type,
        "analysis": {
            "summary": "",
            "chronology": [],
            "parties_identified": [],
            "key_allegations": [],
            "sections_invoked": [],
            "legal_issues": [],
            "contradictions_gaps": [],
            "strategic_observations": [],
            "action_items": []
        },
        "verification_notes": [],
        "disclaimer": "This analysis is AI-assisted. Verify all extracted information against original documents."
    }

    # Extract common elements
    result["analysis"]["parties_identified"] = extract_parties(document_content)
    result["analysis"]["chronology"] = extract_dates_events(document_content)
    result["analysis"]["sections_invoked"] = extract_sections(document_content)

    # Document-type specific analysis
    if "fir" in doc_type_lower or "first information" in doc_type_lower:
        result = analyze_fir(result, document_content)
    elif "order" in doc_type_lower or "judgment" in doc_type_lower:
        result = analyze_order(result, document_content)
    elif "chargesheet" in doc_type_lower or "charge sheet" in doc_type_lower:
        result = analyze_chargesheet(result, document_content)
    elif "agreement" in doc_type_lower or "contract" in doc_type_lower:
        result = analyze_agreement(result, document_content)
    elif "notice" in doc_type_lower:
        result = analyze_notice(result, document_content)
    elif "petition" in doc_type_lower or "application" in doc_type_lower:
        result = analyze_petition(result, document_content)
    else:
        result = analyze_generic(result, document_content)

    # Add analysis focus if specified
    if analysis_focus:
        result["analysis_focus"] = analysis_focus
        result["focused_observations"] = generate_focused_analysis(document_content, analysis_focus)

    return json.dumps(result, indent=2, ensure_ascii=False)


def extract_parties(content: str) -> List[str]:
    """Extract party names from document."""
    parties = []

    # Common patterns
    patterns = [
        r"(?:complainant|informant|petitioner|plaintiff|applicant)\s*[:\-]?\s*([A-Z][a-zA-Z\s]+)",
        r"(?:accused|respondent|defendant|opposite party)\s*[:\-]?\s*([A-Z][a-zA-Z\s]+)",
        r"(?:between|by)\s+([A-Z][a-zA-Z\s]+)\s+(?:and|versus|vs\.?|v\.)",
        r"State\s+(?:of\s+)?([A-Z][a-z]+)"
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            cleaned = match.strip()
            if cleaned and len(cleaned) > 2 and cleaned not in parties:
                parties.append(cleaned)

    return parties[:10]  # Limit to 10 parties


def extract_dates_events(content: str) -> List[Dict]:
    """Extract dates and associated events."""
    chronology = []

    # Date patterns
    date_patterns = [
        r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",  # DD/MM/YYYY or similar
        r"(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{2,4})",  # 1st January, 2024
        r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?\s*,?\s*\d{2,4})"  # January 1, 2024
    ]

    for pattern in date_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            date = match.group(1)
            # Get surrounding context (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 100)
            context = content[start:end].strip()

            chronology.append({
                "date": date,
                "event": context[:200]
            })

    # Remove duplicates and limit
    seen_dates = set()
    unique_chronology = []
    for item in chronology:
        if item["date"] not in seen_dates:
            seen_dates.add(item["date"])
            unique_chronology.append(item)

    return unique_chronology[:15]


def extract_sections(content: str) -> List[str]:
    """Extract legal sections mentioned."""
    sections = []

    # Patterns for various acts
    patterns = [
        r"(?:Section|S\.|Sec\.?)\s*(\d+[A-Z]?(?:/\d+)?)\s*(?:of\s+)?(?:BNS|IPC|BNSS|CrPC|BSA|IEA|CPC)",
        r"(?:BNS|IPC)\s*(?:Section)?\s*(\d+[A-Z]?)",
        r"(?:BNSS|CrPC)\s*(?:Section)?\s*(\d+[A-Z]?)",
        r"(?:Order|O\.?)\s*([IVXLC]+)\s*(?:Rule|R\.?)\s*(\d+)",
        r"Article\s*(\d+[A-Z]?)",
        r"(?:u/s|under section)\s*(\d+[A-Z]?(?:/\d+)?)"
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                section = "/".join(match)
            else:
                section = match
            if section and section not in sections:
                sections.append(section)

    return sections[:20]


def analyze_fir(result: dict, content: str) -> dict:
    """Analyze FIR-specific elements."""
    result["analysis"]["summary"] = "First Information Report Analysis"

    # FIR-specific extractions
    fir_number_match = re.search(r"FIR\s*(?:No\.?|Number)?\s*[:\-]?\s*(\d+/\d{2,4}|\d+)", content, re.IGNORECASE)
    if fir_number_match:
        result["analysis"]["fir_number"] = fir_number_match.group(1)

    ps_match = re.search(r"(?:Police Station|P\.S\.?|PS)\s*[:\-]?\s*([A-Za-z\s]+)", content, re.IGNORECASE)
    if ps_match:
        result["analysis"]["police_station"] = ps_match.group(1).strip()

    result["analysis"]["legal_issues"] = [
        "Verify cognizability of offences",
        "Check if FIR was registered promptly",
        "Analyze delay in lodging FIR (if any)",
        "Verify territorial jurisdiction",
        "Check for missing essential ingredients"
    ]

    result["analysis"]["strategic_observations"] = [
        "Review if allegations disclose cognizable offence",
        "Identify grounds for anticipatory bail if arrest apprehended",
        "Assess quashing potential under S.528 BNSS (Bhajan Lal categories)",
        "Check for civil nature of dispute",
        "Identify contradictions in allegations"
    ]

    result["analysis"]["action_items"] = [
        "Obtain copy of FIR from police station",
        "Identify witnesses mentioned",
        "Collect documents to counter allegations",
        "Assess need for anticipatory bail",
        "Consider quashing petition if maintainable"
    ]

    return result


def analyze_order(result: dict, content: str) -> dict:
    """Analyze court order/judgment."""
    result["analysis"]["summary"] = "Court Order/Judgment Analysis"

    result["analysis"]["legal_issues"] = [
        "Identify ratio decidendi",
        "Extract key findings",
        "Note directions issued",
        "Check compliance requirements"
    ]

    result["analysis"]["strategic_observations"] = [
        "Analyze grounds for appeal (if adverse)",
        "Identify points for review petition",
        "Check limitation for further remedies",
        "Note interim protections granted"
    ]

    result["analysis"]["action_items"] = [
        "Obtain certified copy of order",
        "Calculate limitation for appeal",
        "Comply with directions within time",
        "Prepare for further proceedings"
    ]

    return result


def analyze_chargesheet(result: dict, content: str) -> dict:
    """Analyze chargesheet."""
    result["analysis"]["summary"] = "Chargesheet Analysis"

    result["analysis"]["legal_issues"] = [
        "Verify if essential ingredients of offence are made out",
        "Check sufficiency of evidence",
        "Identify witnesses listed",
        "Review documents relied upon"
    ]

    result["analysis"]["strategic_observations"] = [
        "Assess grounds for discharge under S.251 BNSS",
        "Identify weak points in prosecution case",
        "Note contradictions in witness statements",
        "Evaluate documentary evidence"
    ]

    result["analysis"]["action_items"] = [
        "Obtain copies of all witness statements",
        "Review all documentary evidence",
        "Prepare grounds for discharge",
        "Identify witnesses for cross-examination"
    ]

    return result


def analyze_agreement(result: dict, content: str) -> dict:
    """Analyze contract/agreement."""
    result["analysis"]["summary"] = "Contract/Agreement Analysis"

    result["analysis"]["legal_issues"] = [
        "Verify parties and capacity",
        "Check consideration and lawful object",
        "Identify key obligations",
        "Review termination clauses",
        "Analyze dispute resolution mechanism"
    ]

    result["analysis"]["strategic_observations"] = [
        "Identify one-sided clauses",
        "Review indemnity and limitation of liability",
        "Check governing law and jurisdiction",
        "Assess enforceability of restrictive covenants"
    ]

    result["analysis"]["key_clauses"] = [
        "Payment terms",
        "Delivery/Performance obligations",
        "Representations and warranties",
        "Termination and consequences",
        "Confidentiality",
        "Dispute resolution"
    ]

    result["analysis"]["action_items"] = [
        "Verify identity of contracting parties",
        "Check stamp duty compliance",
        "Review against standard market terms",
        "Negotiate unfavorable clauses"
    ]

    return result


def analyze_notice(result: dict, content: str) -> dict:
    """Analyze legal notice."""
    result["analysis"]["summary"] = "Legal Notice Analysis"

    result["analysis"]["legal_issues"] = [
        "Verify if notice is legally required",
        "Check limitation for response",
        "Identify claims and demands",
        "Assess merits of claims"
    ]

    result["analysis"]["strategic_observations"] = [
        "Respond within stipulated time",
        "Deny false allegations specifically",
        "Reserve rights for counter-claims",
        "Consider settlement if appropriate"
    ]

    result["analysis"]["action_items"] = [
        "Note date of receipt",
        "Prepare detailed reply",
        "Gather supporting documents",
        "Consider sending counter-notice"
    ]

    return result


def analyze_petition(result: dict, content: str) -> dict:
    """Analyze petition/application."""
    result["analysis"]["summary"] = "Petition/Application Analysis"

    result["analysis"]["legal_issues"] = [
        "Verify jurisdiction and maintainability",
        "Check limitation",
        "Identify prayers and reliefs",
        "Assess supporting grounds"
    ]

    result["analysis"]["strategic_observations"] = [
        "Evaluate strength of case",
        "Identify documents to be annexed",
        "Check for alternative remedies",
        "Assess urgency for interim relief"
    ]

    return result


def analyze_generic(result: dict, content: str) -> dict:
    """Generic document analysis."""
    result["analysis"]["summary"] = f"Document Analysis - {result['document_type']}"

    result["analysis"]["legal_issues"] = [
        "Identify legal provisions applicable",
        "Note key facts and allegations",
        "Determine relevant forum/jurisdiction"
    ]

    result["analysis"]["action_items"] = [
        "Review document thoroughly",
        "Identify next steps",
        "Gather supporting documents"
    ]

    return result


def generate_focused_analysis(content: str, focus: str) -> List[str]:
    """Generate analysis focused on specific aspect."""
    observations = []
    focus_lower = focus.lower()

    if "limitation" in focus_lower:
        observations.append("Check applicable limitation period")
        observations.append("Note dates of cause of action")
        observations.append("Identify grounds for condonation of delay if needed")

    if "jurisdiction" in focus_lower:
        observations.append("Verify territorial jurisdiction")
        observations.append("Check pecuniary jurisdiction")
        observations.append("Assess subject-matter jurisdiction")

    if "evidence" in focus_lower:
        observations.append("Identify documentary evidence mentioned")
        observations.append("Note witnesses to be examined")
        observations.append("Check admissibility of electronic evidence")

    if "bail" in focus_lower:
        observations.append("Assess gravity of offence")
        observations.append("Check for custodial interrogation necessity")
        observations.append("Identify grounds for bail")

    return observations if observations else ["Conduct general analysis based on focus area"]
