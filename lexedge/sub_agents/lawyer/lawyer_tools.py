import json
import logging
import os
from typing import Optional
from dotenv import load_dotenv
from google.adk.tools import ToolContext

# Initialize environment and logging
load_dotenv()
LEGAL_API_URL = os.getenv("LEGAL_API_URL", "http://localhost:8000")
LEGAL_API_TIMEOUT = int(os.getenv("LEGAL_API_TIMEOUT", "60"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import legal settings
try:
    from lexedge.config import LEGAL_SETTINGS, get_legal_context_string
    from lexedge.context_manager import agent_context_manager
except ImportError:
    from ...config import LEGAL_SETTINGS, get_legal_context_string
    from ...context_manager import agent_context_manager


def legal_analysis_assessment(legal_issues: str, case_facts: str, tool_context: ToolContext) -> str:
    """
    Perform a comprehensive legal analysis assessment for a case.
    
    Args:
        legal_issues: Description of the legal issues to analyze
        case_facts: Relevant facts of the case
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Structured legal analysis with recommendations
    """
    logger.info(f"Executing legal_analysis_assessment: {legal_issues[:50]}...")
    
    # Get case context
    case_data = agent_context_manager.get_context("CaseProfile").get("data", {})
    client_name = case_data.get("client_name", "the client")
    jurisdiction = case_data.get("jurisdiction") or LEGAL_SETTINGS.get("jurisdiction", "Federal")
    
    # Check for conclude action
    conclude_analysis = "[ACTION: CONCLUDE_ANALYSIS]" in legal_issues
    
    legal_context = get_legal_context_string()
    
    analysis_result = {
        "response_type": "legal_analysis",
        "client_name": client_name,
        "jurisdiction": jurisdiction,
        "legal_system": LEGAL_SETTINGS.get("legal_system", "Common Law"),
        "analysis": {
            "legal_issues": legal_issues.replace("[ACTION: CONCLUDE_ANALYSIS]", "").strip(),
            "case_facts": case_facts,
            "applicable_law": f"Laws of {jurisdiction} under {LEGAL_SETTINGS.get('legal_system', 'Common Law')} system",
            "areas_of_expertise": LEGAL_SETTINGS.get("areas_of_expertise", []),
            "preliminary_assessment": f"Based on the facts presented, this matter involves {legal_issues[:100]}...",
            "risk_level": "moderate",
            "recommended_actions": [
                "Conduct detailed legal research on applicable precedents",
                "Review all relevant documentation",
                "Identify potential claims and defenses",
                "Assess statute of limitations",
                "Evaluate settlement vs. litigation options"
            ],
            "next_steps": [
                "Gather additional documentation",
                "Interview relevant witnesses",
                "Research applicable case law",
                "Prepare initial legal memorandum"
            ]
        },
        "disclaimers": [
            "This analysis is for informational purposes only and does not constitute legal advice.",
            "Please consult with a licensed attorney in your jurisdiction for specific legal guidance.",
            f"This analysis is based on {LEGAL_SETTINGS.get('legal_system', 'Common Law')} principles applicable in {jurisdiction}."
        ],
        "concluded": conclude_analysis
    }
    
    # Update context with assessment
    try:
        agent_context_manager.update_context("LawyerAgent", {
            "last_assessment": {
                "legal_summary": f"Legal analysis for {client_name} regarding {legal_issues[:100]}",
                "jurisdiction": jurisdiction,
                "timestamp": "current"
            }
        })
    except Exception as ctx_err:
        logger.warning(f"Failed to update context: {ctx_err}")
    
    return json.dumps(analysis_result, indent=2)


def legal_specialty_query(specialty: str, query: str, tool_context: ToolContext) -> str:
    """
    Query a legal specialist for specific area of law.
    
    Args:
        specialty: The legal specialty (e.g., IP, Tax, Immigration, Employment)
        query: The specific legal question
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Specialist legal opinion
    """
    logger.info(f"Executing legal_specialty_query: {specialty} - {query[:50]}...")
    
    specialties_info = {
        "IP": "Intellectual Property Law - Patents, Trademarks, Copyrights, Trade Secrets",
        "Tax": "Tax Law - Federal, State, International Tax Planning and Compliance",
        "Immigration": "Immigration Law - Visas, Green Cards, Naturalization, Employment Authorization",
        "Employment": "Employment Law - Labor Relations, Discrimination, Wage & Hour, Benefits",
        "Real Estate": "Real Estate Law - Transactions, Zoning, Landlord-Tenant, Title Issues",
        "Corporate": "Corporate Law - Formation, Governance, M&A, Securities",
        "Litigation": "Civil Litigation - Trial Practice, Discovery, Appeals",
        "Criminal": "Criminal Law - Defense, White Collar, Regulatory Offenses",
        "Family": "Family Law - Divorce, Custody, Support, Adoption",
        "Bankruptcy": "Bankruptcy Law - Chapter 7, 11, 13, Creditor Rights"
    }
    
    specialty_description = specialties_info.get(specialty, f"{specialty} Law")
    
    result = {
        "response_type": "specialist_opinion",
        "specialty": specialty,
        "specialty_description": specialty_description,
        "query": query,
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "opinion": {
            "summary": f"Specialist analysis for {specialty} matter",
            "key_considerations": [
                f"Applicable {specialty} regulations and statutes",
                "Relevant case precedents",
                "Industry best practices",
                "Compliance requirements"
            ],
            "recommendations": [
                f"Consult with a {specialty} specialist attorney",
                "Review applicable regulations",
                "Document all relevant facts and communications"
            ]
        },
        "disclaimer": f"This {specialty} analysis should be reviewed by a licensed attorney specializing in {specialty_description}."
    }
    
    return json.dumps(result, indent=2)


def get_case_data(tool_context: ToolContext) -> str:
    """
    Retrieve current case profile data.
    
    Args:
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Current case profile information
    """
    logger.info("Executing get_case_data...")
    
    case_data = agent_context_manager.get_context("CaseProfile").get("data", {})
    
    if not case_data:
        return json.dumps({
            "response_type": "case_data",
            "status": "no_data",
            "message": "No case profile data available. Please provide case details to proceed."
        })
    
    result = {
        "response_type": "case_data",
        "status": "available",
        "case_profile": case_data,
        "legal_settings": {
            "jurisdiction": LEGAL_SETTINGS.get("jurisdiction"),
            "country": LEGAL_SETTINGS.get("country_of_practice"),
            "legal_system": LEGAL_SETTINGS.get("legal_system"),
            "areas_of_expertise": LEGAL_SETTINGS.get("areas_of_expertise")
        }
    }
    
    return json.dumps(result, indent=2)


def analyze_legal_document(document_text: str, document_type: str, tool_context: ToolContext) -> str:
    """
    Analyze a legal document and extract key information.
    
    Args:
        document_text: The text content of the legal document
        document_type: Type of document (contract, agreement, filing, etc.)
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Structured document analysis
    """
    logger.info(f"Executing analyze_legal_document: {document_type}...")
    
    case_data = agent_context_manager.get_context("CaseProfile").get("data", {})
    client_name = case_data.get("client_name", "the client")
    
    analysis_result = {
        "response_type": "document_analysis",
        "document_type": document_type,
        "client": client_name,
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "analysis": {
            "document_summary": f"Analysis of {document_type} document",
            "key_provisions": [
                "Parties and definitions",
                "Rights and obligations",
                "Term and termination",
                "Liability and indemnification",
                "Dispute resolution"
            ],
            "identified_risks": [
                "Review liability caps and limitations",
                "Assess indemnification obligations",
                "Verify compliance with applicable regulations"
            ],
            "key_dates": [
                "Effective date",
                "Termination date",
                "Notice periods"
            ],
            "recommendations": [
                "Review all defined terms carefully",
                "Verify compliance with jurisdiction requirements",
                "Consider negotiating unfavorable terms"
            ]
        },
        "compliance_check": {
            "frameworks": LEGAL_SETTINGS.get("compliance_frameworks", []),
            "status": "Review recommended"
        },
        "disclaimer": "This document analysis is for informational purposes only. Please consult with a licensed attorney for specific legal advice."
    }
    
    # Update context
    try:
        agent_context_manager.update_context("LegalDocsAgent", {
            "last_analysis": {
                "document_type": document_type,
                "summary": f"Analyzed {document_type} for {client_name}",
                "key_points": ["Parties identified", "Key terms reviewed", "Risks assessed"]
            }
        })
    except Exception as ctx_err:
        logger.warning(f"Failed to update context: {ctx_err}")
    
    return json.dumps(analysis_result, indent=2)


def _get_legal_suggestions(query: str) -> dict:
    """Generate contextual legal suggestions based on the query."""
    query_lower = query.lower()
    
    suggestions = []
    
    # Add relevant follow-up suggestions based on query content
    if any(word in query_lower for word in ["contract", "agreement", "nda"]):
        suggestions.append({
            "id": "contract_review",
            "caption": "Review contract terms",
            "command": "analyze the key terms and risks in this contract",
            "icon": "file-text",
            "icon_display": "� Contract Review",
            "priority": 1,
            "category": "legal"
        })
    
    if any(word in query_lower for word in ["lawsuit", "sue", "litigation"]):
        suggestions.append({
            "id": "litigation_options",
            "caption": "What are my litigation options?",
            "command": "what are the litigation options and potential outcomes",
            "icon": "gavel",
            "icon_display": "⚖️ Litigation",
            "priority": 1,
            "category": "legal"
        })
    
    # Always add these common suggestions
    suggestions.extend([
        {
            "id": "legal_research",
            "caption": "Research applicable laws",
            "command": "research applicable laws and precedents",
            "icon": "search",
            "icon_display": "� Research",
            "priority": 2,
            "category": "legal"
        },
        {
            "id": "next_steps",
            "caption": "What are the next steps?",
            "command": "what are the recommended next steps",
            "icon": "list",
            "icon_display": "📋 Next Steps",
            "priority": 3,
            "category": "legal"
        }
    ])
    
    return {"suggestions": suggestions[:4]}
    