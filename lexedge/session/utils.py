"""
Utility functions for session management.
"""

import logging
from typing import Dict, Any

try:
    # Package import
    from .service import import_time
    from ..config import MAX_MESSAGES_PER_SESSION
except ImportError:
    # Direct import when running from applivew directory
    from service import import_time
    from config import MAX_MESSAGES_PER_SESSION

logger = logging.getLogger(__name__)

# Context control settings
MAX_INTERACTION_HISTORY_ENTRIES = 10  # Maximum entries in interaction_history
MAX_CONTEXT_LENGTH = 32000  # Maximum total character length for context

def get_session_token_data(state: Dict[str, Any]) -> Dict[str, Any]:
    """Safely retrieve token login data from session state."""
    if not state:
        return {}
    
    return state.get('token_login_data', {})

def _trim_interaction_history(interaction_history: list) -> list:
    """
    Trim interaction history to prevent context overflow.
    
    Args:
        interaction_history: List of interaction history entries
        
    Returns:
        list: Trimmed interaction history
    """
    if not interaction_history:
        return interaction_history
    
    # First, check if we exceed the maximum number of entries
    if len(interaction_history) > MAX_INTERACTION_HISTORY_ENTRIES:
        logger.info(f"Trimming interaction history: {len(interaction_history)} -> {MAX_INTERACTION_HISTORY_ENTRIES} entries")
        interaction_history = interaction_history[-MAX_INTERACTION_HISTORY_ENTRIES:]
    
    # Calculate total context length
    total_length = sum(
        len(entry.get("content", "")) 
        for entry in interaction_history
    )
    
    # If total length exceeds limit, trim from the beginning
    if total_length > MAX_CONTEXT_LENGTH:
        logger.info(f"Trimming interaction history by content length: {total_length} -> max {MAX_CONTEXT_LENGTH} chars")
        
        while total_length > MAX_CONTEXT_LENGTH and len(interaction_history) > 1:
            # Remove the oldest entry
            removed_entry = interaction_history.pop(0)
            total_length -= len(removed_entry.get("content", ""))
        
        logger.info(f"Final interaction history: {len(interaction_history)} entries, {total_length} chars")
    
    return interaction_history

async def add_user_query_to_history(session_service, app_name: str, 
                             user_id: str, session_id: str, query: str) -> None:
    """Add a user query to the interaction history in the session state."""
    # Skip empty messages
    if not query or not query.strip():
        logger.info("Skipping empty user query")
        return
    
    # Skip login/logout related messages
    login_keywords = ["login", "sign in", "signin", "log in", "authenticate", "email:", "@", "password:", "credentials"]
    logout_keywords = ["logout", "sign out", "signout", "log out"]
    
    query_lower = query.lower()
    
    # Check if this is a login/logout related query that should be skipped
    is_login_related = any(keyword in query_lower for keyword in login_keywords)
    is_logout_related = any(keyword in query_lower for keyword in logout_keywords)
    
    if is_login_related or is_logout_related:
        logger.info(f"Skipping login/logout related message: '{query}'")
        return
        
    session = await session_service.get_session(
        app_name=app_name, 
        user_id=user_id, 
        session_id=session_id
    )
    
    # Get current state
    state = session.state
    
    # Add to interaction history
    interaction_history = state.get("interaction_history", [])
    interaction_history.append({
        "role": "user",
        "content": query,
        "timestamp": import_time().time()
    })
    
    # Trim interaction history to prevent context overflow
    interaction_history = _trim_interaction_history(interaction_history)
    state["interaction_history"] = interaction_history
    
    # Update last query
    state["last_query"] = query
    
    # Update session with new state
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=state
    )
    
    # Also save to messages table
    await session_service.save_message(
        session_id=session_id,
        role="user",
        content=query
    )

