"""
Fixed WebSocket endpoint with tenant isolation.

This file contains the corrected WebSocket endpoint that should replace
the existing one in app.py (around line 1345).

CRITICAL FIX: Ensures each tenant has isolated WebSocket connections.
"""

import asyncio
import time
import logging
from fastapi import WebSocket, WebSocketDisconnect, Query
from typing import Optional

logger = logging.getLogger(__name__)

# This should be added to app.py to replace the existing @app.websocket("/ws/{client_id}")
async def websocket_endpoint_fixed(
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
    from lexedge.session import session_service
    from lexedge.agent_runner import run_agent
    from lexedge.api.app import manager  # Import the global manager
    
    connection_id = None
    active_session = {"user_id": None, "session_id": None, "tenant_id": None}
    
    try:
        # Step 1: Validate session and extract tenant/user info
        logger.info(f"[WEBSOCKET] Connection attempt for session: {session_id}, tenant: {tenant_id}")
        
        try:
            # Get session from database
            # Note: We need to get the session to validate it exists
            # For now, we'll list all sessions and find the matching one
            all_sessions = session_service.list_sessions(app_name="lexedge")
            session = None
            
            for s in all_sessions:
                if s.id == session_id:
                    session = s
                    break
            
            if not session:
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
                
                # Extract query
                query = data.get("query")
                
                # Handle system messages
                system_message_types = ["ping", "heartbeat", "heartbeat_ack", "connection", "pong"]
                if (data.get("type") in system_message_types or 
                    (query and query.lower() in system_message_types)):
                    
                    if data.get("type") == "ping" or (query and query.lower() == "ping"):
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
                if not query:
                    logger.warning(f"[WEBSOCKET] Empty query from session {session_id}")
                    continue
                
                logger.info(f"[WEBSOCKET] Processing query for session {session_id}: {query[:50]}...")
                
                # Send acknowledgment
                await manager.send_to_session(session_id, {
                    "type": "ack",
                    "message": f"Processing query: {query[:50]}...",
                    "timestamp": time.time()
                })
                
                # Step 5: Process through agent
                try:
                    result = await run_agent(
                        user_id=user_id,
                        query=query,
                        session_id=session_id,
                        app_name="lexedge"
                    )
                    
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


# ============================================================================
# INTEGRATION INSTRUCTIONS
# ============================================================================
"""
To integrate this fix into app.py:

1. Find the existing WebSocket endpoint (around line 1345):
   @app.websocket("/ws/{client_id}")
   async def websocket_endpoint(websocket: WebSocket, client_id: str):

2. Replace it with:
   @app.websocket("/ws")
   async def websocket_endpoint(
       websocket: WebSocket,
       session_id: str = Query(...),
       tenant_id: str = Query(None)
   ):
       await websocket_endpoint_fixed(websocket, session_id, tenant_id)

3. Or copy the entire function body from websocket_endpoint_fixed above.

4. Update the client to connect with:
   ws://localhost:3334/ws?session_id=<session_id>&tenant_id=<tenant_id>
"""
