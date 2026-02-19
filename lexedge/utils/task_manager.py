#!/usr/bin/env python
"""
Task manager for tracking and canceling active agent processing tasks.
"""

import asyncio
import logging
import threading
import time
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ActiveTask:
    """Represents an active agent processing task."""
    task_id: str
    session_id: str
    user_id: str
    task: asyncio.Task
    created_at: float
    description: str

class TaskManager:
    """Manages active agent processing tasks for cancellation."""
    
    def __init__(self):
        self._active_tasks: Dict[str, ActiveTask] = {}
        self._session_tasks: Dict[str, Set[str]] = {}  # session_id -> set of task_ids
        self._lock = threading.Lock()
    
    def register_task(
        self, 
        task_id: str, 
        session_id: str, 
        user_id: str, 
        task: asyncio.Task, 
        description: str = "Agent processing"
    ) -> None:
        """Register a new active task."""
        with self._lock:
            active_task = ActiveTask(
                task_id=task_id,
                session_id=session_id,
                user_id=user_id,
                task=task,
                created_at=time.time(),
                description=description
            )
            
            self._active_tasks[task_id] = active_task
            
            # Track tasks by session
            if session_id not in self._session_tasks:
                self._session_tasks[session_id] = set()
            self._session_tasks[session_id].add(task_id)
            
            logger.info(f"📋 Registered task {task_id} for session {session_id[:8]}... ({description})")
    
    def unregister_task(self, task_id: str) -> None:
        """Unregister a completed task."""
        with self._lock:
            if task_id in self._active_tasks:
                active_task = self._active_tasks[task_id]
                session_id = active_task.session_id
                
                # Remove from active tasks
                del self._active_tasks[task_id]
                
                # Remove from session tasks
                if session_id in self._session_tasks:
                    self._session_tasks[session_id].discard(task_id)
                    if not self._session_tasks[session_id]:
                        del self._session_tasks[session_id]
                
                logger.info(f"📋 Unregistered task {task_id}")
    
    def cancel_session_tasks(self, session_id: str, reason: str = "Cancelled by user") -> int:
        """Cancel all active tasks for a session."""
        cancelled_count = 0
        
        with self._lock:
            task_ids_to_cancel = self._session_tasks.get(session_id, set()).copy()
        
        for task_id in task_ids_to_cancel:
            if self.cancel_task(task_id, reason):
                cancelled_count += 1
        
        logger.info(f"🛑 Cancelled {cancelled_count} tasks for session {session_id[:8]}...")
        return cancelled_count
    
    def cancel_task(self, task_id: str, reason: str = "Cancelled by user") -> bool:
        """Cancel a specific task."""
        with self._lock:
            if task_id not in self._active_tasks:
                return False
            
            active_task = self._active_tasks[task_id]
            task = active_task.task
        
        try:
            if not task.done():
                task.cancel()
                logger.info(f"🛑 Cancelled task {task_id}: {reason}")
                return True
            else:
                logger.debug(f"Task {task_id} already completed")
                return False
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {str(e)}")
            return False
    
    def get_active_tasks(self, session_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Get information about active tasks."""
        with self._lock:
            tasks_info = {}
            
            for task_id, active_task in self._active_tasks.items():
                if session_id is None or active_task.session_id == session_id:
                    tasks_info[task_id] = {
                        "session_id": active_task.session_id,
                        "user_id": active_task.user_id,
                        "description": active_task.description,
                        "created_at": active_task.created_at,
                        "age_seconds": time.time() - active_task.created_at,
                        "is_done": active_task.task.done(),
                        "is_cancelled": active_task.task.cancelled()
                    }
            
            return tasks_info
    
    def cleanup_completed_tasks(self) -> int:
        """Clean up completed/cancelled tasks."""
        completed_count = 0
        
        with self._lock:
            task_ids_to_remove = []
            
            for task_id, active_task in self._active_tasks.items():
                if active_task.task.done():
                    task_ids_to_remove.append(task_id)
        
        for task_id in task_ids_to_remove:
            self.unregister_task(task_id)
            completed_count += 1
        
        if completed_count > 0:
            logger.debug(f"🧹 Cleaned up {completed_count} completed tasks")
        
        return completed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task manager statistics."""
        with self._lock:
            active_count = len(self._active_tasks)
            session_count = len(self._session_tasks)
            
            # Calculate age distribution
            current_time = time.time()
            ages = [current_time - task.created_at for task in self._active_tasks.values()]
            
            return {
                "active_tasks": active_count,
                "active_sessions": session_count,
                "oldest_task_age": max(ages) if ages else 0,
                "newest_task_age": min(ages) if ages else 0,
                "average_task_age": sum(ages) / len(ages) if ages else 0
            }

# Global task manager instance
task_manager = TaskManager()

def get_task_manager() -> TaskManager:
    """Get the global task manager instance."""
    return task_manager 