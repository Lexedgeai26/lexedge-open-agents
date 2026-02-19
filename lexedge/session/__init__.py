"""
Session management module for Appliview.
"""

# Session package for Appliview agent system

# Import session service and utilities
from .service import SQLiteSessionService, session_service
from .utils import add_user_query_to_history, add_agent_response_to_history, display_state
from .context import (
    bind_session_context,
    reset_session_context,
    get_bound_session_context,
)

__all__ = [
    "SQLiteSessionService",
    "session_service",
    "add_user_query_to_history",
    "add_agent_response_to_history",
    "display_state",
    "bind_session_context",
    "reset_session_context",
    "get_bound_session_context",
]
