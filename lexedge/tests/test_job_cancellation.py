#!/usr/bin/env python
"""Simple test for job tool cancellation functionality."""

import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lexedge.utils.agent_pusher import get_current_sessions, push_message_to_existing_session


def _get_current_user_and_session():
    sessions = get_current_sessions()
    if not sessions:
        return None, None, {}
    session = sessions[0]
    return session["user_id"], session["session_id"], session.get("state", {})


def _send_websocket_notification_sync(message, session_id, user_id, cancel_pending_processing=False):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            push_message_to_existing_session(
                message=message,
                session_id=session_id,
                user_id=user_id,
                broadcast_to_ui=True,
                cancel_pending_processing=cancel_pending_processing,
            )
        )
    loop.create_task(
        push_message_to_existing_session(
            message=message,
            session_id=session_id,
            user_id=user_id,
            broadcast_to_ui=True,
            cancel_pending_processing=cancel_pending_processing,
        )
    )
    return {"success": True, "scheduled": True}

def test_job_notifications():
    print("🧪 Testing job tool notifications...")
    
    # Get current user and session
    user_id, session_id, state = _get_current_user_and_session()
    print(f"📍 Found user: {user_id}, session: {session_id[:8] if session_id else None}...")
    
    if not user_id or not session_id:
        print("❌ No active session found")
        return
    
    # Test progress notification (don't cancel)
    print("📤 Sending progress notification (CONTINUE)...")
    _send_websocket_notification_sync(
        "⏳ Fetching jobs from database...", 
        session_id, 
        user_id, 
        cancel_pending_processing=False
    )
    
    # Test completion notification (cancel any pending)
    print("📤 Sending completion notification (CANCEL)...")
    _send_websocket_notification_sync(
        "✅ Job search complete! Found 15 positions.", 
        session_id, 
        user_id, 
        cancel_pending_processing=True
    )
    
    print("✅ Job notification test completed!")

if __name__ == "__main__":
    test_job_notifications() 
