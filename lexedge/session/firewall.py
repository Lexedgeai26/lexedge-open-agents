import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta

from .service import session_service

# Configure logging
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_SESSION_TIMEOUT_MINUTES = 120
DEFAULT_MAX_SESSIONS_PER_IP = 5
DEFAULT_CLEANUP_INTERVAL_SECONDS = 300

class SessionFirewall:
    """
    Session firewall for managing and securing sessions.
    
    Features:
    - Automatic session expiration
    - IP-based connection limiting (future)
    - Rate limiting (future)
    """
    
    def __init__(self, 
                 session_timeout_minutes: int = DEFAULT_SESSION_TIMEOUT_MINUTES,
                 max_sessions_per_ip: int = DEFAULT_MAX_SESSIONS_PER_IP,
                 cleanup_interval_seconds: int = DEFAULT_CLEANUP_INTERVAL_SECONDS):
        """
        Initialize the session firewall.
        """
        self.session_timeout_minutes = session_timeout_minutes
        self.max_sessions_per_ip = max_sessions_per_ip
        self.cleanup_interval_seconds = cleanup_interval_seconds
        
        # Track session activity and IP addresses
        self.session_last_activity: Dict[str, float] = {}
        self.ip_sessions: Dict[str, Set[str]] = {}
        
        # We don't start the cleanup loop here, it should be started via startup event
        self.shutdown_flag = False
        self.cleanup_task = None
        
        logger.info(f"Session firewall initialized with {session_timeout_minutes} minute timeout")
    
    def start_cleanup_task(self):
        """Start the async cleanup loop."""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Session cleanup task started")

    def record_session_activity(self, session_id: str) -> None:
        """Record activity for a session."""
        self.session_last_activity[session_id] = time.time()
    
    def register_session_ip(self, session_id: str, ip_address: str) -> bool:
        """Register a session with its IP address."""
        if ip_address in self.ip_sessions and len(self.ip_sessions[ip_address]) >= self.max_sessions_per_ip:
            return False
        
        if ip_address not in self.ip_sessions:
            self.ip_sessions[ip_address] = set()
        
        self.ip_sessions[ip_address].add(session_id)
        self.record_session_activity(session_id)
        return True
    
    def unregister_session(self, session_id: str, ip_address: Optional[str] = None) -> None:
        """Unregister a session."""
        if session_id in self.session_last_activity:
            del self.session_last_activity[session_id]
        
        if ip_address and ip_address in self.ip_sessions:
            self.ip_sessions[ip_address].discard(session_id)
            if not self.ip_sessions[ip_address]:
                del self.ip_sessions[ip_address]
    
    def is_session_expired(self, session_id: str) -> bool:
        """Check if a session has expired."""
        if session_id not in self.session_last_activity:
            return False
        
        last_activity = self.session_last_activity[session_id]
        current_time = time.time()
        return (current_time - last_activity) > (self.session_timeout_minutes * 60)
    
    async def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions from the database."""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, last_activity in list(self.session_last_activity.items()):
            if (current_time - last_activity) > (self.session_timeout_minutes * 60):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            try:
                all_sessions = await session_service.list_sessions()
                for session in all_sessions:
                    if session.id == session_id:
                        logger.info(f"Deleting expired session {session_id} for user {session.user_id}")
                        await session_service.delete_session(
                            app_name=session.app_name,
                            user_id=session.user_id,
                            session_id=session_id
                        )
                        break
                
                self.unregister_session(session_id)
                
            except Exception as e:
                logger.error(f"Error deleting expired session {session_id}: {str(e)}")
    
    async def _cleanup_loop(self) -> None:
        """Background loop that periodically cleans up expired sessions."""
        while not self.shutdown_flag:
            try:
                await asyncio.sleep(self.cleanup_interval_seconds)
                if self.shutdown_flag:
                    break
                await self._cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in session cleanup: {str(e)}")
    
    def shutdown(self) -> None:
        """Shutdown the firewall."""
        self.shutdown_flag = True
        if self.cleanup_task:
            self.cleanup_task.cancel()
        logger.info("Session firewall shutdown complete")

    def reset(self) -> None:
        """Reset all session tracking data."""
        self.session_last_activity = {}
        self.ip_sessions = {}
        logger.info("Session firewall tracking data has been reset")

# Create a singleton instance
session_firewall = SessionFirewall()
