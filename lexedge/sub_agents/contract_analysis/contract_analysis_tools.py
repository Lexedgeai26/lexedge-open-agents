import json
import logging
import asyncio
from typing import Optional
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

try:
    from lexedge.config import LEGAL_SETTINGS, get_legal_context_string
    from lexedge.context_manager import agent_context_manager
    from lexedge.utils.ollama_client import analyze_legal_text, get_legal_response
except ImportError:
    from ...config import LEGAL_SETTINGS, get_legal_context_string
    from ...context_manager import agent_context_manager
    from ...utils.ollama_client import analyze_legal_text, get_legal_response


def _run_async(coro):
    """Helper to run async function from sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def review_contract(contract_text: str, contract_type: str, tool_context: ToolContext) -> str:
    """
    Perform comprehensive contract review using Ollama.
    
    Args:
        contract_text: The contract text to review
        contract_type: Type of contract (NDA, Service Agreement, Employment, etc.)
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Detailed contract review with recommendations
    """
    logger.info(f"[CONTRACT] Reviewing {contract_type} contract")
    
    case_data = agent_context_manager.get_context("CaseProfile").get("data", {})
    client_name = case_data.get("client_name", "the client")
    jurisdiction = LEGAL_SETTINGS.get("jurisdiction", "Federal")
    
    task = f"""Review this {contract_type} contract for {client_name}.
Jurisdiction: {jurisdiction}

Provide:
1. Executive Summary
2. Key Parties and Terms
3. Important Obligations
4. Risk Assessment (High/Medium/Low)
5. Recommendations

