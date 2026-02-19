#!/usr/bin/env python
"""
Agent pusher utility for the Appliview application.
Provides functions to forcefully push messages to agents for testing and direct interaction.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from google.adk.runners import InMemoryRunner
from google.genai.types import Part, UserContent
import asyncio

logger = logging.getLogger(__name__)

def _get_root_agent():
    """Lazy import of root_agent to avoid circular imports."""
    try:
        from ..root_agent import root_agent
        return root_agent
    except ImportError as e:
        logger.error(f"Failed to import root_agent: {e}")
        raise ImportError("Could not import root_agent. Make sure the module is properly configured.")

def _get_session_service():
    """Lazy import of session_service to avoid circular imports."""
    try:
        from ..session import session_service
        return session_service
    except ImportError as e:
        logger.error(f"Failed to import session_service: {e}")
        raise ImportError("Could not import session_service. Make sure the module is properly configured.")

def _get_websocket_manager():
    """Lazy import of WebSocket manager to avoid circular imports."""
    try:
        from .websocket_manager import manager
        return manager
    except ImportError as e:
        logger.debug(f"WebSocket manager not available: {e}")
        return None

def _get_task_manager():
    """Lazy import of task manager to avoid circular imports."""
    try:
        from .task_manager import get_task_manager
        return get_task_manager()
    except ImportError as e:
        logger.debug(f"Task manager not available: {e}")
        return None

def _extract_response_from_events(events: List[Any]) -> str:
    """
    Extract response text from a list of events.
    
    Args:
        events: List of events from the agent runner
        
    Returns:
        str: The extracted response text
    """
    if not events:
        return "No response received"
    
    # Try to find the best response from events
    response_text = ""
    
    for event in reversed(events):  # Start from the last event
        try:
            # Check if event has content with parts
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text = part.text
                            break
                # Check if content is directly a string
                elif isinstance(event.content, str):
                    response_text = event.content
                    
            # Check if event itself has text
            elif hasattr(event, 'text') and event.text:
                response_text = event.text
                
            # Check if event has a message attribute
            elif hasattr(event, 'message') and event.message:
                if isinstance(event.message, str):
                    response_text = event.message
                elif hasattr(event.message, 'text'):
                    response_text = event.message.text
                    
            # If we found a response, break
            if response_text and response_text.strip():
                break
                
        except Exception as e:
            logger.debug(f"Error extracting from event: {e}")
            continue
    
    # If still no response, try string representation of last event
    if not response_text or not response_text.strip():
        try:
            last_event = events[-1]
            response_text = str(last_event)
            # Clean up the string representation if it's too verbose
            if len(response_text) > 500:
                response_text = response_text[:500] + "..."
        except Exception as e:
            logger.debug(f"Error converting event to string: {e}")
            response_text = "No response received"
    
    return response_text or "No response received"

async def _broadcast_to_websockets(message_data: Dict[str, Any], session_id: Optional[str] = None, cancel_pending_processing: bool = False):
    """
    Broadcast message to connected WebSocket clients.
    
    Args:
        message_data: The message data to broadcast
        session_id: Optional session ID to target specific clients
        cancel_pending_processing: If True, cancels any pending agent processing
    """
    try:
        websocket_manager = _get_websocket_manager()
        if not websocket_manager:
            logger.debug("WebSocket manager not available, skipping broadcast")
            return
        
        # If cancellation is requested, cancel actual LLM processing tasks
        if cancel_pending_processing and session_id:
            task_manager = _get_task_manager()
            if task_manager:
                cancelled_count = task_manager.cancel_session_tasks(
                    session_id, 
                    "Cancelled by WebSocket notification"
                )
                logger.info(f"🛑 Cancelled {cancelled_count} active LLM tasks for session {session_id[:8]}...")
            
            # Send cancellation signal to SPECIFIC SESSION ONLY (not broadcast)
            cancel_data = {
                "type": "processing_cancelled",
                "session_id": session_id,
                "message": "Processing cancelled by agent pusher",
                "source": "agent_pusher_cancellation",
                "timestamp": __import__('time').time(),
                "tasks_cancelled": cancelled_count if task_manager else 0
            }
            await websocket_manager.send_to_session(session_id, cancel_data)
            logger.info(f"📡 Sent processing cancellation signal to session {session_id}")
            
            # Small delay to ensure cancellation is processed
            await asyncio.sleep(0.1)
        
        # Add metadata to indicate this is from agent pusher
        message_with_metadata = {
            **message_data,
            "source": "agent_pusher",
            "timestamp": __import__('time').time(),
            "cancel_pending_processing": cancel_pending_processing,
            "is_interruption": cancel_pending_processing
        }
        
        # Send to SPECIFIC SESSION ONLY - not broadcast!
        if session_id:
            success = await websocket_manager.send_to_session(session_id, message_with_metadata)
            if success:
                logger.info(f"✅ Sent message to session {session_id} (TENANT ISOLATED)")
            else:
                logger.warning(f"⚠️ Failed to send message to session {session_id} - no connection found")
        else:
            logger.warning(f"⚠️ No session_id provided - message not sent (broadcast disabled for security)")
        
    except Exception as e:
        logger.error(f"Error broadcasting to WebSockets: {str(e)}")

def get_current_sessions(app_name: str = "lexedge", user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get current sessions from the session service.
    
    Args:
        app_name: The application name (defaults to "lexedge")
        user_id: Optional user ID to filter sessions
        
    Returns:
        List[Dict[str, Any]]: List of current sessions with metadata
    """
    try:
        session_service = _get_session_service()
        sessions = session_service.list_sessions(app_name=app_name, user_id=user_id)
        if asyncio.iscoroutine(sessions):
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                sessions = asyncio.run(sessions)
            else:
                raise RuntimeError(
                    "get_current_sessions was called from an async context; "
                    "use session_service.list_sessions() with await instead."
                )
        
        session_list = []
        for session in sessions:
            session_list.append({
                "session_id": session.id,
                "user_id": session.user_id,
                "app_name": app_name,
                "state": session.state,
                "created_at": getattr(session, 'created_at', None)
            })
        
        logger.info(f"Found {len(session_list)} sessions for app_name={app_name}, user_id={user_id}")
        return session_list
        
    except Exception as e:
        logger.error(f"Error getting current sessions: {str(e)}")
        return []

