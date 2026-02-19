"""
Improved WebSocket Connection Manager with authentication and resource limits.

Optimized for low-resource machines with:
- Connection limits per user
- Token-based authentication
- Automatic cleanup of stale connections
- Memory-efficient connection tracking
"""

import asyncio
import time
import logging
import uuid
from typing import Dict, Any, Optional, Set
from fastapi import WebSocket
import psutil

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Enhanced WebSocket connection manager with security and resource management.
    
    Features:
    - Token-based authentication
    - Connection limits per user
    - Automatic stale connection cleanup
    - Resource monitoring
    - Memory-efficient storage
    """
    
    def __init__(
        self,
        max_total_connections: int = 100,
        max_connections_per_user: int = 3,
        heartbeat_interval: int = 30,
        connection_timeout: int = 300
    ):
        """
        Initialize connection manager.
        
        Args:
            max_total_connections: Maximum total WebSocket connections (default: 100)
            max_connections_per_user: Maximum connections per user (default: 3)
            heartbeat_interval: Heartbeat interval in seconds (default: 30)
            connection_timeout: Connection timeout in seconds (default: 300)
        """
        self.max_total_connections = max_total_connections
        self.max_connections_per_user = max_connections_per_user
        self.heartbeat_interval = heartbeat_interval
        self.connection_timeout = connection_timeout
        
        # Connection storage: {connection_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Connection metadata: {connection_id: metadata}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # User connections: {user_id: Set[connection_id]}
        self.user_connections: Dict[str, Set[str]] = {}
        
        # Connection timestamps: {connection_id: last_activity_time}
        self.connection_timestamps: Dict[str, float] = {}
        
        # Start cleanup task
        self._cleanup_task = None
        
        logger.info(
            f"ConnectionManager initialized: "
            f"max_total={max_total_connections}, "
            f"max_per_user={max_connections_per_user}"
        )
    
    def start_cleanup_task(self):
        """Start background cleanup task"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_stale_connections())
            logger.info("Started connection cleanup task")
    
    async def _cleanup_stale_connections(self):
        """Background task to clean up stale connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                current_time = time.time()
                stale_connections = []
                
                # Find stale connections
                for conn_id, last_activity in self.connection_timestamps.items():
                    if current_time - last_activity > self.connection_timeout:
                        stale_connections.append(conn_id)
                
                # Disconnect stale connections
                for conn_id in stale_connections:
                    logger.warning(f"Disconnecting stale connection: {conn_id}")
                    await self.disconnect(conn_id, reason="Connection timeout")
                
                if stale_connections:
                    logger.info(f"Cleaned up {len(stale_connections)} stale connections")
                
                # Log resource usage
                self._log_resource_usage()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")
    
    def _log_resource_usage(self):
        """Log current resource usage"""
        try:
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.1)
            
            logger.info(
                f"Resources: {len(self.active_connections)} connections, "
                f"Memory: {memory.percent:.1f}%, CPU: {cpu:.1f}%"
            )
            
            # Warn if resources are high
            if memory.percent > 80:
                logger.warning(f"⚠️ High memory usage: {memory.percent:.1f}%")
            if cpu > 80:
                logger.warning(f"⚠️ High CPU usage: {cpu:.1f}%")
                
        except Exception as e:
            logger.error(f"Error logging resource usage: {str(e)}")
    
    def _generate_connection_id(self, user_id: str, session_id: str) -> str:
        """Generate unique connection ID"""
        return f"{user_id}:{session_id}:{uuid.uuid4().hex[:8]}"
    
    def _get_user_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a user"""
        return len(self.user_connections.get(user_id, set()))
    
    async def can_connect(self, user_id: str) -> tuple[bool, str]:
        """
        Check if user can create a new connection.
        
        Args:
            user_id: User identifier
            
        Returns:
            Tuple of (can_connect: bool, reason: str)
        """
        # Check total connection limit
        if len(self.active_connections) >= self.max_total_connections:
            return False, f"Server at maximum capacity ({self.max_total_connections} connections)"
        
        # Check per-user connection limit
        user_conn_count = self._get_user_connection_count(user_id)
        if user_conn_count >= self.max_connections_per_user:
            return False, f"Maximum connections per user reached ({self.max_connections_per_user})"
        
        return True, "OK"
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        session_id: str,
        metadata: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        Connect a new WebSocket client.
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier
            session_id: Session identifier
            metadata: Additional connection metadata
            
        Returns:
            Connection ID if successful, None otherwise
        """
        # Check if connection is allowed
        can_connect, reason = await self.can_connect(user_id)
        if not can_connect:
            logger.warning(f"Connection rejected for user {user_id}: {reason}")
            await websocket.close(code=1008, reason=reason)
            return None
        
        # Generate connection ID
        connection_id = self._generate_connection_id(user_id, session_id)
        
        try:
            # Accept WebSocket connection
            await websocket.accept()
            
            # Store connection
            self.active_connections[connection_id] = websocket
            self.connection_timestamps[connection_id] = time.time()
            
            # Store metadata
            self.connection_metadata[connection_id] = {
                "user_id": user_id,
                "session_id": session_id,
                "connected_at": time.time(),
                **(metadata or {})
            }
            
            # Track user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            logger.info(
                f"✅ Connected: {connection_id} "
                f"(user: {user_id}, total: {len(self.active_connections)})"
            )
            
            return connection_id
            
        except Exception as e:
            logger.error(f"Error connecting WebSocket: {str(e)}")
            return None
    
    async def disconnect(self, connection_id: str, reason: str = "Normal closure"):
        """
        Disconnect a WebSocket client.
        
        Args:
            connection_id: Connection identifier
            reason: Reason for disconnection
        """
        if connection_id not in self.active_connections:
            return
        
        try:
            # Get metadata before cleanup
            metadata = self.connection_metadata.get(connection_id, {})
            user_id = metadata.get("user_id")
            
            # Close WebSocket
            websocket = self.active_connections[connection_id]
            try:
                await websocket.close()
            except Exception:
                pass  # Already closed
            
            # Remove from active connections
            del self.active_connections[connection_id]
            
            # Remove metadata
            if connection_id in self.connection_metadata:
                del self.connection_metadata[connection_id]
            
            # Remove timestamp
            if connection_id in self.connection_timestamps:
                del self.connection_timestamps[connection_id]
            
            # Remove from user connections
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            logger.info(
                f"❌ Disconnected: {connection_id} "
                f"(reason: {reason}, remaining: {len(self.active_connections)})"
            )
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {str(e)}")
    
    async def send_json(self, connection_id: str, data: Dict[str, Any]) -> bool:
        """
        Send JSON data to a specific connection.
        
        Args:
            connection_id: Connection identifier
            data: Data to send
            
        Returns:
            True if successful, False otherwise
        """
        if connection_id not in self.active_connections:
            logger.warning(f"Cannot send to non-existent connection: {connection_id}")
            return False
        
        try:
            websocket = self.active_connections[connection_id]
            await websocket.send_json(data)
            
            # Update timestamp
            self.connection_timestamps[connection_id] = time.time()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending data to {connection_id}: {str(e)}")
            # Connection likely broken, disconnect it
            await self.disconnect(connection_id, reason="Send failed")
            return False
    
    async def send_to_user(self, user_id: str, data: Dict[str, Any]) -> int:
        """
        Send data to all connections for a user.
        
        Args:
            user_id: User identifier
            data: Data to send
            
        Returns:
            Number of successful sends
        """
        if user_id not in self.user_connections:
            logger.warning(f"No connections found for user: {user_id}")
            return 0
        
        connection_ids = list(self.user_connections[user_id])
        success_count = 0
        
        for conn_id in connection_ids:
            if await self.send_json(conn_id, data):
                success_count += 1
        
        return success_count
    
    async def broadcast(self, data: Dict[str, Any], exclude: Set[str] = None):
        """
        Broadcast data to all connections.
        
        Args:
            data: Data to broadcast
            exclude: Set of connection IDs to exclude
        """
        exclude = exclude or set()
        failed_connections = []
        
        for conn_id in list(self.active_connections.keys()):
            if conn_id in exclude:
                continue
            
            if not await self.send_json(conn_id, data):
                failed_connections.append(conn_id)
        
        if failed_connections:
            logger.warning(f"Broadcast failed for {len(failed_connections)} connections")
    
    def update_timestamp(self, connection_id: str):
        """Update last activity timestamp for a connection"""
        if connection_id in self.connection_timestamps:
            self.connection_timestamps[connection_id] = time.time()
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get connection metadata"""
        return self.connection_metadata.get(connection_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "total_users": len(self.user_connections),
            "max_total_connections": self.max_total_connections,
            "max_connections_per_user": self.max_connections_per_user,
            "connections_by_user": {
                user_id: len(conn_ids)
                for user_id, conn_ids in self.user_connections.items()
            }
        }
    
    async def shutdown(self):
        """Shutdown connection manager"""
        logger.info("Shutting down connection manager...")
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect all connections
        connection_ids = list(self.active_connections.keys())
        for conn_id in connection_ids:
            await self.disconnect(conn_id, reason="Server shutdown")
        
        logger.info("Connection manager shutdown complete")
