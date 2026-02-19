"""
Redis-based session service for low-resource environments.

This implementation uses Redis for fast, concurrent session access while
maintaining a small memory footprint suitable for low-resource machines.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import timedelta
import os

logger = logging.getLogger(__name__)

# Try to import Redis, fall back to SQLite if not available
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("redis package not installed. Install with: pip install redis")
    REDIS_AVAILABLE = False

class Session:
    """Session object compatible with existing session service"""
    def __init__(self, session_id: str, user_id: str, app_name: str, state: Dict[str, Any], last_update_time: float):
        self.id = session_id
        self.user_id = user_id
        self.app_name = app_name
        self.state = state
        self.last_update_time = last_update_time


class RedisSessionService:
    """
    Redis-based session service optimized for low-resource machines.
    
    Features:
    - Async Redis operations for better concurrency
    - Small connection pool (configurable)
    - Automatic session expiration
    - Memory-efficient session storage
    - Fallback to SQLite if Redis unavailable
    """
    
    def __init__(
        self,
        redis_url: str = None,
        pool_size: int = 10,
        session_ttl_hours: int = 2,
        enable_fallback: bool = True
    ):
        """
        Initialize Redis session service.
        
        Args:
            redis_url: Redis connection URL (default: redis://localhost:6379)
            pool_size: Maximum Redis connections (default: 10 for low resources)
            session_ttl_hours: Session time-to-live in hours (default: 2)
            enable_fallback: Use SQLite if Redis unavailable (default: True)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.pool_size = pool_size
        self.session_ttl = timedelta(hours=session_ttl_hours)
        self.enable_fallback = enable_fallback
        
        self.redis_client = None
        self.fallback_service = None
        self._initialized = False
        
        logger.info(f"Initializing Redis session service (pool_size={pool_size}, ttl={session_ttl_hours}h)")
    
    async def initialize(self):
        """Initialize Redis connection pool"""
        if self._initialized:
            return
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using fallback SQLite service")
            if self.enable_fallback:
                from .service import session_service
                self.fallback_service = session_service
            self._initialized = True
            return
        
        try:
            # Create Redis client with connection pool
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                max_connections=self.pool_size,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Redis connection established successfully")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            if self.enable_fallback:
                logger.warning("Falling back to SQLite session service")
                from .service import session_service
                self.fallback_service = session_service
            else:
                raise
            self._initialized = True
    
    def _get_session_key(self, app_name: str, user_id: str, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"session:{app_name}:{user_id}:{session_id}"
    
    def _get_user_sessions_key(self, app_name: str, user_id: str) -> str:
        """Generate Redis key for user's session list"""
        return f"user_sessions:{app_name}:{user_id}"
    
    async def create_session(
        self,
        app_name: str,
        user_id: str,
        session_id: str = None,
        state: Dict[str, Any] = None
    ) -> Session:
        """
        Create or update a session.
        
        Args:
            app_name: Application name
            user_id: User identifier
            session_id: Session ID (generated if not provided)
            state: Session state dictionary
            
        Returns:
            Session object
        """
        await self.initialize()
        
        # Use fallback if Redis unavailable
        if self.fallback_service:
            return self.fallback_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
                state=state
            )
        
        # Generate session_id if not provided
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        state = state or {}
        current_time = time.time()
        
        # Create session data
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "app_name": app_name,
            "state": state,
            "last_update_time": current_time
        }
        
        # Store in Redis with TTL
        session_key = self._get_session_key(app_name, user_id, session_id)
        
        try:
            # Store session data
            await self.redis_client.setex(
                session_key,
                self.session_ttl,
                json.dumps(session_data)
            )
            
            # Add to user's session list
            user_sessions_key = self._get_user_sessions_key(app_name, user_id)
            await self.redis_client.sadd(user_sessions_key, session_id)
            await self.redis_client.expire(user_sessions_key, self.session_ttl)
            
            logger.info(f"Created session {session_id} for user {user_id}")
            
            return Session(
                session_id=session_id,
                user_id=user_id,
                app_name=app_name,
                state=state,
                last_update_time=current_time
            )
            
        except Exception as e:
            logger.error(f"Error creating session in Redis: {str(e)}")
            raise
    
    async def get_session(
        self,
        app_name: str,
        user_id: str,
        session_id: str
    ) -> Optional[Session]:
        """
        Get a session by ID.
        
        Args:
            app_name: Application name
            user_id: User identifier
            session_id: Session ID
            
        Returns:
            Session object or None if not found
        """
        await self.initialize()
        
        # Use fallback if Redis unavailable
        if self.fallback_service:
            return self.fallback_service.get_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id
            )
        
        session_key = self._get_session_key(app_name, user_id, session_id)
        
        try:
            # Get session data from Redis
            session_data_json = await self.redis_client.get(session_key)
            
            if not session_data_json:
                logger.warning(f"Session {session_id} not found for user {user_id}")
                return None
            
            session_data = json.loads(session_data_json)
            
            # Refresh TTL on access
            await self.redis_client.expire(session_key, self.session_ttl)
            
            return Session(
                session_id=session_data["session_id"],
                user_id=session_data["user_id"],
                app_name=session_data["app_name"],
                state=session_data["state"],
                last_update_time=session_data["last_update_time"]
            )
            
        except Exception as e:
            logger.error(f"Error getting session from Redis: {str(e)}")
            return None
    
    async def update_session_state(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
        state: Dict[str, Any]
    ) -> bool:
        """
        Update session state.
        
        Args:
            app_name: Application name
            user_id: User identifier
            session_id: Session ID
            state: New session state
            
        Returns:
            True if successful, False otherwise
        """
        await self.initialize()
        
        # Use fallback if Redis unavailable
        if self.fallback_service:
            return self.fallback_service.update_session_state(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
                state=state
            )
        
        session_key = self._get_session_key(app_name, user_id, session_id)
        
        try:
            # Get existing session
            session_data_json = await self.redis_client.get(session_key)
            
            if not session_data_json:
                logger.warning(f"Cannot update non-existent session {session_id}")
                return False
            
            session_data = json.loads(session_data_json)
            session_data["state"] = state
            session_data["last_update_time"] = time.time()
            
            # Update in Redis
            await self.redis_client.setex(
                session_key,
                self.session_ttl,
                json.dumps(session_data)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating session state: {str(e)}")
            return False
    
    async def list_sessions(
        self,
        app_name: str = None,
        user_id: str = None
    ) -> List[Session]:
        """
        List sessions.
        
        Args:
            app_name: Filter by application name
            user_id: Filter by user ID
            
        Returns:
            List of Session objects
        """
        await self.initialize()
        
        # Use fallback if Redis unavailable
        if self.fallback_service:
            return self.fallback_service.list_sessions(
                app_name=app_name,
                user_id=user_id
            )
        
        sessions = []
        
        try:
            if user_id and app_name:
                # Get sessions for specific user
                user_sessions_key = self._get_user_sessions_key(app_name, user_id)
                session_ids = await self.redis_client.smembers(user_sessions_key)
                
                for session_id in session_ids:
                    session = await self.get_session(app_name, user_id, session_id)
                    if session:
                        sessions.append(session)
            else:
                # Scan all sessions (less efficient, use sparingly)
                pattern = f"session:{app_name or '*'}:{user_id or '*'}:*"
                async for key in self.redis_client.scan_iter(match=pattern, count=100):
                    session_data_json = await self.redis_client.get(key)
                    if session_data_json:
                        session_data = json.loads(session_data_json)
                        sessions.append(Session(
                            session_id=session_data["session_id"],
                            user_id=session_data["user_id"],
                            app_name=session_data["app_name"],
                            state=session_data["state"],
                            last_update_time=session_data["last_update_time"]
                        ))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing sessions: {str(e)}")
            return []
    
    async def delete_session(
        self,
        app_name: str,
        user_id: str,
        session_id: str
    ) -> bool:
        """
        Delete a session.
        
        Args:
            app_name: Application name
            user_id: User identifier
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        await self.initialize()
        
        # Use fallback if Redis unavailable
        if self.fallback_service:
            return self.fallback_service.delete_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id
            )
        
        session_key = self._get_session_key(app_name, user_id, session_id)
        user_sessions_key = self._get_user_sessions_key(app_name, user_id)
        
        try:
            # Delete session
            await self.redis_client.delete(session_key)
            
            # Remove from user's session list
            await self.redis_client.srem(user_sessions_key, session_id)
            
            logger.info(f"Deleted session {session_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            return False
    
    async def clear_all_sessions(self) -> int:
        """
        Clear all sessions (use with caution).
        
        Returns:
            Number of sessions cleared
        """
        await self.initialize()
        
        # Use fallback if Redis unavailable
        if self.fallback_service:
            return self.fallback_service.clear_all_sessions()
        
        try:
            count = 0
            # Delete all session keys
            async for key in self.redis_client.scan_iter(match="session:*", count=100):
                await self.redis_client.delete(key)
                count += 1
            
            # Delete all user session lists
            async for key in self.redis_client.scan_iter(match="user_sessions:*", count=100):
                await self.redis_client.delete(key)
            
            logger.info(f"Cleared {count} sessions from Redis")
            return count
            
        except Exception as e:
            logger.error(f"Error clearing sessions: {str(e)}")
            return 0
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")


# Create singleton instance
redis_session_service = RedisSessionService(
    pool_size=int(os.getenv("REDIS_POOL_SIZE", "10")),
    session_ttl_hours=int(os.getenv("SESSION_TTL_HOURS", "2"))
)
