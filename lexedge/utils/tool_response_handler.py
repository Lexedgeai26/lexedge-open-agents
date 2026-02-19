#!/usr/bin/env python
"""
Tool Response Handler Utility for lexedge
Provides reusable patterns for WebSocket push, suggestions, and LLM cancellation
"""

import json
import logging
import asyncio
import threading
from typing import Optional, Dict, Any, Callable
from lexedge.utils.helper import get_session_data
from lexedge.session import session_service
from lexedge.session.context import get_bound_session_context
from lexedge.utils.agent_names import get_agent_friendly_name

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ToolResponseHandler:
    """
    A reusable handler for tool responses that provides:
    - WebSocket notifications with LLM cancellation
    - Context-aware suggestion generation
    - Session and user management
    - Error handling with fallback suggestions
    """
    
    def __init__(self, tool_name: str, suggestions_generator: Optional[Callable] = None):
        """
        Initialize the tool response handler.
        
        Args:
            tool_name: Name of the tool/function using this handler
            suggestions_generator: Optional function to generate suggestions (defaults to generic suggestions)
        """
        self.tool_name = tool_name
        self.suggestions_generator = suggestions_generator
        
    def get_session_data_placeholder(self):
        """Placeholder function for future session data enhancements."""
        return get_session_data()
        
    def get_current_user_and_session(self):
        """Get current user and session information from bound context."""
        try:
            # CRITICAL: Get session from bound context, NOT from most recent session
            # This ensures each tool call uses the correct session for the current request
            bound_context = get_bound_session_context()
            
            if bound_context and bound_context.get("session_id"):
                session_id = bound_context["session_id"]
                user_id = bound_context.get("user_id")
                
                logger.debug(f"Using bound session context: session={session_id}, user={user_id}")
                
                # Get the actual session object to access state
                from lexedge.config import APP_NAME
                
                # Helper to run async code synchronously
                def _get_session_sync():
                    try:
                        import asyncio
                        # Check if we are already in an event loop
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # We're in a running loop, but this is a sync method.
                                # This is tricky. We'll try to use a future or a separate thread.
                                import threading
                                from concurrent.futures import ThreadPoolExecutor
                                with ThreadPoolExecutor() as executor:
                                    future = executor.submit(lambda: asyncio.run(session_service.get_session(
                                        app_name=APP_NAME,
                                        user_id=user_id,
                                        session_id=session_id
                                    )))
                                    return future.result()
                            else:
                                return loop.run_until_complete(session_service.get_session(
                                    app_name=APP_NAME,
                                    user_id=user_id,
                                    session_id=session_id
                                ))
                        except RuntimeError:
                            # No loop, run with asyncio.run
                            return asyncio.run(session_service.get_session(
                                app_name=APP_NAME,
                                user_id=user_id,
                                session_id=session_id
                            ))
                    except Exception as loop_err:
                        logger.error(f"Error in sync session fetch: {loop_err}")
                        return None

                session = _get_session_sync()
                
                if session:
                    user_name = session.state.get("user_name") or session.state.get("user_id") or user_id
                    return (user_name, session_id, session.state)
                else:
                    logger.warning(f"Session {session_id} not found in session service")
                    return (user_id, session_id, {})
            else:
                logger.error("No bound session context found! Tools must be called within agent execution context.")
                return (None, None, None)
                
        except Exception as e:
            logger.error(f"Error getting current user and session: {str(e)}")
            return (None, None, None)
    
    def send_websocket_notification(
        self, 
        message: str, 
        cancel_llm_processing: bool = True, 
        action_suggestions: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Send a WebSocket notification with optional LLM cancellation and suggestions.
        
        Args:
            message: The notification message to send
            cancel_llm_processing: If True, cancels any pending LLM processing
            action_suggestions: Optional action suggestions to include
            session_id: Optional session ID (will be auto-detected if not provided)
            user_id: Optional user ID (will be auto-detected if not provided)
        """
        # Auto-detect user and session if not provided
        if not user_id or not session_id:
            detected_user_id, detected_session_id, _ = self.get_current_user_and_session()
            user_id = user_id or detected_user_id
            session_id = session_id or detected_session_id
        
        if not user_id or not session_id:
            logger.warning(f"⚠️ No active user/session found for {self.tool_name} WebSocket notification")
            return False
            
        try:
            # Import here to avoid circular imports
            from lexedge.utils.agent_pusher import _get_websocket_manager
            from lexedge.utils.task_manager import get_task_manager
            
            async def _send_notification():
                websocket_manager = _get_websocket_manager()
                if not websocket_manager:
                    logger.debug("WebSocket manager not available for notification")
                    return False
                
                # Handle LLM cancellation if requested  
                cancelled_count = 0
                if cancel_llm_processing:
                    task_manager = get_task_manager()
                    if task_manager:
                        # Convert message to string safely before slicing
                        message_str = str(message) if not isinstance(message, str) else message
                        cancelled_count = task_manager.cancel_session_tasks(
                            session_id, 
                            f"Cancelled by {self.tool_name}: {message_str[:50]}..."
                        )
                        logger.info(f"🛑 {self.tool_name} cancelled {cancelled_count} LLM tasks for session {session_id[:8]}...")
                    
                    # Send cancellation signal to SPECIFIC SESSION ONLY (not broadcast)
                    cancel_data = {
                        "type": "processing_cancelled",
                        "session_id": session_id,
                        "user_id": user_id,
                        "message": f"Processing cancelled by {self.tool_name}",
                        "source": f"{self.tool_name}_cancellation",
                        "timestamp": __import__('time').time(),
                        "tasks_cancelled": cancelled_count
                    }
                    await websocket_manager.send_to_session(session_id, cancel_data)
                    logger.info(f"📡 Sent processing cancellation signal to session {session_id} from {self.tool_name}")
                    
                    # Small delay to ensure cancellation is processed
                    await asyncio.sleep(0.1)
                
                # Create the main notification
                notification_data = {
                    "type": "response",
                    "session_id": session_id,
                    "user_id": user_id,
                    "agent": get_agent_friendly_name(self.tool_name),
                    "source": self.tool_name,
                    "tool_name": self.tool_name,
                    "timestamp": __import__('time').time(),
                    "notification_type": "system",
                    "is_authenticated": True,
                    "cancel_pending_processing": cancel_llm_processing,
                    "is_interruption": cancel_llm_processing,
                    "tasks_cancelled": cancelled_count,
                }

                # If message is a dict, avoid JS coercion to "[object Object]" by
                # placing the full payload under 'data' and emitting a string in 'response'.
                if isinstance(message, dict):
                    msg_text = (
                        message.get("message")
                        or message.get("title")
                        or f"{self.tool_name} update"
                    )
                    # Preserve full payload in response for renderers
                    notification_data["response"] = message
                    # Provide a human-readable string for any text displays
                    notification_data["formatted_response"] = msg_text
                    # Also include under 'data' for consumers expecting it there
                    notification_data["data"] = message
                    # Bubble up template/context for convenience if present
                    if "template" in message:
                        notification_data["template"] = message["template"]
                    if "context" in message:
                        notification_data["context"] = message["context"]
                else:
                    # Message is already a string
                    notification_data["response"] = message
                    notification_data["formatted_response"] = message
                
                # Add action suggestions if provided
                if action_suggestions:
                    notification_data["action_suggestions"] = action_suggestions
                    # Handle both list and dict formats safely
                    if isinstance(action_suggestions, dict):
                        suggestion_count = len(action_suggestions.get('suggestions', []))
                    elif isinstance(action_suggestions, list):
                        suggestion_count = len(action_suggestions)
                    else:
                        suggestion_count = 0
                    logger.info(f"📋 {self.tool_name}: Including {suggestion_count} action suggestions")
                
                # Send notification to SPECIFIC SESSION ONLY (not broadcast)
                success = await websocket_manager.send_to_session(session_id, notification_data)
                if success:
                    logger.info(f"✅ {self.tool_name}: Notification sent to session {session_id} (TENANT ISOLATED, cancel_llm: {cancel_llm_processing}, tasks_cancelled: {cancelled_count})")
                else:
                    logger.warning(f"⚠️ {self.tool_name}: Failed to send notification to session {session_id} - no connection found")
                return success
            
            # Handle event loop execution
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(_send_notification())
                    logger.info(f"📡 {self.tool_name}: Scheduled WebSocket notification for {user_id}")
                else:
                    loop.run_until_complete(_send_notification())
            except RuntimeError:
                # No event loop, create a new one in a thread
                def run_in_thread():
                    asyncio.run(_send_notification())
                
                thread = threading.Thread(target=run_in_thread, daemon=True)
                thread.start()
                logger.info(f"📡 {self.tool_name}: Started WebSocket notification thread for {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending WebSocket notification from {self.tool_name}: {str(e)}")
            return False
    
    def generate_suggestions(self, results_data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate contextual suggestions for the current tool.
        
        Args:
            results_data: The API response data
            context: Additional context for suggestion generation
            
        Returns:
            Dict containing suggestions in the standard format
        """
        if self.suggestions_generator:
            try:
                # Call suggestions generator with correct parameters for candidate suggestions
                # Candidate suggestions expect: (api_response, context, function_name)
                suggestions_result = self.suggestions_generator(results_data or {}, context or {}, self.tool_name)
                
                # Handle both list and dict formats
                if isinstance(suggestions_result, dict) and "suggestions" in suggestions_result:
                    # Already in correct format (new candidate suggestions format)
                    return suggestions_result
                elif isinstance(suggestions_result, list):
                    # Convert list format to dict format (legacy format)
                    return {"suggestions": suggestions_result}
                elif isinstance(suggestions_result, dict):
                    # Job suggestions format - already correct
                    return suggestions_result
                else:
                    # Fallback for unexpected formats
                    return {"suggestions": []}
                    
            except Exception as e:
                logger.error(f"❌ {self.tool_name}: Error generating suggestions: {str(e)}")
        else:
            logger.warning(f"⚠️ {self.tool_name}: No suggestions generator provided")
        
        # Fallback to basic suggestions
        fallback_suggestions = {
            "suggestions": [
                {
                    "id": f"{self.tool_name}_retry",
                    "caption": "Retry Operation",
                    "command": f"retry {self.tool_name}",
                    "icon": "refresh",
                    "icon_display": "🔄 Retry",
                    "priority": 1,
                    "category": "action"
                },
                {
                    "id": "search_candidates_fallback",
                    "caption": "Search for specific candidates",
                    "command": "search for candidates",
                    "icon": "search",
                    "icon_display": "🔍 Search",
                    "priority": 2,
                    "category": "action"
                },
                {
                    "id": "browse_all_fallback",
                    "caption": "Browse all available candidates",
                    "command": "list all candidates",
                    "icon": "users",
                    "icon_display": "👥 Browse",
                    "priority": 3,
                    "category": "action"
                }
            ]
        }
        logger.info(f"💡 {self.tool_name}: Using fallback suggestions: {len(fallback_suggestions['suggestions'])} items")
        return fallback_suggestions
    
    def handle_success_response(
        self, 
        data: Dict[str, Any], 
        formatter: Optional[Callable] = None,
        context: Optional[Dict[str, Any]] = None,
        custom_message: Optional[str] = None
    ) -> str:
        """
        Handle successful API response with formatting, suggestions, and WebSocket notification.
        
        Args:
            data: The API response data
            formatter: Optional function to format the response
            context: Additional context for suggestion generation
            custom_message: Optional custom message (if not provided, will use formatter or raw data)
            
        Returns:
            JSON string of the original response data
        """
        user_id, session_id, _ = self.get_current_user_and_session()
        
        if user_id and session_id:
            try:
                # Format the response if formatter is provided
                if formatter and data:
                    formatted_message = formatter(data)
                elif custom_message:
                    formatted_message = custom_message
                else:
                    formatted_message = f"✅ {self.tool_name} completed successfully"
                
                # Save API response data for export functionality
                # Only save if this is actual API response data (has results)
                if data and (data.get("results") or data.get("data") or len(data) > 0):
                    try:
                        from lexedge.session import session_service
                        import json
                        
                        # Save the API response with proper identification
                        session_service.save_api_response(
                            session_id=session_id,
                            api_source=self.tool_name,
                            response_content=formatted_message,
                            raw_data=json.dumps(data, ensure_ascii=False)
                        )
                        logger.info(f"💾 {self.tool_name}: Saved API response data for export (length: {len(formatted_message)} chars)")
                        
                    except Exception as save_error:
                        logger.error(f"❌ {self.tool_name}: Failed to save API response data: {str(save_error)}")
                
                # Generate suggestions
                suggestions = self.generate_suggestions(data, context)
                
                # Send WebSocket notification with formatted response and suggestions
                self.send_websocket_notification(
                    formatted_message,
                    cancel_llm_processing=True,
                    action_suggestions=suggestions,
                    session_id=session_id,
                    user_id=user_id
                )
                
                logger.info(f"📡 {self.tool_name}: Sent formatted response with {len(suggestions.get('suggestions', []))} suggestions")
                
            except Exception as e:
                logger.error(f"Failed to handle success response for {self.tool_name}: {str(e)}")
                self.handle_error_response(str(e), session_id, user_id)
        
        # Return original data as JSON without any modifications
        # Use ensure_ascii=False to preserve unicode characters properly
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def handle_error_response(self, error_message: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
        """
        Handle error response with WebSocket notification and error suggestions.
        
        Args:
            error_message: The error message
            session_id: Optional session ID
            user_id: Optional user ID
            
        Returns:
            JSON string with error information
        """
        # Auto-detect user and session if not provided
        if not user_id or not session_id:
            detected_user_id, detected_session_id, _ = self.get_current_user_and_session()
            user_id = user_id or detected_user_id
            session_id = session_id or detected_session_id
        
        # Sanitize error message for security - remove technical details
        user_friendly_message = self._sanitize_error_message(error_message)
        
        if user_id and session_id:
            try:
                # Send sanitized error notification to user (no action suggestions on errors)
                self.send_websocket_notification(
                    f"❌ **Error**: {user_friendly_message}",
                    cancel_llm_processing=True,
                    action_suggestions=None,
                    session_id=session_id,
                    user_id=user_id
                )
                
            except Exception:
                pass  # Ignore notification errors during error handling
        
        # Log the original technical error for debugging (server-side only)
        logger.error(f"[{self.tool_name}] Technical error (not shown to user): {error_message}")
        
        # Return sanitized error to prevent technical details leakage
        return json.dumps({"error": user_friendly_message}, ensure_ascii=False)
    
    def _sanitize_error_message(self, error_message: str) -> str:
        """
        Sanitize error messages to remove technical details and provide user-friendly messages.
        
        Args:
            error_message: Raw error message from API or system
            
        Returns:
            User-friendly error message with technical details removed
        """
        error_lower = error_message.lower()
        
        # Check for specific API errors and provide friendly messages
        if "document_type must be" in error_lower:
            return "Invalid search type. Please use the appropriate search function for jobs or candidates."
        
        if "api request failed with status 400" in error_lower:
            return "Invalid request. Please check your search parameters and try again."
        
        if "api request failed with status 401" in error_lower:
            return "Authentication required. Please log in and try again."
        
        if "api request failed with status 403" in error_lower:
            return "Access denied. You don't have permission to perform this action."
        
        if "api request failed with status 404" in error_lower:
            return "Service not found. The requested operation is not available."
        
        if "api request failed with status 429" in error_lower:
            return "Too many requests. Please wait a moment and try again."
        
        if "api request failed with status 500" in error_lower:
            return "Server error. Please try again later or contact support."
        
        if "timeout" in error_lower:
            return "Request timed out. Please try again with a simpler search."
        
        if "connection" in error_lower or "network" in error_lower:
            return "Connection error. Please check your internet connection and try again."
        
        if "missing tenant_id or token" in error_lower:
            return "Session expired. Please refresh the page and log in again."
        
        if "invalid parameter" in error_lower or "validation" in error_lower:
            return "Invalid input. Please check your search criteria and try again."
        
        # Handle JSON and parsing errors
        if any(term in error_lower for term in ["json", "parse", "decode", "format"]):
            return "Data processing error. Please try again or use different search terms."
        
        # Handle database and query errors
        if any(term in error_lower for term in ["database", "query", "sql", "elasticsearch"]):
            return "Search service temporarily unavailable. Please try again in a moment."
        
        # Handle authentication and session errors
        if any(term in error_lower for term in ["auth", "session", "credential", "permission"]):
            return "Authentication issue. Please refresh the page and log in again."
        
        # Remove technical stack traces and internal paths
        if any(term in error_lower for term in ["traceback", "stack", "file \"/", "line ", "exception"]):
            return "An internal error occurred. Please try again or contact support."
        
        # Generic fallback for unknown errors
        if len(error_message) > 200 or any(char in error_message for char in ['{', '}', '[', ']', '"detail"']):
            return "An error occurred while processing your request. Please try again."
        
        # If it's already a short, user-friendly message, return as-is
        return error_message
    
    def send_progress_notification(self, message: str, cancel_llm: bool = False):
        """
        Send a progress notification (doesn't cancel LLM processing by default).
        
        Args:
            message: Progress message to send
            cancel_llm: Whether to cancel LLM processing (default: False for progress updates)
        """
        user_id, session_id, _ = self.get_current_user_and_session()
        
        if user_id and session_id:
            self.send_websocket_notification(
                message,
                cancel_llm_processing=cancel_llm,
                session_id=session_id,
                user_id=user_id
            )


# Factory function for easy creation
def create_tool_handler(tool_name: str, suggestions_generator: Optional[Callable] = None) -> ToolResponseHandler:
    """
    Factory function to create a ToolResponseHandler instance.
    
    Args:
        tool_name: Name of the tool/function
        suggestions_generator: Optional function to generate contextual suggestions
        
    Returns:
        ToolResponseHandler instance ready to use
    """
    return ToolResponseHandler(tool_name, suggestions_generator) 
