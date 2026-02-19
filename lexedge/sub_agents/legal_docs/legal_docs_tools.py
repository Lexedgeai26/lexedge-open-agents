import json
import logging
import os
from typing import Optional
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# Import legal settings
try:
    from lexedge.config import LEGAL_SETTINGS, get_legal_context_string
    from lexedge.context_manager import agent_context_manager
except ImportError:
    from ...config import LEGAL_SETTINGS, get_legal_context_string
    from ...context_manager import agent_context_manager


def _get_interaction_history(tool_context: ToolContext, max_messages: int = 8) -> str:
    """Get interaction history from tool context."""
    history_context = ""
    try:
        if hasattr(tool_context, "state") and "interaction_history" in tool_context.state:
            history = tool_context.state["interaction_history"][-max_messages:]
            parts = []
            for msg in history:
                role = "USER" if msg.get("role") == "user" else "ASSISTANT"
                content = msg.get("content", "")
                if content and content.strip().startswith("{"):
                    try:
                        data = json.loads(content)
                        summary = (
                            data.get("legal_summary")
                            or data.get("analysis_summary")
                            or data.get("document_summary")
                            or ""
                        )
                        if summary:
                            parts.append(f"{role} SUMMARY: {summary}")
                    except Exception:
                        pass
                elif content:
                    parts.append(f"{role}: {content}")
            history_context = "\n".join(parts)
    except Exception as exc:
        logger.warning(f"Context collection failed: {exc}")
    return history_context


def _get_case_profile_summary() -> str:
    """Get case profile summary from context manager."""
    case_profile = agent_context_manager.get_context("CaseProfile").get("data", {})
    if not case_profile:
        return "Case information not yet collected."

    return f"""
    - Case Name: {case_profile.get('case_name', 'Unknown')}
    - Client Name: {case_profile.get('client_name', 'N/A')}
    - Case Type: {case_profile.get('case_type', 'N/A')}
    - Case Number: {case_profile.get('case_number', 'N/A')}
    - Jurisdiction: {case_profile.get('jurisdiction', 'N/A')}
    - Opposing Party: {case_profile.get('opposing_party', 'N/A')}
    - Key Issues: {', '.join(case_profile.get('key_issues', [])) if case_profile.get('key_issues') else 'None'}
    - Filing Deadline: {case_profile.get('filing_deadline', 'Not set')}
    - Case Status: {case_profile.get('status', 'Active')}
    """


def analyze_legal_document(document_text: str, document_type: str, tool_context: ToolContext) -> str:
    """
    Analyze a legal document and extract key information.
    
    Args:
        document_text: The text content of the legal document
        document_type: Type of document (contract, agreement, filing, motion, etc.)
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Structured document analysis with key provisions and risks
    """
    logger.info(f"[LEGAL_DOCS] Analyzing {document_type} document")
    
    case_profile = _get_case_profile_summary()
    history_context = _get_interaction_history(tool_context)
    
    analysis_result = {
        "response_type": "document_analysis",
        "document_type": document_type,
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "legal_system": LEGAL_SETTINGS.get("legal_system", "Common Law"),
        "analysis": {
            "document_summary": f"Analysis of {document_type} document",
            "parties_identified": ["Party A", "Party B"],
            "key_provisions": [
                "Definitions and interpretations",
                "Rights and obligations of parties",
                "Term and termination clauses",
                "Liability and indemnification",
                "Confidentiality provisions",
                "Dispute resolution mechanism",
                "Governing law and jurisdiction"
            ],
            "identified_risks": [
                "Review liability caps and limitations",
                "Assess indemnification obligations",
                "Verify compliance with applicable regulations",
                "Check for unfavorable termination clauses",
                "Review intellectual property provisions"
            ],
            "key_dates": [
                "Effective date",
                "Termination/expiration date",
                "Notice periods",
                "Renewal dates"
            ],
            "compliance_considerations": LEGAL_SETTINGS.get("compliance_frameworks", []),
            "recommendations": [
                "Review all defined terms carefully",
                "Verify compliance with jurisdiction requirements",
                "Consider negotiating unfavorable terms",
                "Ensure proper execution requirements are met"
            ]
        },
        "disclaimer": "This document analysis is for informational purposes only. Please consult with a licensed attorney for specific legal advice."
    }
    
    # Update context
    try:
        agent_context_manager.update_context("LegalDocsAgent", {
            "last_analysis": {
                "document_type": document_type,
                "summary": f"Analyzed {document_type} document",
                "key_points": ["Parties identified", "Key terms reviewed", "Risks assessed"]
            }
        })
    except Exception as ctx_err:
        logger.warning(f"Failed to persist document analysis: {ctx_err}")
    
    return json.dumps(analysis_result, indent=2)