async def get_current_sessions_async(app_name: str = "lexedge", user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Async version of get_current_sessions.
    """
    try:
        session_service = _get_session_service()
        sessions = await session_service.list_sessions(app_name=app_name, user_id=user_id)

        session_list = []
        for session in sessions:
            session_list.append({
                "session_id": session.id,
                "user_id": session.user_id,
                "app_name": app_name,
                "state": session.state,
                "created_at": getattr(session, 'created_at', None)
            })

        logger.info(f"Found {len(session_list)} sessions for app_name={app_name}, user_id={user_id}")
        return session_list

    except Exception as e:
        logger.error(f"Error getting current sessions: {str(e)}")
        return []

async def _run_agent_with_cancellation(
    runner,
    user_id: str,
    session_id: str,
    content,
    task_id: str,
    description: str = "Agent processing"
) -> List[Any]:
    """
    Run agent with task cancellation support.
    
    Args:
        runner: The agent runner
        user_id: User ID
        session_id: Session ID  
        content: Message content
        task_id: Unique task ID for tracking
        description: Task description
        
    Returns:
        List of events from agent execution
    """
    try:
        # Get task manager
        task_manager = _get_task_manager()
        
        # Create the agent task
        async def agent_task():
            events = []
            for event in runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            ):
                events.append(event)
                # Check for cancellation periodically
                if asyncio.current_task().cancelled():
                    logger.info(f"🛑 Agent task {task_id} was cancelled")
                    break
            return events
        
        # Create asyncio task
        task = asyncio.create_task(agent_task())
        
        # Register task for cancellation tracking
        if task_manager:
            task_manager.register_task(task_id, session_id, user_id, task, description)
        
        try:
            # Wait for completion or cancellation
            events = await task
            logger.info(f"✅ Agent task {task_id} completed successfully")
            return events
            
        except asyncio.CancelledError:
            logger.info(f"🛑 Agent task {task_id} was cancelled")
            # Return partial results or empty list
            return []
            
        finally:
            # Always unregister the task
            if task_manager:
                task_manager.unregister_task(task_id)
    
    except Exception as e:
        logger.error(f"Error in agent task {task_id}: {str(e)}")
        # Unregister on error
        task_manager = _get_task_manager()
        if task_manager:
            task_manager.unregister_task(task_id)
        raise

async def push_message_to_existing_session(
    message: str,
    session_id: str,
    user_id: str,
    app_name: str = "lexedge",
    agent=None,
    broadcast_to_ui: bool = True,
    cancel_pending_processing: bool = False
) -> Dict[str, Any]:
    """
    Push a message to an existing agent session and return the response.
    
    Args:
        message: The message to send to the agent
        session_id: The existing session ID to use
        user_id: The user ID associated with the session
        app_name: The application name (default: "lexedge")
        agent: The agent to use (if None, uses root_agent)
        broadcast_to_ui: Whether to broadcast messages to connected WebSocket clients
        cancel_pending_processing: If True, cancels any pending agent processing before sending
        
    Returns:
        Dict containing session_id, response, agent_name, success status, etc.
    """
    try:
        # Generate unique task ID for this operation
        task_id = f"push_msg_{uuid.uuid4().hex[:8]}"
        
        # Get the root agent if none provided
        if agent is None:
            agent = _get_root_agent()
        
        # Get session service
        session_service = _get_session_service()
        
        # Get the existing session
        try:
            session = session_service.get_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id
            )
            if asyncio.iscoroutine(session):
                session = await session
            if not session:
                raise ValueError(f"Session {session_id} not found")
            session_existed = True
        except Exception as e:
            logger.warning(f"Session {session_id} not found, will create new one: {str(e)}")
            session = session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                state={
                    "user_name": user_id,
                    "interaction_history": [],
                    "last_query": None,
                    "last_response": None,
                    "is_authenticated": False
                }
            )
            if asyncio.iscoroutine(session):
                session = await session
            session_id = session.id
            session_existed = False
        
        # Broadcast user message to UI first (and cancel existing tasks if requested)
        if broadcast_to_ui:
            user_message_data = {
                "type": "user_message",
                "session_id": session_id,
                "user_id": user_id,
                "message": message,
                "agent_pusher": True
            }
            await _broadcast_to_websockets(user_message_data, session_id, cancel_pending_processing)
        
        # If cancellation was requested, existing tasks should already be cancelled
        # Continue with new agent processing
        
        # Get or create runner
        runner = session_service.get_runner(app_name=app_name)
        if asyncio.iscoroutine(runner):
            runner = await runner
        if not runner:
            runner = session_service.create_runner(app_name=app_name, agent=agent)
            if asyncio.iscoroutine(runner):
                runner = await runner
        
        # Create message content
        content = session_service.create_message(content=message)
        
        # Run the agent with cancellation support
        events = await _run_agent_with_cancellation(
            runner=runner,
            user_id=user_id,
            session_id=session_id,
            content=content,
            task_id=task_id,
            description=f"Push message: {message[:50]}..."
        )
        
        # Extract response from events
        response_text = _extract_response_from_events(events)
        
        logger.info(f"[EXISTING SESSION] Message sent: {message[:100]}...")
        logger.info(f"[EXISTING SESSION] Response received: {response_text[:100]}...")
        
        # Broadcast agent response to UI
        if broadcast_to_ui:
            agent_response_data = {
                "type": "response", 
                "session_id": session_id,
                "response": response_text,
                "agent": agent.name,
                "agent_pusher": True,
                "is_authenticated": session.state.get("is_authenticated", False)
                if session and hasattr(session, "state") else False,
                "cancel_pending_processing": cancel_pending_processing,
                "is_interruption": cancel_pending_processing
            }
            await _broadcast_to_websockets(agent_response_data, session_id, cancel_pending_processing=False)  # Don't cancel again
        
        return {
            "success": True,
            "session_id": session_id,
            "user_id": user_id,
            "response": response_text,
            "agent_name": agent.name,
            "events_count": len(events),
            "session_existed": session_existed,
            "broadcast_to_ui": broadcast_to_ui,
            "cancel_pending_processing": cancel_pending_processing,
            "task_id": task_id
        }
        
    except Exception as e:
        logger.error(f"Error pushing message to existing session: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id,
            "user_id": user_id,
            "agent_name": agent.name if agent else "unknown",
            "broadcast_to_ui": broadcast_to_ui,
            "cancel_pending_processing": cancel_pending_processing
        }

async def push_message_to_agent(
    message: str,
    user_id: str = "test_user",
    app_name: str = "lexedge",
    agent=None,
    session_id: Optional[str] = None,
    broadcast_to_ui: bool = True
) -> Dict[str, Any]:
    """
    Forcefully push a message to an agent and get the response.
    
    Args:
        message: The message to send to the agent
        user_id: The user ID (defaults to "test_user")
        app_name: The application name (defaults to "lexedge")
        agent: The agent to use (defaults to root_agent)
        session_id: Optional existing session ID to use
        broadcast_to_ui: Whether to broadcast to WebSocket clients (defaults to True)
        
    Returns:
        Dict[str, Any]: Response containing the agent's reply and metadata
    """
    try:
        # If session_id is provided, try to use existing session
        if session_id:
            return await push_message_to_existing_session(
                message=message,
                session_id=session_id,
                user_id=user_id,
                app_name=app_name,
                agent=agent,
                broadcast_to_ui=broadcast_to_ui
            )
        
        # Otherwise, use the original InMemoryRunner approach for isolated testing
        if agent is None:
            agent = _get_root_agent()
            
        # Create an InMemoryRunner with the agent
        runner = InMemoryRunner(agent=agent)
        
        # Create a session
        session = runner.session_service.create_session(
            app_name=app_name, 
            user_id=user_id
        )
        if asyncio.iscoroutine(session):
            session = await session
        
        # Create content with the message
        content = UserContent(parts=[Part(text=message)])
        
        # Run the agent and collect events
        events = list(
            runner.run(
                user_id=session.user_id,
                session_id=session.id,
                new_message=content,
            )
        )
        
        # Extract response from events
        response_text = _extract_response_from_events(events)
        
        logger.info(f"[AGENT PUSHER] Message sent: {message[:100]}...")
        logger.info(f"[AGENT PUSHER] Response received: {response_text[:100]}...")
        logger.debug(f"[AGENT PUSHER] Events count: {len(events)}")
        
        return {
            "success": True,
            "message": message,
            "response": response_text,
            "session_id": session.id,
            "user_id": session.user_id,
            "agent_name": agent.name,
            "events_count": len(events),
            "session_existed": False,
            "broadcast_to_ui": broadcast_to_ui
        }
        
    except Exception as e:
        logger.error(f"Error pushing message to agent: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": message,
            "response": None
        }

async def batch_push_messages(
    messages: List[str],
    user_id: str = "test_user", 
    app_name: str = "lexedge",
    agent=None,
    session_id: Optional[str] = None,
    broadcast_to_ui: bool = True
) -> List[Dict[str, Any]]:
    """
    Push multiple messages to an agent in sequence.
    
    Args:
        messages: List of messages to send
        user_id: The user ID (defaults to "test_user")
        app_name: The application name (defaults to "lexedge")
        agent: The agent to use (defaults to root_agent)
        session_id: Optional existing session ID to use
        broadcast_to_ui: Whether to broadcast to WebSocket clients (defaults to True)
        
    Returns:
        List[Dict[str, Any]]: List of responses for each message
    """
    results = []
    current_session_id = session_id
    
    try:
        # Process each message
        for i, message in enumerate(messages):
            try:
                # For the first message, use the provided session_id or create new
                # For subsequent messages, use the session_id from the first result
                result = await push_message_to_agent(
                    message=message,
                    user_id=user_id,
                    app_name=app_name,
                    agent=agent,
                    session_id=current_session_id,
                    broadcast_to_ui=broadcast_to_ui
                )
                
                # If this was successful and we don't have a session_id yet, use this one
                if result.get("success") and not current_session_id:
                    current_session_id = result["session_id"]
                
                # Add message index
                result["message_index"] = i
                
                logger.info(f"[BATCH PUSHER] Message {i+1}/{len(messages)} processed successfully")
                
            except Exception as e:
                result = {
                    "success": False,
                    "message_index": i,
                    "message": message,
                    "error": str(e),
                    "response": None
                }
                logger.error(f"Error processing message {i+1}: {str(e)}")
            
            results.append(result)
        
        return results
        
    except Exception as e:
        logger.error(f"Error in batch push messages: {str(e)}")
        # Return error results for all messages
        return [
            {
                "success": False,
                "message_index": i,
                "message": message,
                "error": str(e),
                "response": None
            }
            for i, message in enumerate(messages)
        ]

async def create_test_session_with_messages(
    messages: List[str],
    user_id: str = "test_user",
    app_name: str = "lexedge", 
    agent=None,
    session_id: Optional[str] = None,
    broadcast_to_ui: bool = True
) -> Dict[str, Any]:
    """
    Create a test session and push multiple messages to build conversation context.
    
    Args:
        messages: List of messages to send in sequence
        user_id: The user ID (defaults to "test_user")
        app_name: The application name (defaults to "lexedge")
        agent: The agent to use (defaults to root_agent)
        session_id: Optional existing session ID to use
        broadcast_to_ui: Whether to broadcast to WebSocket clients (defaults to True)
        
    Returns:
        Dict[str, Any]: Session information and all responses
    """
    try:
        # Push all messages in batch
        results = await batch_push_messages(messages, user_id, app_name, agent, session_id, broadcast_to_ui)
        
        # Extract session information from first successful result
        session_info = None
        for result in results:
            if result.get("success"):
                session_info = {
                    "session_id": result["session_id"],
                    "user_id": result["user_id"],
                    "agent_name": result["agent_name"]
                }
                break
        
        return {
            "success": True,
            "session_info": session_info,
            "messages_sent": len(messages),
            "results": results,
            "successful_messages": len([r for r in results if r.get("success")]),
            "failed_messages": len([r for r in results if not r.get("success")])
        }
        
    except Exception as e:
        logger.error(f"Error creating test session: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "messages_sent": len(messages),
            "results": []
        } 
