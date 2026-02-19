"""
Login-related callback implementations for agent events.
"""

import logging
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.genai import types

logger = logging.getLogger(__name__)

def after_login_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    After agent callback that runs after login attempts to show appropriate login success/failure messages.
    
    Args:
        callback_context: The context for the callback with access to session state
        
    Returns:
        Optional[types.Content]: None to allow normal processing, or Content to override response
    """
    logger.info("[CALLBACK] After login callback triggered")
    
    session_state = callback_context.state
    # Check if this is a login-related interaction
    is_login_attempt = session_state.get("is_login_attempt", False)
    login_response = session_state.get("login_response", None)
    
    # Check for a direct login success flag (set by the direct login function)
    login_successful = session_state.get("is_authenticated", False)
    login_data = session_state.get("login_data", None)
    
    # Log the authentication state
    logger.info(f"[CALLBACK] Authentication state: is_authenticated={login_successful}, login_data={login_data is not None}")
    
    if is_login_attempt:
        logger.info(f"[CALLBACK] Login attempt detected. Response: {login_response}")
        # Reset flag for next interaction
        session_state["is_login_attempt"] = False
        
        if login_response:
            # Store important login information for the LoginManager
            if login_response.get("status") == "success":
                session_state["login_successful"] = True
                session_state["is_authenticated"] = True
                session_state["user_name"] = login_response.get("user_name", "")
                session_state["role"] = login_response.get("role", "")
                session_state["login_failed"] = False
                session_state["login_error_message"] = None
                session_state["login_error_code"] = 0
                session_state["login_error_type"] = ""
                logger.info(f"[CALLBACK] Login success information prepared for LoginManager")
            else:
                session_state["login_successful"] = False
                session_state["login_failed"] = True
                session_state["is_authenticated"] = False
                session_state["login_error_message"] = login_response.get("error_message", "Authentication failed")
                session_state["login_error_code"] = login_response.get("error_code", 0)
                session_state["login_error_type"] = login_response.get("error_type", "")
                logger.info(f"[CALLBACK] Login failure information prepared for LoginManager: {login_response.get('error_message')}")
            
            # Check if we already have a pre-prepared message from the Login agent
            if not session_state.get("login_response_message"):
                # Prepare a message based on login status
                if login_response.get("status") == "success" or login_successful:
                    user_name = session_state.get("user_name", "User")
                    role = session_state.get("role", "User")
                    session_state["login_response_message"] = (
                        f"Welcome, {user_name}! You've successfully logged in as {role}. "
                        f"You now have access to all Appliview features."
                    )
                else:
                    error_message = session_state.get("login_error_message", "Authentication failed")
                    error_code = session_state.get("login_error_code", 401)
                    
                    if error_code == 401:
                        session_state["login_response_message"] = (
                            f"Login failed: {error_message}\n\n"
                            f"Please verify your credentials and try again."
                        )
                    elif error_code == 404:
                        session_state["login_response_message"] = (
                            f"Login failed: {error_message}\n\n"
                            f"The email you provided was not found in our system. "
                            f"Please check your email address and try again."
                        )
                    else:
                        session_state["login_response_message"] = (
                            f"Login failed: {error_message}\n\n"
                            f"Please try again later or contact support if the issue persists."
                        )
            
            # Instead of transferring, create a custom response with the prepared message
            login_response_message = session_state.get("login_response_message", "")
            if login_response_message:
                logger.info(f"[CALLBACK] Using prepared login response message: {login_response_message[:50]}...")
                return types.Content(
                    role="assistant",
                    parts=[types.Part(text=login_response_message)]
                )
    
    return None

class BeforeLoginCallback:
    """Callback to execute before the Login agent runs."""
    
    def __init__(self):
        """Initialize the callback."""
        self.name = "BeforeLoginCallback"
    
    async def __call__(self, callback_context: CallbackContext, **kwargs) -> Optional[types.Content]:
        """
        Execute before Login agent runs.
        
        Args:
            callback_context: The context for the callback
            
        Returns:
            Optional[types.Content]: None to continue with Login agent
        """
        logger.info(f"BeforeLoginCallback called for session {callback_context.session.id}")
        return None

class AfterLoginCallback:
    """Callback to execute after the Login agent runs."""
    
    def __init__(self):
        """Initialize the callback."""
        self.name = "AfterLoginCallback"
    
    async def __call__(self, callback_context: CallbackContext, **kwargs) -> Optional[types.Content]:
        """
        Execute after Login agent runs.
        
        Args:
            callback_context: The context for the callback
            
        Returns:
            Optional[types.Content]: None to use Login agent response
        """
        logger.info(f"AfterLoginCallback called for session {callback_context.session.id}")
        
        # Set the is_login_attempt flag to trigger the main callback later
        callback_context.state["is_login_attempt"] = True
        
        return None 