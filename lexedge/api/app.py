#!/usr/bin/env python
# app.py - FastAPI application for Appliview agent system

import os
import json
import asyncio
import uuid
import logging
import time
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Header, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from pydantic import BaseModel, EmailStr

from fastapi import FastAPI, Depends, HTTPException, Header, Query, Body, WebSocket, WebSocketDisconnect

import pathlib
import traceback

from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.genai import types

from lexedge.agent_runner import run_agent, stream_agent_response
from lexedge.session import session_service
from lexedge.session.firewall import session_firewall


from lexedge.main_agent import root_agent
from lexedge.utils.audio_transcription import transcribe_audio

# Utility function for comprehensive server cleanup
async def perform_comprehensive_cleanup(context: str = "manual"):
    """
    Perform comprehensive cleanup of all server state.
    
    Args:
        context: String describing when this cleanup is being performed
    """
    logger.info(f"🧹 Performing comprehensive cleanup ({context})")
    
    # 1. Clear WebSocket connections
    try:
        manager.active_connections = {}
        manager.connection_timestamps = {}
        logger.info(f"✅ [{context.upper()}] Cleared WebSocket connections")
    except Exception as e:
        logger.error(f"❌ [{context.upper()}] Failed to clear WebSocket connections: {str(e)}")
    
    # 2. Cancel all active tasks
    try:
        from lexedge.utils.task_manager import get_task_manager
        task_manager = get_task_manager()
        
        all_active_tasks = task_manager.get_active_tasks()
        if all_active_tasks:
            cancelled_count = 0
            for task_id in list(all_active_tasks.keys()):
                if task_manager.cancel_task(task_id, f"{context} - cancelling all tasks"):
                    cancelled_count += 1
            
            cleanup_count = task_manager.cleanup_completed_tasks()
            logger.info(f"✅ [{context.upper()}] Cancelled {cancelled_count} tasks, cleaned up {cleanup_count} references")
        else:
            logger.info(f"✅ [{context.upper()}] No active tasks to cancel")
            
    except Exception as e:
        logger.error(f"❌ [{context.upper()}] Failed to cancel active tasks: {str(e)}")
    
    # 3. Clear all sessions from database
    try:
        session_count = await session_service.clear_all_sessions()
        logger.info(f"✅ [{context.upper()}] Cleared {session_count} sessions from database")
    except Exception as e:
        logger.error(f"❌ [{context.upper()}] Failed to clear sessions: {str(e)}")
    
    # 4. Reset session firewall
    try:
        session_firewall.reset()
        logger.info(f"✅ [{context.upper()}] Reset session firewall")
    except Exception as e:
        logger.error(f"❌ [{context.upper()}] Failed to reset session firewall: {str(e)}")
    
    # 5. Clear any cached data in tools/utilities
    try:
        # Clear suggestion cache if it exists (from tools.py)
        logger.info(f"✅ [{context.upper()}] Reset cached data")
    except Exception as e:
        logger.error(f"❌ [{context.upper()}] Failed to clear cached data: {str(e)}")
    
    logger.info(f"🎯 [{context.upper()}] Comprehensive cleanup completed!")

# Set up logger
logger = logging.getLogger(__name__)

# Get the directory containing this file
CURRENT_DIR = pathlib.Path(__file__).parent.resolve()
STATIC_DIR = CURRENT_DIR / "static"

# Create FastAPI app
app = FastAPI(
    title="LexEdge Legal AI API",
    description="API for interacting with the LexEdge Legal AI agent system through HTTP and WebSockets",
    version="1.0.0"
)

# Include HTMX web routes
try:
    from lexedge.web.routes import router as web_router
    app.include_router(web_router)
except ImportError as e:
    logger.warning(f"Web routes not available: {e}")

# FastAPI startup and shutdown events for comprehensive cleanup
@app.on_event("startup")
async def startup_event():
    """FastAPI startup event - ensures cleanup runs even if server started directly with uvicorn"""
    logger.info("🔄 FastAPI startup event triggered")
    await perform_comprehensive_cleanup("startup event")
    session_firewall.start_cleanup_task()

@app.on_event("shutdown")
async def shutdown_event():
    """FastAPI shutdown event - cleanup on server shutdown"""
    logger.info("🛑 FastAPI shutdown event triggered")
    
    try:
        # Additional shutdown-specific cleanup
        from lexedge.utils.task_manager import get_task_manager
        task_manager = get_task_manager()
        
        all_active_tasks = task_manager.get_active_tasks()
        if all_active_tasks:
            cancelled_count = 0
            for task_id in list(all_active_tasks.keys()):
                if task_manager.cancel_task(task_id, "Server shutdown - cancelling all tasks"):
                    cancelled_count += 1
            logger.info(f"✅ [SHUTDOWN EVENT] Cancelled {cancelled_count} tasks")
        
        # Shutdown session firewall properly
        session_firewall.shutdown()
        logger.info("✅ [SHUTDOWN EVENT] Session firewall shutdown")
        
    except Exception as e:
        logger.error(f"❌ [SHUTDOWN EVENT] Error during shutdown cleanup: {str(e)}")
    
    # Run general cleanup too
    perform_comprehensive_cleanup("shutdown event")

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change this to your specific frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add explicit OPTIONS handler for preflight requests
@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    # Set proper CORS headers for preflight requests
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
        "Access-Control-Max-Age": "3600"
    }
    
    return JSONResponse(
        status_code=200,
        content={"detail": "OK"},
        headers=headers
    )

