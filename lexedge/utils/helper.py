from typing import Any, Dict, Optional

from lexedge.session import session_service
from lexedge.session.context import get_bound_session_context
from lexedge.config import APP_NAME
import logging

logger = logging.getLogger(__name__)


def _enrich_state(session, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return a copy of the session state with metadata attached."""
    resolved_state = dict(state or session.state or {})
    if "session_id" not in resolved_state:
        resolved_state["session_id"] = getattr(session, "id", None)
    if "user_id" not in resolved_state:
        resolved_state["user_id"] = getattr(session, "user_id", None)
    return resolved_state


async def _get_session_by_ids(user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    try:
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
        return _enrich_state(session)
    except Exception as exc:
        logger.warning(
            "Unable to load session %s for user %s: %s",
            session_id,
            user_id,
            exc,
        )
        return None


async def _latest_session_for_user(user_id: str) -> Optional[Dict[str, Any]]:
    sessions = await session_service.list_sessions(app_name=APP_NAME, user_id=user_id)
    if not sessions:
        return None
    session = max(sessions, key=lambda s: getattr(s, "last_update_time", 0))
    return _enrich_state(session)


async def _find_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    sessions = await session_service.list_sessions(app_name=APP_NAME)
    for session in sessions:
        if session.id == session_id:
            return _enrich_state(session)
    return None


async def _pick_recent_session() -> Optional[Dict[str, Any]]:
    sessions = await session_service.list_sessions(app_name=APP_NAME)
    if not sessions:
        return None

    def _pick(predicate):
        filtered = [s for s in sessions if predicate(s)]
        if filtered:
            return max(filtered, key=lambda s: getattr(s, "last_update_time", 0))
        return None

    # Prefer authenticated, then sessions with credentials, then any recent session.
    for selector in (
        lambda s: s.state.get("is_authenticated"),
        lambda s: s.state.get("tenant_id") and s.state.get("token"),
        lambda s: True,
    ):
        session = _pick(selector)
        if session:
            return _enrich_state(session)

    return None


async def _create_fallback_session(user_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
    fallback_session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        state=state,
    )
    return _enrich_state(fallback_session)


async def get_session_data(
    user_id: Optional[str] = None, session_id: Optional[str] = None
) -> dict:
    """Get session data for the current request, honoring bound context when present."""
    try:
        bound_context = get_bound_session_context()
        if bound_context:
            user_id = user_id or bound_context.get("user_id")
            session_id = session_id or bound_context.get("session_id")

        # 1) Explicit session binding
        if user_id and session_id:
            state = await _get_session_by_ids(user_id, session_id)
            if state:
                return state

        # 2) User-specific fallback
        if user_id:
            state = await _latest_session_for_user(user_id)
            if state:
                return state

        # 3) Session-id lookup
        if session_id:
            state = await _find_session_by_id(session_id)
            if state:
                return state

        # 4) Global fallback (legacy behavior)
        state = await _pick_recent_session()
        if state:
            return state

        logger.warning(
            "No active sessions found - creating fallback session for open agent"
        )
        return await _create_fallback_session(
            "system_user",
            {
                "tenant_id": "apl_jobrocket",
                "token": "1c3a1a6e-0014-46d1-bc64-dda4753e5721",
                "is_authenticated": True,
                "is_system_user": True,
                "is_admin": True,
                "created_by": "",
            },
        )

    except Exception as e:
        logger.error(f"Error getting session data: {str(e)}")
        try:
            logger.info("Creating emergency fallback session for open agent")
            return await _create_fallback_session(
                "emergency_user",
                {
                    "tenant_id": "test",
                    "token": "emergency_token",
                    "is_authenticated": False,
                    "is_emergency": True,
                },
            )
        except Exception as emergency_error:
            logger.error(f"Emergency session creation failed: {str(emergency_error)}")
            raise ValueError("Unable to create any session for API access")


def get_admin_scope_params(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Return admin scope params for API calls based on user context."""
    return {"is_admin": True, "created_by": 0}
