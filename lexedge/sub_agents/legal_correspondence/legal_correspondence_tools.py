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


def draft_client_letter(recipient: str, subject: str, content: str, tool_context: ToolContext) -> str:
    """
    Draft a professional client letter.
    
    Args:
        recipient: Name of the recipient
        subject: Subject of the letter
        content: Main content/message of the letter
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Draft client letter
    """
    logger.info(f"[CORRESPONDENCE] Drafting client letter to: {recipient}")
    
    case_data = agent_context_manager.get_context("CaseProfile").get("data", {})
    
    result = {
        "response_type": "client_letter",
        "letter": {
            "header": {
                "firm_name": LEGAL_SETTINGS.get("firm_name", "LexEdge Legal AI"),
                "date": "Current Date",
                "recipient": recipient,
                "re": subject
            },
            "salutation": f"Dear {recipient},",
            "body": content,
            "closing": {
                "regards": "Very truly yours,",
                "firm": LEGAL_SETTINGS.get("firm_name", "LexEdge Legal AI"),
                "signature_line": "[Attorney Name]"
            },
            "footer": {
                "confidentiality_notice": "CONFIDENTIAL: This letter and any attachments are intended only for the addressee and may contain privileged or confidential information.",
                "disclaimer": "This communication is from a law firm and may be privileged and confidential."
            }
        },
        "case_reference": case_data.get("case_name", "N/A"),
        "notes": ["Review before sending", "Customize as needed"],
        "disclaimer": "This draft must be reviewed by licensed counsel before sending."
    }
    
    return json.dumps(result, indent=2)


def draft_legal_notice(notice_type: str, recipient: str, notice_content: str, tool_context: ToolContext) -> str:
    """
    Draft a formal legal notice.
    
    Args:
        notice_type: Type of legal notice
        recipient: Recipient of the notice
        notice_content: Content of the notice
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Draft legal notice
    """
    logger.info(f"[CORRESPONDENCE] Drafting {notice_type} notice to: {recipient}")
    
    case_data = agent_context_manager.get_context("CaseProfile").get("data", {})
    
    result = {
        "response_type": "legal_notice",
        "notice": {
            "header": {
                "title": f"LEGAL NOTICE - {notice_type.upper()}",
                "date": "Current Date",
                "from": LEGAL_SETTINGS.get("firm_name", "LexEdge Legal AI"),
                "to": recipient
            },
            "reference": {
                "case": case_data.get("case_name", "N/A"),
                "matter": case_data.get("case_type", "N/A")
            },
            "body": {
                "introduction": f"PLEASE TAKE NOTICE that {notice_content[:100]}...",
                "main_content": notice_content,
                "legal_basis": f"Pursuant to applicable laws of {LEGAL_SETTINGS.get('jurisdiction', 'Federal')}",
                "required_action": "Please respond within the time required by law."
            },
            "closing": {
                "signature": LEGAL_SETTINGS.get("firm_name", "LexEdge Legal AI"),
                "date_signed": "Current Date"
            },
            "service_information": {
                "method": "To be determined",
                "date_served": "To be completed"
            }
        },
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "notes": [
            "Verify proper service requirements",
            "Ensure compliance with notice periods",
            "Document proof of service"
        ],
        "disclaimer": "This draft must be reviewed by licensed counsel before sending."
    }
    
    return json.dumps(result, indent=2)