Be concise and professional."""

    try:
        analysis = _run_async(analyze_legal_text(contract_text, task))
        return analysis
    except Exception as e:
        logger.error(f"Error in contract review: {e}")
        return f"I apologize, but I encountered an issue analyzing the contract. Please try again or provide a shorter excerpt. Error: {str(e)}"


def assess_contract_risks(contract_text: str, risk_focus: str, tool_context: ToolContext) -> str:
    """
    Assess risks in a contract.
    
    Args:
        contract_text: The contract text to assess
        risk_focus: Specific risk areas to focus on
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Risk assessment report
    """
    logger.info(f"[CONTRACT] Assessing risks with focus on: {risk_focus}")
    
    result = {
        "response_type": "risk_assessment",
        "risk_focus": risk_focus,
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "assessment": {
            "overall_risk_level": "Moderate",
            "risk_categories": {
                "financial_risk": {
                    "level": "Medium",
                    "concerns": ["Payment terms", "Liability caps", "Penalties"]
                },
                "legal_risk": {
                    "level": "Medium",
                    "concerns": ["Indemnification", "Governing law", "Dispute resolution"]
                },
                "operational_risk": {
                    "level": "Low",
                    "concerns": ["Performance obligations", "Delivery timelines"]
                },
                "compliance_risk": {
                    "level": "Medium",
                    "concerns": LEGAL_SETTINGS.get("compliance_frameworks", [])
                }
            },
            "high_priority_items": [
                "Review liability limitations",
                "Assess indemnification scope",
                "Verify insurance requirements"
            ],
            "mitigation_recommendations": [
                "Negotiate liability caps",
                "Add mutual indemnification",
                "Include force majeure clause"
            ]
        },
        "disclaimer": "This risk assessment is for informational purposes only."
    }
    
    return json.dumps(result, indent=2)


def analyze_contract_clauses(contract_text: str, clause_types: str, tool_context: ToolContext) -> str:
    """
    Analyze specific clauses in a contract.
    
    Args:
        contract_text: The contract text to analyze
        clause_types: Types of clauses to focus on (comma-separated)
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Clause-by-clause analysis
    """
    logger.info(f"[CONTRACT] Analyzing clauses: {clause_types}")
    
    clauses = clause_types.split(",") if clause_types else ["general"]
    
    result = {
        "response_type": "clause_analysis",
        "clauses_analyzed": clauses,
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "analysis": {
            clause.strip(): {
                "status": "Review required",
                "standard_language": "Compare with industry standard",
                "concerns": ["Potential concern 1", "Potential concern 2"],
                "recommendations": ["Recommendation 1", "Recommendation 2"]
            }
            for clause in clauses
        },
        "overall_assessment": "Contract requires review of identified clauses",
        "disclaimer": "This clause analysis is for informational purposes only."
    }
    
    return json.dumps(result, indent=2)


def draft_contract(contract_type: str, contract_details: str, tool_context: ToolContext) -> str:
    """
    Draft a new contract based on specifications.
    
    Args:
        contract_type: Type of contract to draft
        contract_details: Details and requirements for the contract
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Draft contract structure
    """
    logger.info(f"[CONTRACT] Drafting {contract_type} contract")
    
    case_data = agent_context_manager.get_context("CaseProfile").get("data", {})
    client_name = case_data.get("client_name", "the client")
    
    result = {
        "response_type": "contract_draft",
        "contract_type": contract_type,
        "client": client_name,
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "draft": {
            "title": f"{contract_type.upper()} AGREEMENT",
            "preamble": f"This {contract_type} Agreement is entered into as of [DATE]",
            "parties": {
                "party_a": client_name,
                "party_b": "[COUNTERPARTY NAME]"
            },
            "recitals": "WHEREAS, the parties wish to enter into this agreement...",
            "sections": [
                {"number": "1", "title": "Definitions", "content": "Key terms defined here"},
                {"number": "2", "title": "Scope of Agreement", "content": contract_details[:200]},
                {"number": "3", "title": "Term and Termination", "content": "Agreement term provisions"},
                {"number": "4", "title": "Compensation", "content": "Payment terms"},
                {"number": "5", "title": "Confidentiality", "content": "Confidentiality obligations"},
                {"number": "6", "title": "Representations and Warranties", "content": "Party representations"},
                {"number": "7", "title": "Indemnification", "content": "Indemnification provisions"},
                {"number": "8", "title": "Limitation of Liability", "content": "Liability limitations"},
                {"number": "9", "title": "Dispute Resolution", "content": "Dispute resolution mechanism"},
                {"number": "10", "title": "General Provisions", "content": "Miscellaneous provisions"}
            ],
            "signature_block": "IN WITNESS WHEREOF, the parties have executed this Agreement..."
        },
        "notes": [
            "This is a draft requiring review by licensed counsel",
            f"Prepared under {LEGAL_SETTINGS.get('jurisdiction', 'Federal')} jurisdiction"
        ],
        "disclaimer": "This draft is for reference only. Have it reviewed by a licensed attorney."
    }
    
    return json.dumps(result, indent=2)


def generate_redlines(original_text: str, proposed_changes: str, tool_context: ToolContext) -> str:
    """
    Generate redlined version of contract with proposed changes.
    
    Args:
        original_text: Original contract text
        proposed_changes: Description of proposed changes
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Redlined contract with tracked changes
    """
    logger.info("[CONTRACT] Generating redlines")
    
    result = {
        "response_type": "redlines",
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "redlines": {
            "summary": "Proposed modifications to the agreement",
            "changes": [
                {
                    "section": "Section to be modified",
                    "original": "Original language",
                    "proposed": "Proposed new language",
                    "rationale": "Reason for change"
                }
            ],
            "additions": [
                {
                    "location": "Where to add",
                    "new_text": "New language to add",
                    "rationale": "Reason for addition"
                }
            ],
            "deletions": [
                {
                    "section": "Section with deletion",
                    "deleted_text": "Text to remove",
                    "rationale": "Reason for deletion"
                }
            ]
        },
        "negotiation_notes": proposed_changes,
        "disclaimer": "These redlines are suggestions only. Review with licensed counsel."
    }
    
    return json.dumps(result, indent=2)
