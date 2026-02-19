"""
Session management service for the Appliview application.
Provides persistence with SQLite database.
"""
import base64
import json
import logging
import sqlite3
import uuid
from typing import Dict, Any, List, Optional
import time

from google.adk.sessions import InMemorySessionService, Session
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.genai import types

try:
    # Package import
    from ..config import DB_PATH, MAX_SESSIONS_PER_USER, MAX_MESSAGES_PER_SESSION
except ImportError:
    # Direct import when running from applivew directory
    from config import DB_PATH, MAX_SESSIONS_PER_USER, MAX_MESSAGES_PER_SESSION

logger = logging.getLogger(__name__)

class SQLiteSessionService(InMemorySessionService):
    """SQLite-based implementation of SessionService."""
    
    def __init__(self, db_path: str = DB_PATH, 
                 max_sessions_per_user: int = MAX_SESSIONS_PER_USER, 
                 max_messages_per_session: int = MAX_MESSAGES_PER_SESSION):
        """Initialize SQLite session service."""
        super().__init__()  # Initialize the base InMemorySessionService
        self.db_path = db_path
        self.max_sessions_per_user = max_sessions_per_user
        self.max_messages_per_session = max_messages_per_session
        self._init_db()
        self._runners = {}  # Cache for runners
    
    def _init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    app_name TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Check if the runners table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='runners'")
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                # Check if agent_type column exists
                cursor = conn.execute("PRAGMA table_info(runners)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if "agent_type" not in columns:
                    # The table exists but doesn't have the agent_type column, so we need to recreate it
                    conn.execute("DROP TABLE runners")
                    table_exists = False
            
            if not table_exists:
                conn.execute("""
                    CREATE TABLE runners (
                        app_name TEXT PRIMARY KEY,
                        agent_name TEXT NOT NULL,
                        agent_type TEXT NOT NULL,
                        agent_description TEXT,
                        agent_instruction TEXT
                    )
                """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            conn.commit()
    
    def _count_user_sessions(self, user_id: str) -> int:
        """Count the number of sessions for a user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM sessions WHERE user_id = ?",
                (user_id,)
            )
            return cursor.fetchone()[0]
    
    def _count_session_messages(self, session_id: str) -> int:
        """Count the number of messages in a session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id = ?",
                (session_id,)
            )
            return cursor.fetchone()[0]
    
    async def _enforce_user_session_limit(self, user_id: str) -> None:
        """Enforce session limit per user by removing oldest sessions if limit exceeded."""
        with sqlite3.connect(self.db_path) as conn:
            # Get current count
            session_count = self._count_user_sessions(user_id)
            
            # If below limit, no action needed
            if session_count <= self.max_sessions_per_user:
                return
                
            # Get the oldest session IDs to remove
            to_remove = session_count - self.max_sessions_per_user
            cursor = conn.execute(
                "SELECT id FROM sessions WHERE user_id = ? ORDER BY created_at ASC LIMIT ?",
                (user_id, to_remove)
            )
            
            # Delete old sessions and their messages
            for row in cursor.fetchall():
                session_id = row[0]
                # Delete messages first due to foreign key constraint
                conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                # Delete session
                conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            
            conn.commit()
    
    async def _enforce_message_limit(self, session_id: str) -> None:
        """Enforce message limit per session by removing oldest messages if limit exceeded."""
        with sqlite3.connect(self.db_path) as conn:
            # Get current count
            message_count = self._count_session_messages(session_id)
            
            # If below limit, no action needed
            if message_count <= self.max_messages_per_session:
                return
                
            # Get the oldest message IDs to remove
            to_remove = message_count - self.max_messages_per_session
            conn.execute(
                "DELETE FROM messages WHERE id IN (SELECT id FROM messages WHERE session_id = ? ORDER BY created_at ASC LIMIT ?)",
                (session_id, to_remove)
            )
            conn.commit()
    
    async def create_session(self, *, app_name: str, user_id: str, 
                      state: Optional[Dict[str, Any]] = None, 
                      session_id: Optional[str] = None) -> Session:
        """Create a new session."""
        session_id = session_id or str(uuid.uuid4())
        state = state or {}
        
        # Enforce session limit per user
        await self._enforce_user_session_limit(user_id)
        
        with sqlite3.connect(self.db_path) as conn:
            # Check if session already exists
            cursor = conn.execute(
                "SELECT id FROM sessions WHERE id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            
            if row:
                # Update existing session
                conn.execute(
                    "UPDATE sessions SET app_name = ?, user_id = ?, state = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (app_name, user_id, json.dumps(state), session_id)
                )
            else:
                # Create new session
                conn.execute(
                    "INSERT INTO sessions (id, app_name, user_id, state) VALUES (?, ?, ?, ?)",
                    (session_id, app_name, user_id, json.dumps(state))
                )
            conn.commit()
        
        # Call parent method to maintain in-memory state as well
        try:
            # Try to get the session from the parent's in-memory storage
            result = await super().get_session(app_name=app_name, user_id=user_id, session_id=session_id)
            # Update the in-memory state
            result.state = state
        except Exception:
            # If it doesn't exist in memory, create it
            result = await super().create_session(
                app_name=app_name, 
                user_id=user_id, 
                state=state, 
                session_id=session_id
            )
        
        return result
    
    async def get_session(self, *, app_name: str, user_id: str, session_id: str) -> Session:
        """Get session information."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT state FROM sessions WHERE id = ? AND app_name = ? AND user_id = ?",
                (session_id, app_name, user_id)
            )
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"Session not found: {session_id}")
            
            state = json.loads(row[0])
        
        # Call parent method to maintain in-memory state
        try:
            return await super().get_session(app_name=app_name, user_id=user_id, session_id=session_id)
        except Exception:
            # If it doesn't exist in memory, create it
            return await super().create_session(
                app_name=app_name,
                user_id=user_id,
                state=state,
                session_id=session_id
            )
    
    async def delete_session(self, *, app_name: str, user_id: str, session_id: str) -> None:
        """Delete a session."""
        with sqlite3.connect(self.db_path) as conn:
            # Delete messages first due to foreign key constraint
            conn.execute(
                "DELETE FROM messages WHERE session_id = ?",
                (session_id,)
            )
            # Delete session
            conn.execute(
                "DELETE FROM sessions WHERE id = ? AND app_name = ? AND user_id = ?",
                (session_id, app_name, user_id)
            )
            conn.commit()
        
        # Delete from memory too
        try:
            super().delete_session(app_name=app_name, user_id=user_id, session_id=session_id)
        except Exception:
            # Ignore if it doesn't exist in memory
            pass
    
    async def get_runner(self, *, app_name: str) -> Optional[Runner]:
        """Get existing runner for an application."""
        # Don't use cache - always return None to force fresh runner creation
        # This ensures the root agent evaluates each query independently
        return None
    
    async def create_runner(self, *, app_name: str, agent: Agent) -> Runner:
        """Create a new runner for an agent."""
        # Store only string representations in the database
        agent_type = agent.__class__.__name__
        agent_instruction = agent.instruction
        if not isinstance(agent_instruction, str):
            agent_instruction = f"[Dynamic Provider: {getattr(agent_instruction, '__name__', 'unknown')}]"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO runners (app_name, agent_name, agent_type, agent_description, agent_instruction) VALUES (?, ?, ?, ?, ?)",
                (app_name, agent.name, agent_type, agent.description, agent_instruction)
            )
            conn.commit()
        
        # Create a new runner (don't cache it)
        runner = Runner(
            app_name=app_name,
            agent=agent,
            session_service=self
        )
        
        # Don't cache the runner to ensure fresh evaluation each time
        # self._runners[app_name] = runner
        
        return runner
    
    async def save_message(self, *, session_id: str, role: str, content: str) -> str:
        """Save a message to the database."""
        # Enforce message limit for this session
        await self._enforce_message_limit(session_id)
        
        # Generate message ID
        message_id = str(uuid.uuid4())
        
        # Insert message into database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO messages (id, session_id, role, content) VALUES (?, ?, ?, ?)",
                (message_id, session_id, role, content)
            )
            conn.commit()
        
        return message_id
    
    async def save_api_response(self, *, session_id: str, api_source: str, 
                         response_content: str, raw_data: Optional[str] = None) -> str:
        """
        Save an API response specifically marked as exportable data.
        
        Args:
            session_id: The session ID
            api_source: The source of the API response (e.g., 'candidate_search', 'job_search')
            response_content: The formatted response content for display
            raw_data: Optional raw JSON data from the API
            
        Returns:
            str: The message ID
        """
        # Enforce message limit for this session
        await self._enforce_message_limit(session_id)
        
        # Generate message ID
        message_id = str(uuid.uuid4())
        
        # Insert API response into database with special marking
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO messages 
                   (id, session_id, role, content, message_type, api_source, api_response_data) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (message_id, session_id, "assistant", response_content, 
                 "api_response", api_source, raw_data)
            )
            conn.commit()
        
        logger.info(f"💾 Saved API response from {api_source} to session {session_id} (length: {len(response_content)} chars)")
        return message_id
    
    async def get_api_responses(self, *, session_id: Optional[str] = None, user_id: Optional[str] = None,
                         api_source: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve API response data for exports.
        
        Args:
            session_id: Optional session ID to filter by
            user_id: Optional user ID to filter by  
            api_source: Optional API source to filter by (e.g., 'candidate_search')
            limit: Maximum number of responses to return
            
        Returns:
            List of API response records
        """
        query = """
            SELECT m.id, m.session_id, m.content, m.api_source, m.api_response_data, 
                   m.created_at, s.user_id
            FROM messages m
            JOIN sessions s ON m.session_id = s.id
            WHERE m.message_type = 'api_response'
        """
        params = []
        
        # Add filters
        if session_id:
            query += " AND m.session_id = ?"
            params.append(session_id)
        if user_id:
            query += " AND s.user_id = ?"
            params.append(user_id)
        if api_source:
            query += " AND m.api_source = ?"
            params.append(api_source)
            
        query += " ORDER BY m.created_at DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'session_id': row[1], 
                'content': row[2],
                'api_source': row[3],
                'api_response_data': row[4],
                'created_at': row[5],
                'user_id': row[6]
            })
            
        logger.info(f"Retrieved {len(results)} API response records")
        return results
    
    def create_message(
        self,
        *,
        content: str,
        role: str = "user",
        data: Optional[Dict[str, Any]] = None,
    ) -> types.Content:
        """Create a new message for sending to the agent."""
        parts: List[types.Part] = []

        if content:
            parts.append(types.Part.from_text(text=content))

        if data:
            image_b64 = data.get("image_b64") or data.get("image_data_b64")
            mime_type = data.get("mime_type")

            if image_b64:
                try:
                    if image_b64.startswith("data:"):
                        header, image_b64 = image_b64.split(",", 1)
                        if not mime_type and ";" in header:
                            mime_type = header.split(":", 1)[1].split(";", 1)[0]

                    image_bytes = base64.b64decode(image_b64)
                    parts.append(
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=mime_type or "application/octet-stream",
                        )
                    )
                except Exception as decode_error:
                    logger.warning(f"Failed to decode image data for message: {decode_error}")

        if not parts:
            parts.append(types.Part.from_text(text=""))

        return types.Content(role=role, parts=parts)
    
    async def list_sessions(self, *, app_name: Optional[str] = None, user_id: Optional[str] = None) -> List[Session]:
        """List sessions matching the given criteria."""
        query = "SELECT id, app_name, user_id, state FROM sessions"
        params = []
        
        # Add filters if provided
        filters = []
        if app_name:
            filters.append("app_name = ?")
            params.append(app_name)
        if user_id:
            filters.append("user_id = ?")
            params.append(user_id)
        
        if filters:
            query += " WHERE " + " AND ".join(filters)
        
        # Add ordering
        query += " ORDER BY updated_at DESC"
        
        logger.info(f"SQL Query for list_sessions: {query} with params {params}")
        
        # Execute query
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
        logger.info(f"Found {len(rows)} sessions in database matching filters")
        
        # Create Session objects
        sessions = []
        for row in rows:
            session_id, app_name, user_id, state_str = row
            logger.info(f"Processing session {session_id} for user {user_id}")
            
            try:
                # Check for empty or invalid state
                if not state_str or state_str.strip() == "":
                    logger.warning(f"Empty state found for session {session_id}, user {user_id}. Skipping.")
                    continue
                    
                state = json.loads(state_str)
                
                # Skip if state is None or not a dict
                if state is None or not isinstance(state, dict):
                    logger.warning(f"Invalid state type for session {session_id}, user {user_id}. Skipping.")
                    continue
                
                # Create a new session object directly
                session = Session(
                    id=session_id,
                    app_name=app_name,
                    user_id=user_id,
                    state=state,
                    last_update_time=time.time()  # Use current time since we don't have the actual update time
                )
                sessions.append(session)
                logger.info(f"Successfully loaded session {session_id}")
                
            except Exception as e:
                logger.error(f"Error processing session {session_id}: {str(e)}")
                # Skip this session and continue with others
                continue
        
        logger.info(f"Returning {len(sessions)} valid sessions")
        return sessions

    async def _cleanup_stale_sessions(self, max_age_hours=24):
        """Clean up sessions older than the specified age in hours"""
        with sqlite3.connect(self.db_path) as conn:
            # Calculate cutoff time
            cutoff_time = time.time() - (max_age_hours * 3600)
            
            # Find stale sessions
            cursor = conn.execute(
                "SELECT id FROM sessions WHERE updated_at < ?",
                (cutoff_time,)
            )
            
            stale_session_ids = [row[0] for row in cursor.fetchall()]
            
            # Delete stale sessions
            for session_id in stale_session_ids:
                try:
                    # Delete messages first due to foreign key constraint
                    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                    # Delete session
                    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                    logger.info(f"Cleaned up stale session: {session_id}")
                except Exception as e:
                    logger.error(f"Error cleaning up session {session_id}: {str(e)}")
            
            conn.commit()
            
            return len(stale_session_ids)

    async def clear_all_sessions(self):
        """Clear all sessions from the database, use with caution!"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get count of sessions before deletion for reporting
                cursor = conn.execute("SELECT COUNT(*) FROM sessions")
                session_count = cursor.fetchone()[0]
                
                # Delete all messages first due to foreign key constraints
                conn.execute("DELETE FROM messages")
                
                # Delete all sessions
                conn.execute("DELETE FROM sessions")
                
                # Commit the changes
                conn.commit()
                
                logger.info(f"Cleared all sessions from the database. Removed {session_count} sessions.")
                return session_count
        except Exception as e:
            logger.error(f"Error clearing all sessions: {str(e)}")
            return 0
    
    async def get_or_create_session(self, *, app_name: str, user_id: str, session_id: Optional[str] = None, 
                             default_state: Optional[Dict[str, Any]] = None) -> Session:
        """
        Get an existing session or create a new one with proper defaults.
        This is the centralized method that all agents should use for session management.
        
        Args:
            app_name: The application name
            user_id: The user ID
            session_id: Optional specific session ID to retrieve
            default_state: Optional default state to use when creating a new session
            
        Returns:
            Session: The existing or newly created session
        """
        try:
            if session_id:
                # Try to get specific session
                return await self.get_session(
                    app_name=app_name,
                    user_id=user_id,
                    session_id=session_id
                )
            else:
                # Get the most recent session for this user and app
                sessions = await self.list_sessions(app_name=app_name, user_id=user_id)
                if sessions:
                    return sessions[0]  # Most recent session
                raise ValueError("No sessions found")
        except Exception:
            # Session not found or no sessions exist, create a new one with proper defaults
            if default_state is None:
                default_state = {
                    "user_name": user_id,
                    "interaction_history": [],
                    "last_query": None,
                    "last_response": None,
                    "is_authenticated": False
                }
            
            logger.info(f"Creating new session for user {user_id} in app {app_name}")
            return await self.create_session(
                app_name=app_name,
                user_id=user_id,
                state=default_state
            )

# Helper to import time to avoid circular dependencies
def import_time():
    import time
    return time

# Create a singleton instance
session_service = SQLiteSessionService() 
