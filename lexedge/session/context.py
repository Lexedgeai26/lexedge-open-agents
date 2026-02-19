"""
Utilities for binding the current session/user context so that tool calls
can resolve the correct tenant credentials per request.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Optional, Dict, Any

_current_session_ctx: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "lexedge_current_session_ctx", default=None
)


def bind_session_context(user_id: Optional[str], session_id: Optional[str]) -> Token:
    """
    Bind the currently executing task to the provided user/session identifiers.

    Args:
        user_id: The logical user identifier for the session.
        session_id: The backing session identifier.

    Returns:
        Context token that should be passed to ``reset_session_context``.
    """
    return _current_session_ctx.set(
        {"user_id": user_id, "session_id": session_id}
    )


def reset_session_context(token: Token) -> None:
    """Reset the bound session context using the token returned from bind."""
    if token:
        _current_session_ctx.reset(token)


def get_bound_session_context() -> Optional[Dict[str, Any]]:
    """Return the currently bound session context if one is active."""
    return _current_session_ctx.get()