def draft_demand_letter(recipient: str, demand_amount: str, demand_basis: str, deadline: str, tool_context: ToolContext) -> str:
    """
    Draft a demand letter.
    
    Args:
        recipient: Recipient of the demand
        demand_amount: Amount or action demanded
        demand_basis: Legal basis for the demand
        deadline: Deadline for response/compliance
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Draft demand letter
    """
    logger.info(f"[CORRESPONDENCE] Drafting demand letter to: {recipient}")
    
    case_data = agent_context_manager.get_context("CaseProfile").get("data", {})
    client_name = case_data.get("client_name", "our client")
    
    result = {
        "response_type": "demand_letter",
        "letter": {
            "header": {
                "title": "DEMAND LETTER",
                "date": "Current Date",
                "via": "Certified Mail, Return Receipt Requested",
                "to": recipient,
                "from": LEGAL_SETTINGS.get("firm_name", "LexEdge Legal AI"),
                "re": f"Demand on Behalf of {client_name}"
            },
            "body": {
                "introduction": f"Please be advised that this firm represents {client_name} in connection with the above-referenced matter.",
                "facts": "Statement of relevant facts supporting the demand.",
                "legal_basis": demand_basis,
                "demand": f"DEMAND IS HEREBY MADE for {demand_amount}.",
                "deadline": f"Please respond to this demand on or before {deadline}.",
                "consequences": "Failure to comply with this demand may result in the initiation of legal proceedings without further notice.",
                "reservation_of_rights": "All rights are expressly reserved."
            },
            "closing": {
                "regards": "Very truly yours,",
                "firm": LEGAL_SETTINGS.get("firm_name", "LexEdge Legal AI"),
                "signature_line": "[Attorney Name]",
                "cc": client_name
            }
        },
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "notes": [
            "Review all facts for accuracy",
            "Verify legal basis and citations",
            "Confirm deadline is appropriate",
            "Send via certified mail with return receipt"
        ],
        "disclaimer": "This draft must be reviewed by licensed counsel before sending."
    }
    
    return json.dumps(result, indent=2)


def draft_settlement_proposal(recipient: str, settlement_terms: str, rationale: str, tool_context: ToolContext) -> str:
    """
    Draft a settlement proposal.
    
    Args:
        recipient: Recipient of the proposal
        settlement_terms: Proposed settlement terms
        rationale: Rationale for the settlement
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Draft settlement proposal
    """
    logger.info(f"[CORRESPONDENCE] Drafting settlement proposal to: {recipient}")
    
    case_data = agent_context_manager.get_context("CaseProfile").get("data", {})
    client_name = case_data.get("client_name", "our client")
    
    result = {
        "response_type": "settlement_proposal",
        "proposal": {
            "header": {
                "title": "SETTLEMENT PROPOSAL",
                "marking": "CONFIDENTIAL - FOR SETTLEMENT PURPOSES ONLY",
                "date": "Current Date",
                "to": recipient,
                "from": LEGAL_SETTINGS.get("firm_name", "LexEdge Legal AI"),
                "re": f"Settlement Proposal - {case_data.get('case_name', 'Pending Matter')}"
            },
            "body": {
                "introduction": f"On behalf of {client_name}, we submit this settlement proposal for your consideration.",
                "background": "Brief summary of the dispute and proceedings to date.",
                "rationale": rationale,
                "proposed_terms": {
                    "summary": settlement_terms,
                    "key_terms": [
                        "Term 1 - To be specified",
                        "Term 2 - To be specified",
                        "Term 3 - To be specified"
                    ],
                    "release_language": "Mutual release of all claims",
                    "confidentiality": "Terms to remain confidential"
                },
                "response_deadline": "Please respond within [X] days.",
                "reservation": "This proposal is made for settlement purposes only and is not an admission of liability."
            },
            "closing": {
                "regards": "Very truly yours,",
                "firm": LEGAL_SETTINGS.get("firm_name", "LexEdge Legal AI"),
                "signature_line": "[Attorney Name]"
            },
            "legal_protections": {
                "rule_408": "This communication is made pursuant to Federal Rule of Evidence 408 and equivalent state rules.",
                "confidentiality": "This proposal is confidential and may not be disclosed or used for any purpose other than settlement discussions."
            }
        },
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "notes": [
            "Review settlement terms with client",
            "Verify authority to make proposal",
            "Consider tax implications",
            "Document all settlement communications"
        ],
        "disclaimer": "This draft must be reviewed by licensed counsel and approved by client before sending."
    }
    
    return json.dumps(result, indent=2)
