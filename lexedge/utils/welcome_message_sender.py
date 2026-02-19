#!/usr/bin/env python
"""
Welcome Message Sender Utility

This module provides functionality to send welcome messages immediately after successful login
using WebSocket push notifications, without waiting for LLM processing.
"""

import logging
import asyncio
import threading
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


async def send_welcome_message_async(
    session_id: str,
    user_id: str,
    user_name: str,
    tenant_name: str,
    welcome_message: str,
    formatted_welcome: str,
    capabilities_overview: Dict[str, Any],
    quick_start_suggestions: list
) -> bool:
    """
    Send welcome message via WebSocket asynchronously.
    
    Args:
        session_id: User's session ID
        user_id: User's ID
        user_name: User's display name
        tenant_name: Tenant name
        welcome_message: Plain text welcome message
        formatted_welcome: HTML formatted welcome message
        capabilities_overview: System capabilities overview
        quick_start_suggestions: List of quick start suggestions
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        # Import here to avoid circular imports
        from lexedge.utils.agent_pusher import _get_websocket_manager
        
        websocket_manager = _get_websocket_manager()
        if not websocket_manager:
            logger.warning("WebSocket manager not available, cannot send welcome message")
            return False
        
        # Create welcome message data with the EXACT same structure as WebSocket responses
        # This matches the format used in app.py for regular responses and auto-welcome
        welcome_data = {
            "type": "response",
            "session_id": session_id,
            "response": welcome_message,
            "formatted_response": formatted_welcome,
            "agent": "welcome_message_sender", 
            "is_authenticated": True,
            "user_name": user_name,
            "user_id": user_id,
            "role": "user",
            "action_suggestions": {
                "suggestions": quick_start_suggestions
            },
            "capabilities_overview": capabilities_overview,
            "message": "Welcome message sent immediately after login",
            "timestamp": time.time()
        }
        
        # Send welcome message to SPECIFIC SESSION ONLY (not broadcast)
        success = await websocket_manager.send_to_session(session_id, welcome_data)
        if success:
            logger.info(f"✅ Welcome message sent to session {session_id} for user {user_name} (TENANT ISOLATED)")
        else:
            logger.warning(f"⚠️ Failed to send welcome message to session {session_id} - no connection found")
        return True
        
    except Exception as e:
        logger.error(f"Error sending welcome message via WebSocket: {str(e)}")
        return False


def send_welcome_message_sync(
    session_id: str,
    user_id: str,
    user_name: str,
    tenant_name: str,
    welcome_message: str,
    formatted_welcome: str,
    capabilities_overview: Dict[str, Any],
    quick_start_suggestions: list
) -> bool:
    """
    Send welcome message via WebSocket synchronously.
    
    This function handles the async/thread management automatically.
    
    Args:
        session_id: User's session ID
        user_id: User's ID
        user_name: User's display name
        tenant_name: Tenant name
        welcome_message: Plain text welcome message
        formatted_welcome: HTML formatted welcome message
        capabilities_overview: System capabilities overview
        quick_start_suggestions: List of quick start suggestions
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        async def _send_async():
            return await send_welcome_message_async(
                session_id=session_id,
                user_id=user_id,
                user_name=user_name,
                tenant_name=tenant_name,
                welcome_message=welcome_message,
                formatted_welcome=formatted_welcome,
                capabilities_overview=capabilities_overview,
                quick_start_suggestions=quick_start_suggestions
            )
        
        # Try to run in existing event loop or create new one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If event loop is running, schedule the coroutine and return immediately
                task = asyncio.create_task(_send_async())
                logger.info(f"📧 Scheduled welcome message for {user_name} (ID: {user_id})")
                return True  # Return True immediately since we scheduled it
            else:
                # Run in the existing loop
                return loop.run_until_complete(_send_async())
        except RuntimeError:
            # No event loop, create a new one in a thread
            result_container = [False]
            
            def run_in_thread():
                try:
                    result_container[0] = asyncio.run(_send_async())
                except Exception as e:
                    logger.error(f"Error in welcome message thread: {str(e)}")
                    result_container[0] = False
            
            thread = threading.Thread(target=run_in_thread, daemon=True)
            thread.start()
            thread.join(timeout=5.0)  # Wait up to 5 seconds
            
            logger.info(f"📧 Welcome message thread completed for {user_name}")
            return result_container[0]
        
    except Exception as e:
        logger.error(f"Error sending welcome message: {str(e)}")
        return False


