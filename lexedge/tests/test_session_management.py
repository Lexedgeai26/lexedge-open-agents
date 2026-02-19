#!/usr/bin/env python
"""
Test script to demonstrate getting current sessions and pushing messages to existing sessions.
"""

import sys
import os
import logging
import asyncio
from dotenv import load_dotenv

# Add parent directory to path to import lexedge modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_get_current_sessions():
    """Test getting current sessions from the session service."""
    print("\n=== Getting Current Sessions ===")
    
    from lexedge.utils.agent_pusher import get_current_sessions
    
    # Get all sessions
    all_sessions = get_current_sessions()
    print(f"📊 Total sessions found: {len(all_sessions)}")
    
    for i, session in enumerate(all_sessions):
        print(f"🔍 Session {i+1}:")
        print(f"   📝 ID: {session['session_id']}")
        print(f"   👤 User: {session['user_id']}")
        print(f"   📱 App: {session['app_name']}")
        print(f"   ⏰ Created: {session.get('created_at', 'Unknown')}")
        
        # Show some state info if available
        state = session.get('state', {})
        if isinstance(state, dict):
            last_query = state.get('last_query')
            if last_query:
                print(f"   💬 Last Query: {last_query[:50]}...")
    
    return all_sessions

def test_push_to_existing_session():
    """Test pushing a message to an existing session."""
    print("\n=== Testing Push to Existing Session ===")
    
    from lexedge.utils.agent_pusher import (
        get_current_sessions,
        push_message_to_existing_session,
        push_message_to_agent,
    )
    
    # Get current sessions
    sessions = get_current_sessions()
    
    if not sessions:
        print("❌ No existing sessions found. Creating a test session first...")
        # Create a session first
        result = asyncio.run(push_message_to_agent("Hello, this is a test", user_id="test_user"))
        if result["success"]:
            session_id = result["session_id"]
            user_id = result["user_id"]
        else:
            print(f"❌ Failed to create test session: {result.get('error')}")
            return
    else:
        # Use the first existing session
        session_id = sessions[0]["session_id"]
        user_id = sessions[0]["user_id"]
        print(f"✅ Using existing session: {session_id}")
    
    # Push a message to the existing session
    test_message = "This is a test message pushed to an existing session"
    result = asyncio.run(
        push_message_to_existing_session(
            message=test_message,
            session_id=session_id,
            user_id=user_id
        )
    )
    
    if result["success"]:
        print(f"✅ Message sent successfully to existing session!")
        print(f"📝 Message: {result['message']}")
        print(f"🤖 Agent: {result['agent_name']}")
        print(f"💬 Response: {result['response'][:200]}...")
        print(f"🔍 Session ID: {result['session_id']}")
        print(f"📊 Session Existed: {result.get('session_existed', False)}")
    else:
        print(f"❌ Failed to send message: {result['error']}")

def test_batch_with_existing_session():
    """Test batch messages with an existing session."""
    print("\n=== Testing Batch Messages with Existing Session ===")
    
    from lexedge.utils.agent_pusher import get_current_sessions, batch_push_messages
    
    # Get current sessions
    sessions = get_current_sessions()
    
    if sessions:
        session_id = sessions[0]["session_id"]
        user_id = sessions[0]["user_id"]
        print(f"✅ Using existing session: {session_id}")
    else:
        session_id = None
        user_id = "test_user"
        print("📝 No existing sessions, will create new one")
    
    # Test messages
    messages = [
        "Hello, I'm continuing our conversation",
        "Can you help me with job search?",
        "What positions are currently available?"
    ]
    
    # Send batch messages
    results = asyncio.run(
        batch_push_messages(
            messages=messages,
            user_id=user_id,
            session_id=session_id
        )
    )
    
    print(f"📦 Batch processed {len(results)} messages:")
    
    for i, result in enumerate(results):
        if result["success"]:
            print(f"✅ Message {i+1}: Success")
            print(f"   📝 Query: {result['message']}")
            print(f"   💬 Response: {result['response'][:100]}...")
            print(f"   🔍 Session: {result['session_id']}")
            if 'session_existed' in result:
                print(f"   📊 Used existing session: {result['session_existed']}")
        else:
            print(f"❌ Message {i+1}: Failed - {result['error']}")

def test_session_filtering():
    """Test getting sessions filtered by user."""
    print("\n=== Testing Session Filtering ===")
    
    from lexedge.utils.agent_pusher import get_current_sessions
    
    # Test different user filters
    test_users = ["test_user", "chirag", "system_user"]
    
    for user in test_users:
        sessions = get_current_sessions(user_id=user)
        print(f"👤 User '{user}': {len(sessions)} sessions")
        
        for session in sessions[:3]:  # Show first 3
            print(f"   🔍 {session['session_id'][:8]}...")

def main():
    """Main function to run all tests."""
    print("🚀 Starting Current Session Tests...")
    
    try:
        # Test getting current sessions
        sessions = test_get_current_sessions()
        
        # Test pushing to existing session
        test_push_to_existing_session()
        
        # Test batch messages with existing session
        test_batch_with_existing_session()
        
        # Test session filtering
        test_session_filtering()
        
        print("\n🎉 All session tests completed!")
        
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    main() 
