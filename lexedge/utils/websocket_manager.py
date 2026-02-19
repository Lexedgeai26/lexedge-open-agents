import logging
import time
from typing import Dict, Any, Set, Optional
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manager for WebSocket connections with tenant isolation"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # {connection_id: WebSocket}
        self.connection_timestamps: Dict[str, float] = {}  # {connection_id: timestamp}
        self.session_connections: Dict[str, str] = {}  # {session_id: connection_id}
        self.tenant_connections: Dict[str, Set[str]] = {}  # {tenant_id: Set[connection_id]}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}  # {connection_id: metadata}
    
    def _generate_connection_id(self, tenant_id: str, user_id: str, session_id: str) -> str:
        """Generate unique connection ID with tenant isolation"""
        import uuid
        return f"{tenant_id}:{user_id}:{session_id}:{uuid.uuid4().hex[:8]}"
    
    async def connect(self, websocket: WebSocket, session_id: str, tenant_id: str, user_id: str) -> str:
        """Connect a new WebSocket client with tenant isolation"""
        # Generate unique connection ID
        connection_id = self._generate_connection_id(tenant_id, user_id, session_id)
        
        # If this session already has a connection, close and disconnect the old one
        if session_id in self.session_connections:
            old_conn_id = self.session_connections[session_id]
            logger.info(f"Replacing existing connection for session {session_id}")
            # Try to close the old WebSocket gracefully before disconnecting
            if old_conn_id in self.active_connections:
                try:
                    old_ws = self.active_connections[old_conn_id]
                    await old_ws.close(code=1000, reason="Replaced by new connection")
                except Exception as e:
                    logger.warning(f"Could not close old WebSocket gracefully: {e}")
            self.disconnect(old_conn_id)
        
        # Accept and store connection
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_timestamps[connection_id] = time.time()
        self.session_connections[session_id] = connection_id
        
        # Track by tenant
        if tenant_id not in self.tenant_connections:
            self.tenant_connections[tenant_id] = set()
        self.tenant_connections[tenant_id].add(connection_id)
        
        # Store metadata
        self.connection_metadata[connection_id] = {
            "session_id": session_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "connected_at": time.time()
        }
        
        logger.info(f"✅ Connected: {connection_id}")
        return connection_id
    
    def disconnect(self, connection_id: str):
        """Disconnect a WebSocket client"""
        if connection_id not in self.active_connections:
            return
        
        # Get metadata before cleanup
        metadata = self.connection_metadata.get(connection_id, {})
        session_id = metadata.get("session_id")
        tenant_id = metadata.get("tenant_id")
        
        # Remove from active connections
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if connection_id in self.connection_timestamps:
            del self.connection_timestamps[connection_id]
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
        
        # Remove from session mapping
        if session_id and session_id in self.session_connections:
            if self.session_connections[session_id] == connection_id:
                del self.session_connections[session_id]
        
        # Remove from tenant mapping
        if tenant_id and tenant_id in self.tenant_connections:
            self.tenant_connections[tenant_id].discard(connection_id)
            if not self.tenant_connections[tenant_id]:
                del self.tenant_connections[tenant_id]
        
        logger.info(f"❌ Disconnected: {connection_id}")
    
    async def send_json(self, connection_id: str, data: Dict[str, Any]) -> bool:
        """Send JSON data to a specific connection"""
        if connection_id in self.active_connections:
            try:
                # Get metadata for this connection
                metadata = self.connection_metadata.get(connection_id, {})
                msg_type = data.get("type", "unknown")
                agent = data.get("agent", "N/A")
                
                logger.debug(f"🚀 SENDING TO SOCKET: {connection_id} (Session: {metadata.get('session_id')}, Type: {msg_type})")
                
                await self.active_connections[connection_id].send_json(data)
                self.connection_timestamps[connection_id] = time.time()
                
                logger.info(f"✅ SENT TO SOCKET: {connection_id}")
                return True
            except Exception as e:
                logger.error(f"❌ Error sending data to connection {connection_id}: {str(e)}")
                self.disconnect(connection_id)
                return False
        else:
            logger.warning(f"⚠️ Connection {connection_id} not found in active connections")
        return False
    
    async def send_to_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Send JSON data to a specific session (TENANT ISOLATED)"""
        if session_id not in self.session_connections:
            logger.warning(f"⚠️ No connection found for session {session_id}")
            return False
        
        connection_id = self.session_connections[session_id]
        return await self.send_json(connection_id, data)
    
    async def send_to_tenant(self, tenant_id: str, data: Dict[str, Any]) -> int:
        """Send JSON data to all connections in a tenant"""
        if tenant_id not in self.tenant_connections:
            logger.warning(f"No connections found for tenant {tenant_id}")
            return 0
        
        success_count = 0
        for connection_id in list(self.tenant_connections[tenant_id]):
            if await self.send_json(connection_id, data):
                success_count += 1
        
        return success_count
    
    def update_timestamp(self, connection_id: str):
        """Update the last activity timestamp for a connection"""
        if connection_id in self.connection_timestamps:
            self.connection_timestamps[connection_id] = time.time()
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        disconnected_clients = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
                self.connection_timestamps[client_id] = time.time()
            except Exception:
                disconnected_clients.append(client_id)
        
        for client_id in disconnected_clients:
            self.disconnect(client_id)

# Create singleton instance
manager = ConnectionManager()