# Audio transcription proxy (convert to WAV + retry)
@app.post("/audio/transcribe")
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        result = transcribe_audio(
            audio_bytes,
            filename=file.filename or "audio.webm",
            content_type=file.content_type
        )
        return JSONResponse(status_code=200, content=result)
    except Exception as exc:
        logger.error(f"Audio transcription failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

# Mount static files
os.makedirs(STATIC_DIR, exist_ok=True)  # Ensure static directory exists
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ----- Pydantic Models for API -----

class AgentQuery(BaseModel):
    """Model for agent query requests"""
    user_id: str = Field(..., description="User's unique identifier")
    query: str = Field(..., description="Query for the agent")
    session_id: Optional[str] = Field(None, description="Optional session ID. If not provided, a new session will be created")
    app_name: str = Field("lexedge", description="Application name")

class SessionCreate(BaseModel):
    """Model for creating a new session"""
    user_id: str = Field(..., description="User's unique identifier")
    app_name: str = Field("lexedge", description="Application name")
    initial_state: Optional[Dict[str, Any]] = Field(None, description="Initial session state")

class SessionResponse(BaseModel):
    """Model for session responses"""
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    app_name: str = Field(..., description="Application name")
    state: Dict[str, Any] = Field(..., description="Current session state")
    last_update_time: float = Field(..., description="Last update timestamp")

class AgentResponse(BaseModel):
    """Model for agent responses"""
    session_id: str = Field(..., description="Session ID")
    response: Optional[str] = Field(None, description="Agent response")
    formatted_response: Optional[str] = Field(None, description="HTML formatted response for rich display")
    agent: Optional[str] = Field(None, description="Agent that generated the response")
    is_authenticated: Optional[bool] = Field(False, description="Whether the user is authenticated")
    user_name: Optional[str] = Field("", description="User's name")
    role: Optional[str] = Field("", description="User's role")
    action_suggestions: Optional[Dict[str, Any]] = Field(None, description="Contextual action suggestions for the client")
    login_failed: Optional[bool] = Field(False, description="Whether the last login attempt failed")
    login_error: Optional[str] = Field(None, description="Login error message if any")
    login_error_code: Optional[int] = Field(0, description="Login error code")
    login_error_type: Optional[str] = Field("", description="Type of login error")

class StreamQuery(BaseModel):
    """Model for streaming agent query requests"""
    user_id: str = Field(..., description="User's unique identifier")
    query: str = Field(..., description="Query for the agent")
    session_id: Optional[str] = Field(None, description="Optional session ID. If not provided, a new session will be created")
    app_name: str = Field("lexedge", description="Application name")

class TokenValidationRequest(BaseModel):
    tenant_id: str
    token: str

class TokenValidationResponse(BaseModel):
    status: str
    data: Dict[str, Any]

class TokenLoginRequest(BaseModel):
    user_id: str
    tenant_id: str
    tenant_admin_id: str
    role_id: str
    token: str

class LoginResponse(BaseModel):
    tenant_id: str
    token: str
    name: str
    email: str
    role: str
    tenant_name: str
    is_admin: bool
    user_id: str = None
    tenant_code: str = None
    tenant_admin_id: str = None
    session_id: str = None
    welcome_message: str = None
    formatted_welcome: str = None
    capabilities_overview: Dict[str, Any] = None
    quick_start_suggestions: List[Dict[str, Any]] = None

@app.post("/api/v1/jobs/validate-token", response_model=TokenValidationResponse)
async def validate_token(request: TokenValidationRequest, x_tenant_id: str = Header(...), x_tenant_token: str = Header(...)):
    # Simple validation for demonstration purposes
    # In a real application, you would validate the token against a database or auth service
    if x_tenant_id == "test" and len(x_tenant_token) > 10: # Basic check
        return TokenValidationResponse(
            status="success",
            data={
                "name": "test_user",
                "tenant_id": x_tenant_id,
                "tenant_name": "Test Tenant",
                "role": "admin",
                "is_admin": True,
            }
        )
    else:
        raise HTTPException(status_code=401, detail="Invalid tenant credentials")

# Token-based login endpoint
@app.post("/token-login", response_model=LoginResponse, summary="Token-based Login", tags=["Authentication"])
async def token_login(login_data: TokenLoginRequest = Body(...)):
    """
    Authenticate a user with a pre-validated token using the validate-token endpoint.
    
    This endpoint validates the token against the backend service and returns authentication 
    information including a session_id with the actual tenant information.
    """
    try:
        # Import the token_login function from tools to validate the token
        from lexedge.tools.auth import token_login 
        
        # Validate the token using the backend validation service
        validation_result = token_login(
            user_id=login_data.user_id,
            tenant_id=login_data.tenant_id,
            tenant_admin_id=login_data.tenant_admin_id,
            role_id=login_data.role_id,
            token=login_data.token
        )
        
        logger.info(f"Token validation result: {validation_result}")
        
        # Check if validation was successful
        if validation_result.get("status") != "success":
            error_message = validation_result.get("error_message", "Token validation failed")
            error_code = validation_result.get("error_code", 401)
            logger.error(f"Token validation failed: {error_message}")
            raise HTTPException(
                status_code=error_code,
                detail=error_message
            )
        
        # Extract validated data
        validated_data = validation_result.get("data", {})
        user_name = validated_data.get("name", "Unknown User")  # Extract actual user name
        tenant_name = validated_data.get("tenant_name", "Unknown Tenant")
        validated_tenant_id = validated_data.get("tenant_id", login_data.tenant_id)
        token_expiry = validated_data.get("token_expiry")
        
        # Extract welcome message data
        welcome_message = validated_data.get("welcome_message", "")
        formatted_welcome = validated_data.get("formatted_welcome", "")
        capabilities_overview = validated_data.get("capabilities_overview", {})
        quick_start_suggestions = validated_data.get("quick_start_suggestions", [])
        
        # Create token login data structure
        token_login_data = {
            "user_id": login_data.user_id,
            "tenant_id": validated_tenant_id,
            "tenant_admin_id": login_data.tenant_admin_id,
            "role_id": login_data.role_id,
            "token": login_data.token,
            "token_expiry": token_expiry
        }
        
        # Create a new session with validated authentication data
        initial_state = {
            "user_name": user_name,  # Use actual user name from validation
            "user_id": login_data.user_id,
            "is_authenticated": True,
            "token": login_data.token,
            "tenant_id": validated_tenant_id,
            "tenant_name": tenant_name,  # Store the actual tenant name from validation
            "role": "user",  # Default role
            "is_admin": False,  # Default to non-admin
            "interaction_history": [],
            "last_query": None,
            "last_response": None,
            "token_login_data": token_login_data,  # Store token login data for reference
            "token_expiry": token_expiry,
            "welcome_message": welcome_message,  # Store welcome message
            "formatted_welcome": formatted_welcome,  # Store formatted welcome
            "capabilities_overview": capabilities_overview,  # Store capabilities
            "show_welcome_on_connect": True,  # Flag to show welcome message on WebSocket connect
            "quick_start_suggestions": quick_start_suggestions
        }
        
        logger.info(f"Creating session with validated user: {user_name} from tenant: {tenant_name}")
        
        # Create new session
        session = await session_service.create_session(
            app_name="lexedge",
            user_id=login_data.user_id,
            state=initial_state
        )
        session_id = session.id
        logger.info(f"Created new token-based session {session_id} for user {login_data.user_id} with user name {user_name}")
        
        # Return login response with validated data
        return LoginResponse(
            tenant_id=validated_tenant_id,
            token=login_data.token,
            name=user_name,  # Use actual user name from validation
            email=validated_data.get("email", f"user@{validated_tenant_id}.com"),  # Default email format
            role=validated_data.get("role", "user"),  # Default role
            tenant_name=tenant_name,  # Actual tenant name from validation
            is_admin=validated_data.get("is_admin", False),  # Default to non-admin
            user_id=login_data.user_id,
            tenant_code=validated_tenant_id,
            tenant_admin_id=login_data.tenant_admin_id,
            session_id=session_id,
            welcome_message=welcome_message,
            formatted_welcome=formatted_welcome,
            capabilities_overview=capabilities_overview,
            quick_start_suggestions=quick_start_suggestions
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like validation failures)
        raise
    except Exception as e:
        logger.error(f"Error during token-based login: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Token login failed: {str(e)}"
        )

# ----- WebSocket Connection Manager -----

from lexedge.utils.websocket_manager import manager
# manager is now imported from lexedge.utils.websocket_manager

# ----- HTTP Routes -----

@app.get("/")
async def root():
    """Root endpoint with WebSocket demo client"""
    return {"message": "Welcome to Appliview Agent API", "version": "1.0.0", "status": "running"}

@app.post("/sessions", response_model=SessionResponse)
async def create_session(session_data: SessionCreate):
    """Create a new session"""
    try:
        # Use default initial state if not provided
        initial_state = session_data.initial_state or {
            "user_name": session_data.user_id,
            "interaction_history": [],
            "last_query": None,
            "last_response": None
        }
        
        # Create session
        session = await session_service.create_session(
            app_name=session_data.app_name,
            user_id=session_data.user_id,
            state=initial_state
        )
        
        # Return session information
        return SessionResponse(
            session_id=session.id,
            user_id=session_data.user_id,
            app_name=session_data.app_name,
            state=session.state,
            last_update_time=session.last_update_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, user_id: str, app_name: str = "lexedge"):
    """Get session information"""
    try:
        session = await session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        return SessionResponse(
            session_id=session.id,
            user_id=user_id,
            app_name=app_name,
            state=session.state,
            last_update_time=session.last_update_time
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")

@app.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(user_id: Optional[str] = None, app_name: Optional[str] = "lexedge"):
    """List sessions"""
    try:
        sessions = await session_service.list_sessions(
            user_id=user_id,
            app_name=app_name
        )
        
        return [
            SessionResponse(
                session_id=session.id,
                user_id=session.user_id,
                app_name=session.app_name,
                state=session.state,
                last_update_time=session.last_update_time
            )
            for session in sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

@app.post("/agent/query", response_model=AgentResponse)
async def query_agent(query_data: AgentQuery):
    """Query the agent with HTTP"""
    try:
        result = await run_agent(
            user_id=query_data.user_id,
            query=query_data.query,
            session_id=query_data.session_id,
            app_name=query_data.app_name
        )
        
        # Return only what's in the AgentResponse model
        return AgentResponse(
            session_id=result["session_id"],
            response=result["response"],
            formatted_response=result.get("formatted_response"),
            agent=result["agent"],
            is_authenticated=result.get("is_authenticated", False),
            user_name=result.get("user_name", ""),
            role=result.get("role", ""),
            action_suggestions=result.get("action_suggestions", {}),
            login_failed=result.get("login_failed", False),
            login_error=result.get("login_error"),
            login_error_code=result.get("login_error_code", 0),
            login_error_type=result.get("login_error_type", "")
        )
    except Exception as e:
        logger.error(f"Agent query failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Agent query failed: {str(e)}")

@app.post("/agent/stream")
async def stream_agent(query_data: StreamQuery):
    """
    Stream agent responses using Server-Sent Events (SSE).
    
    This endpoint is designed for streaming real-time notifications and alerts
    from the Appliview agent.
    """
    async def event_generator():
        try:
            # Start with a connection established message
            yield "data: " + json.dumps({"type": "connection_established"}) + "\n\n"
            
            # Stream responses from the agent
            async for chunk in stream_agent_response(
                user_id=query_data.user_id,
                query=query_data.query,
                session_id=query_data.session_id,
                app_name=query_data.app_name
            ):
                # Format as SSE event
                yield "data: " + json.dumps(chunk) + "\n\n"
                
                # If this is the final response in a stream, send a completion event
                if chunk.get("stream_complete", False):
                    yield "data: " + json.dumps({"type": "stream_complete"}) + "\n\n"
                    
            # Add a final event to indicate the stream is done
            yield "data: " + json.dumps({"type": "stream_ended"}) + "\n\n"
            
        except Exception as e:
            logger.error(f"Error during streaming: {str(e)}")
            logger.error(traceback.format_exc())
            # Send error as SSE event
            yield "data: " + json.dumps({
                "type": "error",
                "error": str(e)
            }) + "\n\n"
    
    # Return streaming response with proper headers for SSE
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user_id: str, app_name: str = "lexedge"):
    """Delete a session"""
    try:
        # Delete from session service
        await session_service.delete_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        # Unregister from session firewall
        session_firewall.unregister_session(session_id)
        
        return {"message": f"Session {session_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Failed to delete session: {str(e)}")

@app.post("/logout")
async def logout(session_id: str, user_id: str, app_name: str = "lexedge"):
    """Logout a user and invalidate their session, clearing all session data"""
    try:
        # Get the session to verify it exists
        try:
            session = await session_service.get_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")
        
        # Process a logout request through the agent to clear all data
        try:
            result = await run_agent(
                user_id=user_id,
                query="logout",
                session_id=session_id,
                app_name=app_name
            )
            logger.info(f"Logout agent completed: {result.get('response', 'No response')}")
        except Exception as e:
            logger.warning(f"Error running logout agent command: {str(e)}")
        
        # Unregister from session firewall first
        session_firewall.unregister_session(session_id)
        
        # Delete the session entirely from the database
        try:
            await session_service.delete_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id
            )
            logger.info(f"Successfully deleted session {session_id} from database")
        except Exception as e:
            logger.error(f"Error deleting session from database: {str(e)}")
        
        # If there is an active WebSocket mapped to this session, disconnect it to avoid stale connections
        try:
            if session_id in manager.session_connections:
                conn_id = manager.session_connections.get(session_id)
                logger.info(f"Disconnecting WebSocket connection {conn_id} for logged out session {session_id}")
                manager.disconnect(conn_id)
        except Exception as disconnect_err:
            logger.warning(f"Failed to disconnect WebSocket for session {session_id}: {disconnect_err}")
        
        return {
            "message": f"User {user_id} logged out successfully and all session data cleared", 
            "success": True,
            "session_cleared": True
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to logout: {str(e)}")

@app.get("/chat-history/{session_id}")
async def get_chat_history(session_id: str, user_id: str, app_name: str = "lexedge", auth_user_name: Optional[str] = None):
    """Get the chat history for a specific session"""
    try:
        logger.info(f"Fetching chat history for session: {session_id}, user: {user_id}, auth_user: {auth_user_name}")
        
        # Try to get the session first by session ID and user ID
        session = None
        try:
            session = await session_service.get_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id
            )
            logger.info(f"Found session by direct user_id and session_id")
        except Exception as direct_error:
            logger.warning(f"Couldn't get session directly: {str(direct_error)}")
            
            # If direct lookup fails and we have auth_user_name, try to find by looking at all sessions
            if auth_user_name:
                logger.info(f"Trying to find session by auth_user_name: {auth_user_name}")
                try:
                    # Get all sessions
                    all_sessions = await session_service.list_sessions(app_name=app_name)
                    
                    # Look for the specific session ID
                    for s in all_sessions:
                        if s.id == session_id:
                            # Found the session
                            session = s
                            logger.info(f"Found session {session_id} by scanning all sessions")
                            break
                except Exception as list_error:
                    logger.error(f"Error listing all sessions: {str(list_error)}")
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found")
        
        # Don't filter by auth_user_name if provided
        # This allows viewing any session as long as they have the session ID
        
        # Extract conversation history from session state
        conversation_history = []
        if session.state and "interaction_history" in session.state:
            # Get the conversation history
            history = session.state["interaction_history"]
            
            # Filter out messages with empty content
            conversation_history = [
                msg for msg in history 
                if msg.get("content") and msg.get("content").strip()
            ]
            
            # Log the filtering results
            if len(history) != len(conversation_history):
                logger.info(f"Filtered out {len(history) - len(conversation_history)} empty messages from chat history")
        
        return {
            "session_id": session.id,
            "user_id": session.user_id,
            "auth_info": {
                "is_authenticated": session.state.get("is_authenticated", False),
                "user_name": session.state.get("user_name", ""),
                "role": session.state.get("role", "")
            },
            "conversation_history": conversation_history
        }
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        logger.error(f"Failed to retrieve chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {str(e)}")

@app.get("/user-chat-history")
async def get_user_chat_history(user_id: str, app_name: str = "lexedge", auth_user_name: Optional[str] = None):
    """Get all chat sessions and their history for a user
    
    This can find sessions by either:
    1. The client-side user_id (like demo_user_XXX)
    2. The authenticated user_name in session state (after login)
    """
    try:
        logger.info(f"Fetching chat history for user_id: {user_id}, auth_user_name: {auth_user_name}, app: {app_name}")
        
        # Directly get sessions for this user_id from the database
        logger.debug(f"Fetching sessions directly by user_id={user_id}")
        sessions = await session_service.list_sessions(app_name=app_name, user_id=user_id)
        logger.info(f"Found {len(sessions)} sessions directly matching user_id={user_id}")
        
        # If no sessions found, try to get all sessions and filter manually
        if not sessions:
            logger.debug("No sessions found by direct query, trying manual filtering")
            all_sessions = await session_service.list_sessions(app_name=app_name)
            logger.info(f"Found {len(all_sessions)} total sessions across all users")
            
            # Filter manually
            for session in all_sessions:
                if session.user_id == user_id:
                    sessions.append(session)
        
        if not sessions:
            logger.warning(f"No sessions found for user {user_id}")
            return {
                "client_user_id": user_id,
                "authenticated_user_name": auth_user_name,
                "sessions": []
            }
        
        logger.info(f"Found {len(sessions)} total sessions for user {user_id}")
        
        # Process all valid sessions
        sessions_history = []
        for session in sessions:
            try:
                # Skip sessions with None state
                if not session or not hasattr(session, 'state') or session.state is None:
                    logger.warning(f"Skipping invalid session {getattr(session, 'id', 'unknown')}, missing or invalid state")
                    continue
                
                # Get the raw conversation history
                conversation_history = []
                if "interaction_history" in session.state:
                    raw_history = session.state["interaction_history"]
                    
                    # Filter out messages with empty content
                    conversation_history = [
                        msg for msg in raw_history 
                        if msg.get("content") and msg.get("content").strip()
                    ]
                    
                    # Log the filtering results
                    if len(raw_history) != len(conversation_history):
                        logger.info(f"Filtered out {len(raw_history) - len(conversation_history)} empty messages from session {session.id}")
                
                # Get authentication info
                is_authenticated = session.state.get("is_authenticated", False)
                session_user_name = session.state.get("user_name", "")
                
                auth_info = {
                    "is_authenticated": is_authenticated,
                    "user_name": session_user_name,
                    "role": session.state.get("role", "")
                }
                
                # Add the session to the response
                logger.info(f"Adding session {session.id} to history response with {len(conversation_history)} messages")
                
                sessions_history.append({
                    "session_id": session.id,
                    "client_user_id": session.user_id,
                    "last_update_time": session.last_update_time,
                    "conversation_history": conversation_history,
                    "auth_info": auth_info
                })
            except Exception as e:
                # Log error but continue processing other sessions
                logger.error(f"Error processing session {getattr(session, 'id', 'unknown')}: {str(e)}")
                continue
        
        # Sort sessions by last update time (newest first)
        sessions_history.sort(key=lambda x: x["last_update_time"], reverse=True)
        
        logger.info(f"Returning {len(sessions_history)} sessions in history response")
        
        return {
            "client_user_id": user_id,
            "authenticated_user_name": auth_user_name,
            "sessions": sessions_history
        }
    except Exception as e:
        logger.error(f"Failed to retrieve user chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user chat history: {str(e)}")

# Add a dedicated route for the WebSocket demo client
@app.get("/demo", response_class=HTMLResponse)
async def demo():
    """WebSocket demo client"""
    # Check if index.html exists
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        with open(index_path, "r") as f:
            html_content = f.read()
        return html_content
    else:
        return "<html><body><h1>Demo client not found</h1></body></html>"

# Add an explicit logout endpoint
@app.post("/agent/logout", response_model=AgentResponse)
async def logout_user(query_data: AgentQuery):
    """Explicitly log out a user by clearing their authentication state and session data"""
    try:
        # Force query to be "logout" regardless of what was sent
        result = await run_agent(
            user_id=query_data.user_id,
            query="logout",
            session_id=query_data.session_id,
            app_name=query_data.app_name
        )
        
        # Additional cleanup: unregister from session firewall
        if query_data.session_id:
            session_firewall.unregister_session(query_data.session_id)
            logger.info(f"Unregistered session {query_data.session_id} from firewall during agent logout")
        
        logout_message = "You have been successfully logged out and all session data has been cleared."
        # Format the logout message with the same formatting function
        formatted_logout = "<p>You have been successfully logged out and all session data has been cleared.</p>"
        
        return AgentResponse(
            session_id=result["session_id"],
            response=logout_message,
            formatted_response=formatted_logout,
            agent="lexedge_manager",
            is_authenticated=False,
            user_name="",
            role="",
            action_suggestions=result.get("action_suggestions", {}),
            login_failed=result.get("login_failed", False),
            login_error=result.get("login_error"),
            login_error_code=result.get("login_error_code", 0),
            login_error_type=result.get("login_error_type", "")
        )
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenLoginRequest(BaseModel):
    user_id: str
    tenant_id: str
    tenant_admin_id: str
    role_id: str
    token: str

class LoginResponse(BaseModel):
    tenant_id: str
    token: str
    name: str
    email: str
    role: str
    tenant_name: str
    is_admin: bool
    user_id: str = None
    tenant_code: str = None
    tenant_admin_id: str = None
    session_id: str = None
    welcome_message: str = None
    formatted_welcome: str = None
    capabilities_overview: Dict[str, Any] = None
    quick_start_suggestions: List[Dict[str, Any]] = None
    

TENANT_ID = "test-tenant-123"
API_TOKEN = "test-token-abc-xyz-789"

# Hardcoded login credentials
TEST_EMAIL = "user@example.com"
TEST_PASSWORD = "password123"
TEST_NAME = "Test User"
# New login endpoint
@app.post("/login", response_model=LoginResponse, summary="User Login", tags=["Authentication"])
async def login(login_data: LoginRequest = Body(...)):
    """
    Authenticate a user with email and password.
    
    This endpoint accepts email and password and returns:
    - tenant_id: The tenant identifier
    - token: Authentication token for subsequent API calls
    - name: User's full name
    - email: User's email address
    
    For testing, use these credentials:
    - Email: user@example.com
    - Password: password123
    """
    if login_data.email != TEST_EMAIL or login_data.password != TEST_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    return LoginResponse(
        tenant_id=TENANT_ID,
        token=API_TOKEN,
        name=TEST_NAME,
        email=TEST_EMAIL,
        role="admin",
        tenant_name="Test Tenant",
        is_admin=True,
        user_id="123",
        tenant_code="123",
        tenant_admin_id="123"
    )

@app.post("/direct-login", response_model=LoginResponse, summary="User Direct Login", tags=["Authentication"])
async def direct_login(login_data: LoginRequest = Body(...)):
    """
    Authenticate a user with email and password and create a session automatically.
    
    This endpoint accepts email and password and returns:
    - tenant_id: The tenant identifier
    - token: Authentication token for subsequent API calls
    - name: User's full name
    - email: User's email address
    - session_id: A new or existing session ID for the authenticated user
    
    For testing, use these credentials:
    - Email: user@example.com
    - Password: password123
    """
    if login_data.email != TEST_EMAIL or login_data.password != TEST_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Use a consistent user_id format - match what the frontend is sending to WebSocket
    # Important: This must exactly match the format used by the client WebSocket
    user_id = f"user_{login_data.email.replace('@', '_').replace('.', '_')}"
    logger.info(f"Login: Using consistent user_id: {user_id}")
    
    # Create a new session or get existing one for the user
    try:
        # Try to get existing sessions for this user
        sessions = await session_service.list_sessions(
            user_id=user_id,
            app_name="lexedge"
        )
        
        # Get the most recent session or create a new one
        if sessions:
            # Find the most recently updated session
            session = max(sessions, key=lambda s: s.last_update_time)
            session_id = session.id
            
            # Update the session state to ensure authentication info is present
            session.state.update({
                "user_name": TEST_NAME,
                "user_id": user_id,
                "is_authenticated": True,
                "token": API_TOKEN,
                "tenant_id": TENANT_ID,
                "tenant_name": "Test Tenant",
                "role": "admin",
                "is_admin": True
            })
            
            # Save the updated session
            await session_service.create_session(
                app_name="lexedge",
                user_id=user_id,
                session_id=session_id,
                state=session.state
            )
            
            # Record activity to prevent session expiration
            session_firewall.record_session_activity(session_id)          
            logger.info(f"Using existing session {session_id} for user {user_id} (updated state)")
        else:
            # Create a new session with authentication data
            initial_state = {
                "user_name": TEST_NAME,
                "user_id": user_id,
                "is_authenticated": True,
                "token": API_TOKEN,
                "tenant_id": TENANT_ID,
                "tenant_name": "Test Tenant",
                "role": "admin",
                "is_admin": True,
                "interaction_history": [],
                "last_query": None,
                "last_response": None
            }
            
            session = await session_service.create_session(
                app_name="lexedge",
                user_id=user_id,
                state=initial_state
            )
            session_id = session.id
            logger.info(f"Created new session {session_id} for user {user_id}")
        
        # Return login response with session_id
        return LoginResponse(
            tenant_id=TENANT_ID,
            token=API_TOKEN,
            name=TEST_NAME,
            email=TEST_EMAIL,
            role="admin",
            tenant_name="Test Tenant",
            is_admin=True,
            user_id=user_id,  # Return the exact same user_id format
            tenant_code="123",
            tenant_admin_id="123",
            session_id=session_id  # Add session_id to response
        )
    except Exception as e:
        logger.error(f"Error creating session for authenticated user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Session creation failed: {str(e)}"
        )

# Session validation endpoint
@app.get("/validate-session/{session_id}", summary="Validate Session", tags=["Authentication"])
async def validate_session(session_id: str):
    """
    Check if a session is still valid.
    Client should call this on page load before trying to connect WebSocket.
    """
    try:
        # Try to find the session
        sessions = await session_service.list_sessions(app_name="lexedge")
        session_exists = any(s.id == session_id for s in sessions)
        
        if session_exists:
            return {"valid": True, "session_id": session_id}
        else:
            return {"valid": False, "session_id": session_id, "error": "Session not found or expired"}
    except Exception as e:
        logger.error(f"Error validating session: {str(e)}")
        return {"valid": False, "session_id": session_id, "error": str(e)}

# Token-based login endpoint
@app.post("/token-login", response_model=LoginResponse, summary="Token-based Login", tags=["Authentication"])
async def token_login(login_data: TokenLoginRequest = Body(...)):
    """
    Authenticate a user with a pre-validated token using the validate-token endpoint.
    
    This endpoint validates the token against the backend service and returns authentication 
    information including a session_id with the actual tenant information.
    """
    try:
        # Import the token_login function from tools to validate the token
        from lexedge.tools import token_login 
        
        # Validate the token using the backend validation service
        validation_result = token_login(
            user_id=login_data.user_id,
            tenant_id=login_data.tenant_id,
            tenant_admin_id=login_data.tenant_admin_id,
            role_id=login_data.role_id,
            token=login_data.token
        )
        
        logger.info(f"Token validation result: {validation_result}")
        
        # Check if validation was successful
        if validation_result.get("status") != "success":
            error_message = validation_result.get("error_message", "Token validation failed")
            error_code = validation_result.get("error_code", 401)
            logger.error(f"Token validation failed: {error_message}")
            raise HTTPException(
                status_code=error_code,
                detail=error_message
            )
        
        # Extract validated data
        validated_data = validation_result.get("data", {})
        user_name = validated_data.get("name", "Unknown User")  # Extract actual user name
        tenant_name = validated_data.get("tenant_name", "Unknown Tenant")
        validated_tenant_id = validated_data.get("tenant_id", login_data.tenant_id)
        token_expiry = validated_data.get("token_expiry")
        
        # Extract welcome message data
        welcome_message = validated_data.get("welcome_message", "")
        formatted_welcome = validated_data.get("formatted_welcome", "")
        capabilities_overview = validated_data.get("capabilities_overview", {})
        quick_start_suggestions = validated_data.get("quick_start_suggestions", [])
        
        # Create token login data structure
        token_login_data = {
            "user_id": login_data.user_id,
            "tenant_id": validated_tenant_id,
            "tenant_admin_id": login_data.tenant_admin_id,
            "role_id": login_data.role_id,
            "token": login_data.token,
            "token_expiry": token_expiry
        }
        
        # Create a new session with validated authentication data
        initial_state = {
            "user_name": user_name,  # Use actual user name from validation
            "user_id": login_data.user_id,
            "is_authenticated": True,
            "token": login_data.token,
            "tenant_id": validated_tenant_id,
            "tenant_name": tenant_name,  # Store the actual tenant name from validation
            "role": "user",  # Default role
            "is_admin": False,  # Default to non-admin
            "interaction_history": [],
            "last_query": None,
            "last_response": None,
            "token_login_data": token_login_data,  # Store token login data for reference
            "token_expiry": token_expiry,
            "welcome_message": welcome_message,  # Store welcome message
            "formatted_welcome": formatted_welcome,  # Store formatted welcome
            "capabilities_overview": capabilities_overview,  # Store capabilities
            "show_welcome_on_connect": False,  # Welcome messages only sent during login, not on WebSocket connect
            "quick_start_suggestions": quick_start_suggestions
        }
        
        logger.info(f"Creating session with validated user: {user_name} from tenant: {tenant_name}")
        
        # Create new session
        session = await session_service.create_session(
            app_name="lexedge",
            user_id=login_data.user_id,
            state=initial_state
        )
        session_id = session.id
        logger.info(f"Created new token-based session {session_id} for user {login_data.user_id} with user name {user_name}")
        
        # Send immediate welcome message via WebSocket
        try:
            from lexedge.utils.welcome_message_sender import send_delayed_welcome_message
            
            welcome_session_data = {
                'session_id': session_id,
                'user_id': login_data.user_id,
                'user_name': user_name,
                'tenant_name': tenant_name,
                'welcome_message': welcome_message,
                'formatted_welcome': formatted_welcome,
                'capabilities_overview': capabilities_overview,
                'quick_start_suggestions': quick_start_suggestions
            }
            
            # Send welcome message with a 3-second delay to allow client to connect to WebSocket
            welcome_sent = send_delayed_welcome_message(welcome_session_data, delay_seconds=3.0)
            logger.info(f"Delayed welcome message scheduled: {welcome_sent} for user {user_name}")
            
        except Exception as e:
            logger.error(f"Failed to schedule delayed welcome message: {str(e)}")
            # Don't fail the login if welcome message fails
        
        # Return login response with validated data
        return LoginResponse(
            tenant_id=validated_tenant_id,
            token=login_data.token,
            name=user_name,  # Use actual user name from validation
            email=validated_data.get("email", f"user@{validated_tenant_id}.com"),  # Default email format
            role=validated_data.get("role", "user"),  # Default role
            tenant_name=tenant_name,  # Actual tenant name from validation
            is_admin=validated_data.get("is_admin", False),  # Default to non-admin
            user_id=login_data.user_id,
            tenant_code=validated_tenant_id,
            tenant_admin_id=login_data.tenant_admin_id,
            session_id=session_id,
            welcome_message=welcome_message,
            formatted_welcome=formatted_welcome,
            capabilities_overview=capabilities_overview,
            quick_start_suggestions=quick_start_suggestions
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like validation failures)
        raise
    except Exception as e:
        logger.error(f"Error during token-based login: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Token login failed: {str(e)}"
        )

@app.get("/test-welcome")
async def test_welcome_message():
    """Test endpoint to demonstrate welcome message generation"""
    try:
        from lexedge.tools import generate_welcome_message
        
        # Test with sample data
        test_user_name = "Chirag"
        test_tenant_name = "Test Company"
        
        welcome_data = generate_welcome_message(test_user_name, test_tenant_name)
        
        return {
            "message": "Welcome message generated successfully",
            "user_name": test_user_name,
            "tenant_name": test_tenant_name,
            "welcome_data": welcome_data
        }
    except Exception as e:
        logger.error(f"Error testing welcome message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate welcome message: {str(e)}")

@app.post("/admin/cleanup")
async def admin_cleanup():
    """Admin endpoint to manually trigger comprehensive server cleanup"""
    try:
        logger.info("🔧 Manual cleanup triggered by admin endpoint")
        perform_comprehensive_cleanup("admin manual")
        return {
            "success": True,
            "message": "Comprehensive cleanup completed successfully",
            "timestamp": __import__('time').time()
        }
    except Exception as e:
        logger.error(f"❌ Admin cleanup failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": __import__('time').time()
        }

# ----- Admin UI Compatibility Routes -----

@app.get("/api/admin/tenant/notifications/unread_count")
async def admin_unread_notifications():
    """Compatibility endpoint for admin UI unread notification count."""
    return {"unread_count": 0}

# ----- WebSocket Route -----


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str = Query(..., description="Session ID from login"),
    tenant_id: str = Query(None, description="Tenant ID (optional, extracted from session if not provided)")
):
    """
    WebSocket endpoint with TENANT ISOLATION.
    
    URL Format: ws://localhost:3334/ws?session_id=<session_id>&tenant_id=<tenant_id>
    
    This ensures:
    - Each tenant has separate WebSocket connections
    - Messages are routed only to the correct session
    - No cross-tenant message leakage
    """
    
    connection_id = None
    active_session = {"user_id": None, "session_id": None, "tenant_id": None}
    
    try:
        # Step 1: Validate session and extract tenant/user info
        logger.info(f"[WEBSOCKET] Connection attempt for session: {session_id}, tenant: {tenant_id}")
        
        try:
            # Get session from database
            # Note: We need to get the session to validate it exists
            # For now, we'll list all sessions and find the matching one
            all_sessions = await session_service.list_sessions(app_name="lexedge")
            session = None
            
            for s in all_sessions:
                if s.id == session_id:
                    session = s
                    break
            
            if not session:
                if session_id == "demo_session":
                    # Auto-create demo session for easier development
                    logger.info(f"[WEBSOCKET] Auto-creating demo session")
                    session = await session_service.create_session(
                        app_name="lexedge",
                        user_id="demo_user",
                        session_id="demo_session",
                        state={
                            "user_name": "Demo User",
                            "is_authenticated": True,
                            "tenant_id": "default",
                            "role": "admin"
                        }
                    )
                else:
                    logger.error(f"[WEBSOCKET] Session {session_id} not found")
                    await websocket.close(code=1008, reason="Invalid session")
                    return
            
            # Extract user and tenant from session
            user_id = session.user_id
            session_tenant_id = session.state.get("tenant_id", "default")
            
            # Use provided tenant_id or fall back to session tenant_id
            final_tenant_id = tenant_id or session_tenant_id
            
            logger.info(f"[WEBSOCKET] Validated session: user={user_id}, tenant={final_tenant_id}")
            
        except Exception as e:
            logger.error(f"[WEBSOCKET] Session validation failed: {str(e)}")
            await websocket.close(code=1008, reason="Authentication failed")
            return
        
        # Step 2: Connect with tenant isolation
        connection_id = await manager.connect(
            websocket=websocket,
            session_id=session_id,
            tenant_id=final_tenant_id,
            user_id=user_id
        )
        
        if not connection_id:
            logger.error(f"[WEBSOCKET] Failed to create connection")
            return
        
        # Store session info
        active_session = {
            "user_id": user_id,
            "session_id": session_id,
            "tenant_id": final_tenant_id
        }
        
        logger.info(f"[WEBSOCKET] ✅ Connection established: {connection_id}")
        
        # Step 3: Send connection acknowledgment
        await manager.send_to_session(session_id, {
            "type": "connection_ack",
            "message": "Connected successfully",
            "session_id": session_id,
            "tenant_id": final_tenant_id,
            "connection_id": connection_id,
            "timestamp": time.time()
        })
        
        # Step 4: Main message loop
        while True:
            try:
                # Receive message from client
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60)
                
                # Update timestamp
                manager.update_timestamp(connection_id)
                
                # Extract query and data
                query = data.get("query")
                message_data = data.get("data") # Optional structured data (e.g. images)
                force_agent = data.get("force_agent") # Optional forced agent from bootstrap command
                logger.info(f"[WEBSOCKET] Received force_agent: {force_agent}")
                
                # Handle system messages
                system_message_types = ["ping", "heartbeat", "heartbeat_ack", "connection", "pong"]
                if (data.get("type") in system_message_types or 
                    (query and isinstance(query, str) and query.lower() in system_message_types)):
                    
                    if data.get("type") == "ping" or (query and isinstance(query, str) and query.lower() == "ping"):
                        await manager.send_to_session(session_id, {
                            "type": "pong",
                            "timestamp": time.time()
                        })
                    else:
                        await manager.send_to_session(session_id, {
                            "type": "ack",
                            "message": "System message received",
                            "timestamp": time.time()
                        })
                    continue
                
                # Validate query
                if not query and not message_data:
                    logger.warning(f"[WEBSOCKET] Empty query/data from session {session_id}")
                    continue
                
                display_query = query[:50] if query and isinstance(query, str) else "[Binary/Structured Data]"
                logger.info(f"[WEBSOCKET] Processing request for session {session_id}: {display_query}...")
                
                # Send acknowledgment
                await manager.send_to_session(session_id, {
                    "type": "ack",
                    "message": f"Processing request: {display_query}...",
                    "timestamp": time.time()
                })
                
                # Step 5: Process through agent
                try:
                    result = await run_agent(
                        user_id=user_id,
                        query=query or "Process the provided data.",
                        session_id=session_id,
                        app_name="lexedge",
                        message_data=message_data,
                        force_agent=force_agent
                    )
                    
                    if result.get("response"):
                        # Step 6: Send response ONLY to this session (TENANT ISOLATED)
                        response_data = {
                            "type": "response",
                            "session_id": session_id,
                            "tenant_id": final_tenant_id,
                            "response": result.get("response"),
                            "formatted_response": result.get("formatted_response"),
                            "agent": result.get("agent"),
                            "is_authenticated": result.get("is_authenticated", False),
                            "user_name": result.get("user_name", ""),
                            "role": result.get("role", ""),
                            "action_suggestions": result.get("action_suggestions", {}),
                            "timestamp": time.time()
                        }
                        
                        # CRITICAL: Send only to this session, not broadcast
                        success = await manager.send_to_session(session_id, response_data)
                        
                        if not success:
                            logger.error(f"[WEBSOCKET] Failed to send response to session {session_id}")
                            break
                        
                        logger.info(f"[WEBSOCKET] ✅ Response sent to session {session_id}")
                    else:
                        logger.info(f"[WEBSOCKET] Skipping empty response for session {session_id} (likely tool-handled)")
                    
                except Exception as e:
                    logger.error(f"[WEBSOCKET] Error processing query: {str(e)}")
                    await manager.send_to_session(session_id, {
                        "type": "error",
                        "message": f"Error processing query: {str(e)}",
                        "timestamp": time.time()
                    })
                
            except asyncio.TimeoutError:
                # Check if connection is still active
                if connection_id not in manager.connection_timestamps:
                    logger.warning(f"[WEBSOCKET] Connection {connection_id} timed out")
                    break
                continue
                
            except Exception as e:
                logger.error(f"[WEBSOCKET] Error in message loop: {str(e)}")
                break
        
    except WebSocketDisconnect:
        logger.info(f"[WEBSOCKET] Client disconnected: session={session_id}")
    
    except Exception as e:
        logger.error(f"[WEBSOCKET] Unexpected error: {str(e)}")
    
    finally:
        # Cleanup
        if connection_id:
            manager.disconnect(connection_id)
            logger.info(f"[WEBSOCKET] Cleaned up connection: {connection_id}")