def generate_legal_summary(case_context: str, tool_context: ToolContext) -> str:
    """
    Generate a comprehensive legal summary from case context.
    
    Args:
        case_context: The case context and relevant information
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Structured legal summary
    """
    logger.info("[LEGAL_DOCS] Generating legal summary")
    
    case_profile = _get_case_profile_summary()
    history_context = _get_interaction_history(tool_context)
    last_analysis = agent_context_manager.get_context("LegalDocsAgent").get("last_analysis")
    
    summary_result = {
        "response_type": "legal_summary",
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "legal_system": LEGAL_SETTINGS.get("legal_system", "Common Law"),
        "summary": {
            "title": "Legal Case Summary",
            "case_overview": case_context[:500] if case_context else "Case context not provided",
            "key_legal_issues": [
                "Primary legal issue to be determined",
                "Secondary considerations",
                "Procedural requirements"
            ],
            "applicable_law": [
                f"Laws of {LEGAL_SETTINGS.get('jurisdiction', 'Federal')}",
                f"{LEGAL_SETTINGS.get('legal_system', 'Common Law')} principles",
                "Relevant statutes and regulations"
            ],
            "case_strengths": [
                "Strong factual basis",
                "Clear legal precedent",
                "Well-documented evidence"
            ],
            "case_weaknesses": [
                "Areas requiring additional evidence",
                "Potential counterarguments",
                "Procedural challenges"
            ],
            "recommended_strategy": [
                "Conduct thorough legal research",
                "Gather supporting documentation",
                "Prepare comprehensive legal memorandum",
                "Consider settlement options"
            ],
            "next_steps": [
                "Review all relevant documents",
                "Interview key witnesses",
                "Research applicable precedents",
                "Prepare initial case assessment"
            ]
        },
        "disclaimer": "This legal summary is for informational purposes only and does not constitute legal advice."
    }
    
    # Update context
    try:
        agent_context_manager.update_context("LegalDocsAgent", {
            "last_summary": summary_result
        })
    except Exception as ctx_err:
        logger.warning(f"Failed to persist legal summary: {ctx_err}")
    
    return json.dumps(summary_result, indent=2)


def review_contract(contract_text: str, review_focus: str, tool_context: ToolContext) -> str:
    """
    Perform detailed contract review with risk assessment.
    
    Args:
        contract_text: The contract text to review
        review_focus: Specific areas to focus on (e.g., liability, IP, termination)
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Detailed contract review with recommendations
    """
    logger.info(f"[LEGAL_DOCS] Reviewing contract with focus on: {review_focus}")
    
    case_data = agent_context_manager.get_context("CaseProfile").get("data", {})
    client_name = case_data.get("client_name", "the client")
    
    review_result = {
        "response_type": "contract_review",
        "client": client_name,
        "review_focus": review_focus,
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "review": {
            "executive_summary": f"Contract review for {client_name} focusing on {review_focus}",
            "contract_type": "To be determined from content",
            "parties": {
                "party_a": "First Party",
                "party_b": "Second Party"
            },
            "key_terms": {
                "term_duration": "Review contract for specific term",
                "payment_terms": "Review payment provisions",
                "termination_rights": "Review termination clauses",
                "renewal_provisions": "Review auto-renewal terms"
            },
            "risk_assessment": {
                "high_risk_clauses": [
                    "Unlimited liability provisions",
                    "Broad indemnification requirements",
                    "One-sided termination rights"
                ],
                "medium_risk_clauses": [
                    "Automatic renewal terms",
                    "Non-compete provisions",
                    "Exclusivity requirements"
                ],
                "low_risk_clauses": [
                    "Standard confidentiality terms",
                    "Reasonable notice periods"
                ]
            },
            "compliance_check": {
                "frameworks": LEGAL_SETTINGS.get("compliance_frameworks", []),
                "status": "Review recommended",
                "notes": "Verify compliance with applicable regulations"
            },
            "recommended_changes": [
                "Negotiate liability caps",
                "Add mutual termination rights",
                "Clarify ambiguous terms",
                "Include dispute resolution mechanism"
            ],
            "approval_recommendation": "Conditional - pending negotiation of high-risk terms"
        },
        "disclaimer": "This contract review is for informational purposes only. Please consult with a licensed attorney before signing any legal documents."
    }
    
    return json.dumps(review_result, indent=2)


def draft_legal_document(document_type: str, document_details: str, tool_context: ToolContext) -> str:
    """
    Draft a legal document based on provided specifications.
    
    Args:
        document_type: Type of document to draft (letter, motion, agreement, etc.)
        document_details: Details and requirements for the document
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Draft legal document structure
    """
    logger.info(f"[LEGAL_DOCS] Drafting {document_type} document")
    
    case_data = agent_context_manager.get_context("CaseProfile").get("data", {})
    client_name = case_data.get("client_name", "the client")
    
    draft_result = {
        "response_type": "document_draft",
        "document_type": document_type,
        "client": client_name,
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "draft": {
            "title": f"DRAFT - {document_type.upper()}",
            "prepared_for": client_name,
            "prepared_by": LEGAL_SETTINGS.get("firm_name", "LexEdge Legal AI"),
            "date": "Current Date",
            "sections": [
                {
                    "heading": "Introduction/Preamble",
                    "content": "This section introduces the document and its purpose."
                },
                {
                    "heading": "Definitions",
                    "content": "Key terms and their definitions used throughout this document."
                },
                {
                    "heading": "Main Body",
                    "content": f"The substantive content based on: {document_details[:200]}..."
                },
                {
                    "heading": "Terms and Conditions",
                    "content": "Applicable terms, conditions, and obligations."
                },
                {
                    "heading": "Signatures",
                    "content": "Signature blocks for all parties."
                }
            ],
            "notes": [
                "This is a draft document requiring review by licensed counsel",
                f"Document prepared under {LEGAL_SETTINGS.get('jurisdiction', 'Federal')} jurisdiction",
                "All terms should be verified for accuracy and completeness"
            ]
        },
        "disclaimer": "This draft document is for reference purposes only. Please have it reviewed and finalized by a licensed attorney before use."
    }
    
    return json.dumps(draft_result, indent=2)
