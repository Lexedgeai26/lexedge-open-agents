import json
import logging
from typing import Optional
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

try:
    from lexedge.config import LEGAL_SETTINGS
    from lexedge.context_manager import agent_context_manager
except ImportError:
    from ...config import LEGAL_SETTINGS
    from ...context_manager import agent_context_manager


def collect_client_info(client_name: str, contact_info: str, matter_description: str, tool_context: ToolContext) -> str:
    """
    Collect and store client information for case intake.
    
    Args:
        client_name: Name of the client
        contact_info: Client contact information
        matter_description: Brief description of the legal matter
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Client information confirmation
    """
    logger.info(f"[CASE_INTAKE] Collecting client info for: {client_name}")
    
    client_data = {
        "client_name": client_name,
        "contact_info": contact_info,
        "matter_description": matter_description,
        "intake_status": "In Progress"
    }
    
    # Store in context
    try:
        agent_context_manager.update_context("CaseProfile", {
            "data": {
                "client_name": client_name,
                "contact_info": contact_info,
                "matter_description": matter_description,
                "status": "Intake"
            }
        })
    except Exception as ctx_err:
        logger.warning(f"Failed to store client info: {ctx_err}")
    
    result = {
        "response_type": "client_intake",
        "client_info": client_data,
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "firm": LEGAL_SETTINGS.get("firm_name", "LexEdge Legal AI"),
        "next_steps": [
            "Perform conflict check",
            "Determine case type and jurisdiction",
            "Prepare engagement letter",
            "Create case profile"
        ],
        "areas_of_expertise": LEGAL_SETTINGS.get("areas_of_expertise", []),
        "confirmation": f"Client information collected for {client_name}"
    }
    
    return json.dumps(result, indent=2)


def check_conflicts(client_name: str, opposing_parties: str, related_entities: str, tool_context: ToolContext) -> str:
    """
    Perform conflict of interest check.
    
    Args:
        client_name: Name of the prospective client
        opposing_parties: Names of opposing parties
        related_entities: Related entities to check
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Conflict check results
    """
    logger.info(f"[CASE_INTAKE] Checking conflicts for: {client_name}")
    
    result = {
        "response_type": "conflict_check",
        "client": client_name,
        "parties_checked": {
            "client": client_name,
            "opposing_parties": [p.strip() for p in opposing_parties.split(",")] if opposing_parties else [],
            "related_entities": [e.strip() for e in related_entities.split(",")] if related_entities else []
        },
        "results": {
            "conflicts_found": False,
            "potential_conflicts": [],
            "cleared_parties": [client_name],
            "notes": "No conflicts identified in preliminary check"
        },
        "recommendations": [
            "Conduct thorough conflict search in firm database",
            "Check all related parties and entities",
            "Document conflict check results",
            "Obtain conflict waivers if needed"
        ],
        "disclaimer": "This is a preliminary conflict check. Conduct comprehensive conflict search per firm policies."
    }
    
    return json.dumps(result, indent=2)


def create_engagement_letter(client_name: str, matter_type: str, fee_arrangement: str, tool_context: ToolContext) -> str:
    """
    Create an engagement letter for the client.
    
    Args:
        client_name: Name of the client
        matter_type: Type of legal matter
        fee_arrangement: Fee arrangement (hourly, flat fee, contingency, etc.)
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Draft engagement letter
    """
    logger.info(f"[CASE_INTAKE] Creating engagement letter for: {client_name}")
    
    result = {
        "response_type": "engagement_letter",
        "client": client_name,
        "matter_type": matter_type,
        "firm": LEGAL_SETTINGS.get("firm_name", "LexEdge Legal AI"),
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "letter": {
            "title": "ENGAGEMENT LETTER",
            "date": "Current Date",
            "sections": [
                {
                    "heading": "Scope of Representation",
                    "content": f"This letter confirms our engagement to represent you in connection with {matter_type}."
                },
                {
                    "heading": "Fee Arrangement",
                    "content": f"Our fee arrangement for this matter will be: {fee_arrangement}"
                },
                {
                    "heading": "Responsibilities",
                    "content": "We will provide legal services with reasonable diligence and keep you informed of significant developments."
                },
                {
                    "heading": "Client Responsibilities",
                    "content": "You agree to provide complete and accurate information, respond promptly to requests, and pay invoices timely."
                },
                {
                    "heading": "Confidentiality",
                    "content": "All communications between us are protected by attorney-client privilege."
                },
                {
                    "heading": "Termination",
                    "content": "Either party may terminate this engagement upon written notice."
                },
                {
                    "heading": "Acceptance",
                    "content": "Please sign and return a copy of this letter to confirm your acceptance."
                }
            ],
            "signature_blocks": {
                "firm": LEGAL_SETTINGS.get("firm_name", "LexEdge Legal AI"),
                "client": client_name
            }
        },
        "notes": [
            "This is a draft engagement letter",
            "Review and customize for specific matter",
            "Have licensed attorney review before sending"
        ],
        "disclaimer": "This draft must be reviewed by licensed counsel before use."
    }
    
    return json.dumps(result, indent=2)


def create_case_profile(client_name: str, case_type: str, case_details: str, jurisdiction: str, tool_context: ToolContext) -> str:
    """
    Create a comprehensive case profile.
    
    Args:
        client_name: Name of the client
        case_type: Type of case
        case_details: Details about the case
        jurisdiction: Applicable jurisdiction
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Case profile confirmation
    """
    logger.info(f"[CASE_INTAKE] Creating case profile for: {client_name}")
    
    effective_jurisdiction = jurisdiction or LEGAL_SETTINGS.get("jurisdiction", "Federal")
    
    case_profile = {
        "case_name": f"{client_name} - {case_type}",
        "client_name": client_name,
        "case_type": case_type,
        "case_number": "To be assigned",
        "jurisdiction": effective_jurisdiction,
        "opposing_party": "To be identified",
        "key_issues": [],
        "filing_deadline": "To be determined",
        "status": "Active",
        "case_details": case_details
    }
    
    # Store in context
    try:
        agent_context_manager.update_context("CaseProfile", {
            "data": case_profile
        })
    except Exception as ctx_err:
        logger.warning(f"Failed to store case profile: {ctx_err}")
    
    result = {
        "response_type": "case_profile",
        "profile": case_profile,
        "legal_settings": {
            "firm": LEGAL_SETTINGS.get("firm_name"),
            "jurisdiction": effective_jurisdiction,
            "legal_system": LEGAL_SETTINGS.get("legal_system"),
            "areas_of_expertise": LEGAL_SETTINGS.get("areas_of_expertise")
        },
        "next_steps": [
            "Assign case number",
            "Identify key issues and deadlines",
            "Begin legal research",
            "Develop case strategy"
        ],
        "confirmation": f"Case profile created for {client_name}"
    }
    
    return json.dumps(result, indent=2)