async def add_agent_response_to_history(session_service, app_name: str, 
                                 user_id: str, session_id: str, 
                                 agent_name: str, response: str) -> None:
    """Add an agent response to the interaction history in the session state."""
    # Skip empty messages
    if not response or not response.strip():
        logger.info("Skipping empty agent response")
        return
        
    # Skip login/logout related messages
    response_lower = response.lower()
    
    # Skip login/logout related responses based on content or agent name
    if agent_name == "lexedge_login" or "login failed" in response_lower or "log in" in response_lower or "logged in" in response_lower or "logged out" in response_lower:
        logger.info(f"Skipping login/logout related agent response from {agent_name}")
        return
        
    session = await session_service.get_session(
        app_name=app_name, 
        user_id=user_id, 
        session_id=session_id
    )
    
    # Get current state
    state = session.state
    
    # Add to interaction history
    interaction_history = state.get("interaction_history", [])
    interaction_history.append({
        "role": "agent",
        "agent_name": agent_name,
        "content": response,
        "timestamp": import_time().time()
    })
    
    # Trim interaction history to prevent context overflow
    interaction_history = _trim_interaction_history(interaction_history)
    state["interaction_history"] = interaction_history
    
    # Update last response
    state["last_response"] = response
    
    # Process login-related responses
    if agent_name == "lexedge_login":
        process_login_response(state, response)
    
    # Update session with new state
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=state
    )
    
    # Also save to messages table
    await session_service.save_message(
        session_id=session_id,
        role="assistant",
        content=response
    )

def process_login_response(state: Dict[str, Any], response: str) -> None:
    """Process login response to update authentication state."""
    import json
    
    login_data = state.get("login_data", {})
    login_failed = state.get("login_failed", False)
    
    # Parse JSON from the login agent if present
    login_result = None
    if "{" in response and "}" in response:
        try:
            json_start = response.find("{")
            json_end = response.find("}", json_start) + 1
            login_json_str = response[json_start:json_end]
            login_result = json.loads(login_json_str)
            logger.info(f"Extracted login result from history: {login_result}")
            
            # Process login result based on status
            if login_result.get("status") == "success":
                # If login was successful and we have login data, update auth state
                if login_data:
                    state["is_authenticated"] = True
                    state["user_name"] = login_data.get("name", "")
                    state["user_id"] = login_data.get("user_id", "")
                    state["token"] = login_data.get("token", "")
                    state["tenant_id"] = login_data.get("tenant_id", "")
                    state["tenant_name"] = login_data.get("tenant_name", "")
                    state["role"] = login_data.get("role", "")
                    state["is_admin"] = login_data.get("is_admin", False)
                    # Clear any login failure state
                    state["login_failed"] = False
                    state["login_error_message"] = None
                    state["login_error_code"] = 0
                    state["login_error_type"] = ""
            elif login_result.get("status") == "failure":
                # Mark login as failed with structured error information
                state["login_failed"] = True
                state["login_error_message"] = login_result.get("message", "Authentication failed")
                state["login_error_code"] = login_result.get("error_code", 0)
                state["login_error_type"] = login_result.get("error_type", "")
                state["is_authenticated"] = False
        except Exception as e:
            logger.error(f"Error parsing JSON from login response in history: {e}")
    
    # If we couldn't parse JSON, fall back to text-based detection
    if not login_result:
        # If login was successful
        if "successfully authenticated" in response.lower() and login_data:
            state["is_authenticated"] = True
            state["user_name"] = login_data.get("name", "")
            state["user_id"] = login_data.get("user_id", "")
            state["token"] = login_data.get("token", "")
            state["tenant_id"] = login_data.get("tenant_id", "")
            state["tenant_name"] = login_data.get("tenant_name", "")
            state["role"] = login_data.get("role", "")
            state["is_admin"] = login_data.get("is_admin", False)
            # Clear the login failure state
            state["login_failed"] = False
            state["login_error_message"] = None
            state["login_error_code"] = 0
            state["login_error_type"] = ""
        
        # If login failed (text-based detection as fallback)
        elif any(phrase in response.lower() for phrase in ["login failed", "authentication failed", "invalid"]) or login_failed:
            # Make sure the login_failed flag is set
            state["login_failed"] = True
            # Only set error message if it's not already present
            if not state.get("login_error_message"):
                state["login_error_message"] = "Invalid credentials or server error"
                state["login_error_code"] = 400
                state["login_error_type"] = "general_error"

async def display_state(session_service, app_name: str, user_id: str, 
                 session_id: str, label: str = "Current State") -> None:
    """Display the current session state."""
    try:
        session = await session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        print(f"\n--- {label} ---")
        
        # Display user info
        if "user_name" in session.state:
            print(f"User: {session.state.get('user_name', 'Unknown')}")
        
        # Display last query/response if they exist
        if session.state.get("last_query"):
            print(f"Last Query: {session.state['last_query']}")
        if session.state.get("last_response"):
            print(f"Last Response: {session.state['last_response']}")
        
        # Display interaction history (summarized)
        history = session.state.get("interaction_history", [])
        if history:
            print(f"Interaction History: {len(history)} entries")
        
        print("-" * (22 + len(label)))
    except Exception as e:
        print(f"Error displaying state: {e}") 