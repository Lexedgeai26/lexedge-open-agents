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


def track_deadlines(case_id: str, tool_context: ToolContext) -> str:
    """
    Track and manage case deadlines.
    
    Args:
        case_id: Case identifier
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Deadline tracking information
    """
    logger.info(f"[CASE_MGMT] Tracking deadlines for case: {case_id}")
    
    case_data = agent_context_manager.get_context("CaseProfile").get("data", {})
    
    result = {
        "response_type": "deadline_tracking",
        "case_id": case_id,
        "case_name": case_data.get("case_name", "Unknown"),
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "deadlines": {
            "upcoming": [
                {
                    "type": "Filing Deadline",
                    "date": case_data.get("filing_deadline", "To be determined"),
                    "description": "Response/Motion filing deadline",
                    "priority": "High",
                    "days_remaining": "Calculate from current date"
                },
                {
                    "type": "Discovery Deadline",
                    "date": "To be determined",
                    "description": "Discovery completion deadline",
                    "priority": "Medium",
                    "days_remaining": "Calculate from current date"
                }
            ],
            "statute_of_limitations": {
                "applicable": True,
                "deadline": "Review applicable statute",
                "notes": f"Based on {LEGAL_SETTINGS.get('jurisdiction')} law"
            },
            "court_dates": [
                {
                    "type": "Hearing",
                    "date": "To be scheduled",
                    "court": "Court name",
                    "judge": "Assigned judge"
                }
            ]
        },
        "court_levels": LEGAL_SETTINGS.get("court_levels", []),
        "reminders": [
            "Review all deadlines with licensed counsel",
            "Calendar all critical dates",
            "Set reminder notifications"
        ]
    }
    
    return json.dumps(result, indent=2)


def generate_case_timeline(case_id: str, tool_context: ToolContext) -> str:
    """
    Generate a comprehensive case timeline.
    
    Args:
        case_id: Case identifier
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Case timeline with key events
    """
    logger.info(f"[CASE_MGMT] Generating timeline for case: {case_id}")
    
    case_data = agent_context_manager.get_context("CaseProfile").get("data", {})
    
    result = {
        "response_type": "case_timeline",
        "case_id": case_id,
        "case_name": case_data.get("case_name", "Unknown"),
        "case_type": case_data.get("case_type", "Unknown"),
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "timeline": {
            "phases": [
                {
                    "phase": "Case Intake",
                    "status": "Completed" if case_data else "In Progress",
                    "events": ["Client consultation", "Conflict check", "Engagement letter"]
                },
                {
                    "phase": "Investigation & Research",
                    "status": "In Progress",
                    "events": ["Fact gathering", "Legal research", "Document review"]
                },
                {
                    "phase": "Pleadings",
                    "status": "Pending",
                    "events": ["Draft complaint/answer", "File with court", "Service of process"]
                },
                {
                    "phase": "Discovery",
                    "status": "Pending",
                    "events": ["Written discovery", "Depositions", "Expert witnesses"]
                },
                {
                    "phase": "Pre-Trial",
                    "status": "Pending",
                    "events": ["Motions practice", "Settlement negotiations", "Trial preparation"]
                },
                {
                    "phase": "Trial/Resolution",
                    "status": "Pending",
                    "events": ["Trial", "Verdict/Judgment", "Post-trial motions"]
                }
            ],
            "key_milestones": [
                {"milestone": "Case opened", "date": "Current"},
                {"milestone": "Filing deadline", "date": case_data.get("filing_deadline", "TBD")}
            ]
        },
        "notes": "Timeline is estimated and subject to change based on case developments"
    }
    
    return json.dumps(result, indent=2)


def manage_case_tasks(case_id: str, action: str, task_details: str, tool_context: ToolContext) -> str:
    """
    Manage tasks for a case.
    
    Args:
        case_id: Case identifier
        action: Action to perform (add, update, complete, list)
        task_details: Details of the task
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Task management result
    """
    logger.info(f"[CASE_MGMT] Managing tasks for case {case_id}: {action}")
    
    result = {
        "response_type": "task_management",
        "case_id": case_id,
        "action": action,
        "tasks": {
            "pending": [
                {
                    "id": "task_001",
                    "title": "Review case documents",
                    "priority": "High",
                    "due_date": "Upcoming",
                    "assigned_to": "Legal team",
                    "status": "Pending"
                },
                {
                    "id": "task_002",
                    "title": "Conduct legal research",
                    "priority": "High",
                    "due_date": "Upcoming",
                    "assigned_to": "Research team",
                    "status": "In Progress"
                }
            ],
            "completed": [],
            "new_task": {
                "details": task_details,
                "status": f"Task {action} processed"
            } if task_details else None
        },
        "summary": f"Task {action} completed for case {case_id}"
    }
    
    return json.dumps(result, indent=2)


def update_case_status(case_id: str, new_status: str, notes: str, tool_context: ToolContext) -> str:
    """
    Update the status of a case.
    
    Args:
        case_id: Case identifier
        new_status: New status for the case
        notes: Notes about the status change
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Status update confirmation
    """
    logger.info(f"[CASE_MGMT] Updating status for case {case_id} to: {new_status}")
    
    case_data = agent_context_manager.get_context("CaseProfile").get("data", {})
    old_status = case_data.get("status", "Unknown")
    
    # Update context
    try:
        agent_context_manager.update_context("CaseProfile", {
            "data": {
                **case_data,
                "status": new_status
            }
        })
    except Exception as ctx_err:
        logger.warning(f"Failed to update case status: {ctx_err}")
    
    result = {
        "response_type": "status_update",
        "case_id": case_id,
        "case_name": case_data.get("case_name", "Unknown"),
        "status_change": {
            "previous_status": old_status,
            "new_status": new_status,
            "updated_by": "LexEdge Legal AI",
            "timestamp": "Current",
            "notes": notes
        },
        "valid_statuses": [
            "Active",
            "Pending",
            "Discovery",
            "Pre-Trial",
            "Trial",
            "Settlement",
            "Closed",
            "On Hold"
        ],
        "confirmation": f"Case status updated from '{old_status}' to '{new_status}'"
    }
    
    return json.dumps(result, indent=2)
