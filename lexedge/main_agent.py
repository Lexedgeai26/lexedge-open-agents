# Main agent module - exports the root agent for LexEdge Legal AI
from .root_agent import root_agent

def create_runner(app_name: str = "lexedge"):
    """Create a runner for the root agent."""
    from .session import session_service
    return session_service.create_runner(app_name, root_agent)

__all__ = ["root_agent", "create_runner"] 