def send_immediate_welcome_message(session_data: Dict[str, Any]) -> bool:
    """
    Send welcome message immediately after successful login.
    
    This is the main function to be called from the login endpoint.
    
    Args:
        session_data: Dictionary containing session information including:
            - session_id: User's session ID
            - user_id: User's ID
            - user_name: User's display name
            - tenant_name: Tenant name
            - welcome_message: Plain text welcome message
            - formatted_welcome: HTML formatted welcome message
            - capabilities_overview: System capabilities overview
            - quick_start_suggestions: List of quick start suggestions
            
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    required_fields = [
        'session_id', 'user_id', 'user_name', 'tenant_name',
        'welcome_message', 'formatted_welcome', 'capabilities_overview',
        'quick_start_suggestions'
    ]
    
    # Validate required fields
    missing_fields = [field for field in required_fields if field not in session_data]
    if missing_fields:
        logger.error(f"Missing required fields for welcome message: {missing_fields}")
        return False
    
    logger.info(f"📧 Sending immediate welcome message for user {session_data['user_name']} after login")
    
    return send_welcome_message_sync(
        session_id=session_data['session_id'],
        user_id=session_data['user_id'],
        user_name=session_data['user_name'],
        tenant_name=session_data['tenant_name'],
        welcome_message=session_data['welcome_message'],
        formatted_welcome=session_data['formatted_welcome'],
        capabilities_overview=session_data['capabilities_overview'],
        quick_start_suggestions=session_data['quick_start_suggestions']
    )


def send_custom_welcome_template(
    session_id: str,
    user_id: str,
    user_name: str,
    tenant_name: str,
    custom_message: Optional[str] = None
) -> bool:
    """
    Send a custom welcome message with default template.
    
    Args:
        session_id: User's session ID
        user_id: User's ID
        user_name: User's display name
        tenant_name: Tenant name
        custom_message: Optional custom message to include
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    # Create a basic welcome message template
    if custom_message:
        welcome_text = f"Welcome {user_name}! 🎉\n\n{custom_message}\n\nYour session has been established for {tenant_name}."
    else:
        welcome_text = f"Welcome {user_name}! 🎉\n\nYour session has been established for {tenant_name}. I'm ready to help you with recruiting and job search tasks."
    
    formatted_welcome = f'<div class="welcome-message"><h2>🎉 Welcome {user_name}!</h2><p>{welcome_text}</p></div>'
    
    # Basic capabilities and suggestions
    capabilities_overview = {
        "total_agents": 1,
        "main_categories": ["Job Search", "Candidate Management"],
        "key_features": ["Natural language queries", "Job matching", "Candidate search"]
    }
    
    quick_start_suggestions = [
        {"id": "browse_jobs", "caption": "Browse Jobs", "command": "show me all jobs", "icon": "briefcase"},
        {"id": "find_candidates", "caption": "Find Candidates", "command": "show me candidates", "icon": "users"}
    ]
    
    return send_welcome_message_sync(
        session_id=session_id,
        user_id=user_id,
        user_name=user_name,
        tenant_name=tenant_name,
        welcome_message=welcome_text,
        formatted_welcome=formatted_welcome,
        capabilities_overview=capabilities_overview,
        quick_start_suggestions=quick_start_suggestions
    )


def send_delayed_welcome_message(session_data: Dict[str, Any], delay_seconds: float = 2.0) -> bool:
    """
    Send welcome message with a delay to ensure client has time to connect.
    
    Args:
        session_data: Dictionary containing session information
        delay_seconds: Number of seconds to wait before sending
        
    Returns:
        bool: True if message was scheduled successfully, False otherwise
    """
    async def _delayed_send():
        await asyncio.sleep(delay_seconds)
        return await send_welcome_message_async(
            session_id=session_data['session_id'],
            user_id=session_data['user_id'],
            user_name=session_data['user_name'],
            tenant_name=session_data['tenant_name'],
            welcome_message=session_data['welcome_message'],
            formatted_welcome=session_data['formatted_welcome'],
            capabilities_overview=session_data['capabilities_overview'],
            quick_start_suggestions=session_data['quick_start_suggestions']
        )
    
    try:
        # Schedule the delayed send
        def run_delayed():
            try:
                asyncio.run(_delayed_send())
            except Exception as e:
                logger.error(f"Error in delayed welcome message: {str(e)}")
        
        thread = threading.Thread(target=run_delayed, daemon=True)
        thread.start()
        
        logger.info(f"📧 Scheduled delayed welcome message for user {session_data['user_name']} in {delay_seconds} seconds")
        return True
        
    except Exception as e:
        logger.error(f"Error scheduling delayed welcome message: {str(e)}")
        return False


if __name__ == "__main__":
    # Test function
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from lexedge.utils import get_current_sessions
    
    # Test with existing session
    sessions = get_current_sessions()
    if sessions:
        session = sessions[0]
        result = send_custom_welcome_template(
            session_id=session["session_id"],
            user_id=session["user_id"],
            user_name="Test User",
            tenant_name="Test Tenant",
            custom_message="This is a test welcome message sent immediately without LLM processing!"
        )
        print(f"Welcome message test result: {result}")
    else:
        print("No active sessions found for testing") 