@app.websocket("/api/admin/tenant/agent/chat/ws")
async def websocket_endpoint_admin(
    websocket: WebSocket,
    session_id: Optional[str] = Query(None, description="Session ID"),
    tenant_id: Optional[str] = Query(None, description="Tenant ID")
):
    """
    Compatibility WebSocket endpoint for admin UI clients.
    Falls back to demo_session if no session_id is provided.
    """
    await websocket_endpoint(
        websocket=websocket,
        session_id=session_id or "demo_session",
        tenant_id=tenant_id
    )



@app.get("/stream-demo", response_class=HTMLResponse)
async def stream_demo():
    """Serve the streaming demo page"""
    with open(os.path.join(STATIC_DIR, "stream_demo.html"), "r") as f:
        content = f.read()
    return content

# ----- Voice WebSocket Endpoint -----

@app.websocket("/ws/voice")
async def voice_websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    session_id: str,
    app_name: str = "lexedge"
):
    """
    WebSocket endpoint for bidirectional audio streaming (Voice Mode).
    Uses Google ADK Runner for low-latency streaming.
    """
    from lexedge.main_agent import root_agent, create_runner
    from lexedge.session import session_service
    
    logger.info(f"[VOICE-WS] Connection request: user_id={user_id}, session_id={session_id}")
    await websocket.accept()
    logger.info("[VOICE-WS] Connection accepted")

    # Initialize Runner
    # We use the shared session service to maintain context with text chat
    runner = create_runner(app_name)
    
    # Configure RunConfig
    # Assume the model supports AUDIO/native-audio if it's Gemini 1.5 Pro
    # We default case to TEXT output for safety unless we know for sure, 
    # BUT the user asked for "voice agent", so we try AUDIO.
    # However, to be safe with all models, let's stick to TEXT output for now 
    # (responses read out by frontend TTS or if model sends audio).
    # Gemini 1.5 Pro supports native audio out.
    
    # Check model capabilities or config?
    # We'll assume native audio (Bidi) is desired.
    model_name = root_agent.model.model_name if hasattr(root_agent, 'model') else "gemini-1.5-pro"
    is_native_audio = True # Force try native audio for "voice agent" experience
    
    if is_native_audio:
        run_config = RunConfig(
            streaming_mode=StreamingMode.BIDI,
            response_modalities=["AUDIO"], # Request Audio response
            input_audio_transcription=types.AudioTranscriptionConfig(),
            output_audio_transcription=types.AudioTranscriptionConfig(),
        )
    else:
        run_config = RunConfig(
            streaming_mode=StreamingMode.BIDI,
            response_modalities=["TEXT"],
            input_audio_transcription=types.AudioTranscriptionConfig(),
        )

    # Get or create session
    session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    if not session:
        await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)

    live_request_queue = LiveRequestQueue()

    async def upstream_task() -> None:
        """Receives messages from WebSocket and sends to LiveRequestQueue."""
        logger.debug("[VOICE-WS] upstream_task started")
        while True:
            try:
                message = await websocket.receive()
            except Exception as recv_err:
                logger.error(f"[VOICE-WS] Error receiving WebSocket message: {recv_err}")
                break

            # Handle binary (audio)
            if "bytes" in message:
                audio_data = message["bytes"]
                # logger.debug(f"[VOICE-WS] Received audio chunk: {len(audio_data)} bytes")
                audio_blob = types.Blob(mime_type="audio/pcm;rate=16000", data=audio_data)
                live_request_queue.send_realtime(audio_blob)

            # Handle text (commands)
            elif "text" in message:
                text_data = message["text"]
                logger.info(f"[VOICE-WS] Received text: {text_data}")
                try:
                    json_msg = json.loads(text_data)
                    if json_msg.get("type") == "text":
                         content = types.Content(parts=[types.Part(text=json_msg["text"])])
                         live_request_queue.send_content(content)
                except json.JSONDecodeError:
                    # Treat as raw text
                    content = types.Content(parts=[types.Part(text=text_data)])
                    live_request_queue.send_content(content)

    async def downstream_task() -> None:
        """Receives Events from runner and sends to WebSocket."""
        logger.debug("[VOICE-WS] downstream_task started")
        try:
            async for event in runner.run_live(
                user_id=user_id,
                session_id=session_id,
                live_request_queue=live_request_queue,
                run_config=run_config,
            ):
                event_json = event.model_dump_json(exclude_none=True, by_alias=True)
                await websocket.send_text(event_json)
        except Exception as e:
            logger.error(f"[VOICE-WS] Error in downstream task: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    try:
        await asyncio.gather(upstream_task(), downstream_task())
    except WebSocketDisconnect:
        logger.info("[VOICE-WS] Client disconnected")
    except Exception as e:
        logger.error(f"[VOICE-WS] Unexpected error: {e}")
    finally:
        live_request_queue.close()
        logger.info("[VOICE-WS] Closed")


# ----- Main Function -----

def start():
    """Run the FastAPI app with uvicorn with comprehensive server startup cleanup"""
    import uvicorn
    
    logger.info("🚀 Starting lexedge server...")
    
    # Perform comprehensive cleanup before starting
    import asyncio
    try:
        asyncio.run(perform_comprehensive_cleanup("server start"))
    except Exception as e:
        logger.warning(f"Startup cleanup encountered an issue: {e}")
    
    # Log startup completion
    logger.info("✅ Session firewall initialized with timeout management")
    logger.info("🎯 lexedge server ready to accept connections!")
    logger.info("=" * 60)
    
    # Run the FastAPI app
    # NOTE: reload=False to prevent session loss on file changes
    uvicorn.run("lexedge.api.app:app", host="0.0.0.0", port=3334, reload=False)

if __name__ == "__main__":
    start() 
