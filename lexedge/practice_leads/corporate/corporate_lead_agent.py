"""
Corporate & Commercial Lead Agent

Specialized agent for corporate and commercial matters in India.

Scope:
- Contracts: NDA, MSA, SHA, SPA, SSA
- Employment Agreements
- Loan Agreements
- Lease/License Agreements
- Board Resolutions
- Companies Act, 2013 Compliance
- NCLT Matters (oppression, mismanagement)
"""

from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext

try:
    from lexedge.config import LlmModel
except ImportError:
    from ...config import LlmModel

from lexedge.prompts.agent_prompts import get_corporate_lead_prompt
from lexedge.shared_tools import (
    map_statute_sections,
    research_case_law,
    verify_citation,
    analyze_document,
    validate_output
)


def corporate_instruction_provider(context: ReadonlyContext) -> str:
    """Dynamic instruction provider for corporate lead agent."""
    return get_corporate_lead_prompt()


# Corporate-specific tools



def review_contract(contract_text: str, review_perspective: str = "balanced") -> str:
    """
    Review a contract and identify key issues and risks.

    Args:
        contract_text: Text of the contract to review
        review_perspective: "buyer", "seller", "balanced"

    Returns:
        JSON with contract review analysis
    """
    import json
    import re

    result = {
        "response_type": "contract_review",
        "perspective": review_perspective,
        "key_clauses_identified": [],
        "risk_areas": [],
        "missing_clauses": [],
        "recommendations": [],
        "negotiation_points": []
    }

    contract_lower = contract_text.lower()

    # Identify key clauses
    clause_checks = {
        "term_termination": any(word in contract_lower for word in ["term", "termination", "expiry", "renewal"]),
        "payment": any(word in contract_lower for word in ["payment", "consideration", "price", "fee"]),
        "confidentiality": any(word in contract_lower for word in ["confidential", "non-disclosure", "proprietary"]),
        "indemnity": any(word in contract_lower for word in ["indemnify", "indemnification", "hold harmless"]),
        "limitation_of_liability": any(word in contract_lower for word in ["limitation of liability", "liability cap", "consequential"]),
        "ip_rights": any(word in contract_lower for word in ["intellectual property", "ip rights", "license", "ownership"]),
        "warranties": any(word in contract_lower for word in ["warranty", "represent", "guarantee"]),
        "dispute_resolution": any(word in contract_lower for word in ["arbitration", "jurisdiction", "dispute", "governing law"]),
        "force_majeure": any(word in contract_lower for word in ["force majeure", "act of god", "unforeseeable"]),
        "assignment": any(word in contract_lower for word in ["assignment", "transfer", "successor"])
    }

    for clause, present in clause_checks.items():
        if present:
            result["key_clauses_identified"].append(clause.replace("_", " ").title())
        else:
            result["missing_clauses"].append(clause.replace("_", " ").title())

    # Risk analysis
    if "unlimited liability" in contract_lower or "no limitation" in contract_lower:
        result["risk_areas"].append({
            "area": "Unlimited Liability",
            "severity": "HIGH",
            "recommendation": "Negotiate a liability cap (typically contract value or 12-month fees)"
        })

    if "indemnify" in contract_lower and "all claims" in contract_lower:
        result["risk_areas"].append({
            "area": "Broad Indemnification",
            "severity": "HIGH",
            "recommendation": "Limit indemnification to third-party IP claims and gross negligence"
        })

    if "exclusive jurisdiction" not in contract_lower and "arbitration" not in contract_lower:
        result["risk_areas"].append({
            "area": "Unclear Dispute Resolution",
            "severity": "MEDIUM",
            "recommendation": "Add clear dispute resolution mechanism (arbitration recommended)"
        })

    if "automatic renewal" in contract_lower:
        result["risk_areas"].append({
            "area": "Auto-Renewal",
            "severity": "MEDIUM",
            "recommendation": "Ensure adequate notice period for non-renewal"
        })

    # Recommendations based on perspective
    if review_perspective == "buyer":
        result["negotiation_points"] = [
            "Seek broader warranties from seller",
            "Limit liability for indirect/consequential damages",
            "Ensure clear acceptance criteria",
            "Add audit rights if applicable",
            "Include SLA with penalties"
        ]
    elif review_perspective == "seller":
        result["negotiation_points"] = [
            "Limit warranty scope and duration",
            "Cap liability to contract value",
            "Exclude consequential damages",
            "Ensure clear payment terms",
            "Add termination for convenience with notice"
        ]
    else:
        result["negotiation_points"] = [
            "Balance indemnification obligations",
            "Mutual limitation of liability",
            "Clear termination rights for both parties",
            "Balanced IP ownership",
            "Mutual confidentiality obligations"
        ]

    result["summary"] = f"Identified {len(result['key_clauses_identified'])} key clauses, {len(result['risk_areas'])} risk areas, and {len(result['missing_clauses'])} missing clauses."

    return json.dumps(result, indent=2, ensure_ascii=False)





CorporateCommercialLeadAgent = LlmAgent(
    name="CorporateCommercialLeadAgent",
    model=LlmModel,
    description=(
        "Corporate & Commercial Lead Agent for India. Handles contracts (NDA, MSA, SHA, SPA), "
        "corporate governance, board resolutions, Companies Act compliance, and NCLT matters. "
        "Provides contract review with risk analysis and negotiation points."
    ),
    instruction=corporate_instruction_provider,
    tools=[
        # Corporate-specific tools
        review_contract,
        # Shared tools
        map_statute_sections,
        research_case_law,
        verify_citation,
        analyze_document,
        validate_output
    ]
)
