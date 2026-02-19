#!/usr/bin/env python
"""
Test script to demonstrate pushing messages with WebSocket broadcasting to UI.
"""

import sys
import os
import asyncio
import logging
from dotenv import load_dotenv

# Add parent directory to path to import lexedge modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_push():
    """Test pushing messages with WebSocket broadcasting."""
    print("🚀 Testing WebSocket Push to Active Session...")
    
    from lexedge.utils.agent_pusher import get_current_sessions_async, push_message_to_existing_session
    
    # Get current active sessions
    print("\n📋 Getting current sessions...")
    sessions = await get_current_sessions_async()
    
    if not sessions:
        print("❌ No active sessions found!")
        return
    
    print(f"✅ Found {len(sessions)} active sessions:")
    for i, session in enumerate(sessions):
        print(f"   {i+1}. Session: {session['session_id'][:8]}... (User: {session['user_id']})")
    
    # Use the first session
    target_session = sessions[0]
    session_id = target_session["session_id"]
    user_id = target_session["user_id"]
    
    print(f"\n🎯 Targeting session: {session_id[:8]}... (User: {user_id})")
    print("📡 This message will be broadcasted to any connected WebSocket clients!")
    
    # Push a test message WITH WebSocket broadcasting
    test_message = "🔥 URGENT: This is a test message pushed via Agent Pusher that should appear on the UI! Can you help me find software engineering jobs?"
    
    print(f"\n📤 Sending message with UI broadcast: {test_message}")
    
    result = await push_message_to_existing_session(
        message=test_message,
        session_id=session_id,
        user_id=user_id,
        broadcast_to_ui=True  # Enable WebSocket broadcasting
    )
    
    # Display results
    print(f"\n📊 Results:")
    if result["success"]:
        print(f"✅ Message sent successfully!")
        print(f"🔍 Session ID: {result['session_id']}")
        print(f"👤 User ID: {result['user_id']}")
        print(f"🤖 Agent: {result['agent_name']}")
        print(f"📡 Broadcast to UI: {result.get('broadcast_to_ui', False)}")
        print(f"📊 Session Existed: {result.get('session_existed', False)}")
        print(f"\n💬 Agent Response:")
        print(f"   {result['response']}")
        
        print(f"\n🌐 If you have the UI open (localhost:9000), you should see:")
        print(f"   1. Your message: '{test_message}'")
        print(f"   2. Agent's response: '{result['response'][:100]}...'")
    else:
        print(f"❌ Failed to send message!")
        print(f"   Error: {result.get('error', 'Unknown error')}")

async def test_multiple_broadcasts():
    """Test multiple messages with WebSocket broadcasting."""
    print("\n\n🔄 Testing Multiple WebSocket Broadcasts...")
    
    from lexedge.utils.agent_pusher import get_current_sessions_async, batch_push_messages
    
    # Get current sessions
    sessions = await get_current_sessions_async()
    
    if not sessions:
        print("❌ No active sessions found!")
        return
    
    # Use the first session
    target_session = sessions[0]
    session_id = target_session["session_id"]
    user_id = target_session["user_id"]
    
    print(f"🎯 Using session: {session_id[:8]}... (User: {user_id})")
    print("📡 These messages will be broadcasted to UI in real-time!")
    
    # Multiple test messages
    messages = [
        "🟢 Message 1: What remote software engineering positions are available?",
        "🟡 Message 2: Show me jobs with Python experience required", 
        "🔴 Message 3: What about senior-level roles with 5+ years experience?"
    ]
    
    print(f"\n📤 Sending {len(messages)} messages with UI broadcast...")
    
    results = await batch_push_messages(
        messages=messages,
        user_id=user_id,
        session_id=session_id,
        broadcast_to_ui=True  # Enable WebSocket broadcasting
    )
    
    # Display results
    print(f"\n📊 Batch Results:")
    for i, result in enumerate(results):
        print(f"\n   📨 Message {i+1}: {messages[i]}")
        if result["success"]:
            print(f"   ✅ Success")
            print(f"   💬 Response: {result['response'][:100]}...")
            print(f"   📡 Broadcasted to UI: {result.get('broadcast_to_ui', False)}")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
    
    print(f"\n🌐 Check your UI - you should see all messages appear in real-time!")

async def test_without_broadcast():
    """Test pushing messages WITHOUT WebSocket broadcasting for comparison."""
    print("\n\n🔇 Testing Push WITHOUT WebSocket Broadcasting...")
    
    from lexedge.utils.agent_pusher import get_current_sessions_async, push_message_to_existing_session
    
    # Get current sessions
    sessions = await get_current_sessions_async()
    
    if not sessions:
        print("❌ No active sessions found!")
        return
    
    # Use the first session
    target_session = sessions[0]
    session_id = target_session["session_id"]
    user_id = target_session["user_id"]
    
    print(f"🎯 Using session: {session_id[:8]}... (User: {user_id})")
    print("🔇 This message will NOT be broadcasted to UI (silent push)")
    
    # Push a test message WITHOUT WebSocket broadcasting
    test_message = "🔇 Silent message: This message should NOT appear on the UI - testing silent push"
    
    print(f"\n📤 Sending SILENT message: {test_message}")
    
    result = await push_message_to_existing_session(
        message=test_message,
        session_id=session_id,
        user_id=user_id,
        broadcast_to_ui=False  # Disable WebSocket broadcasting
    )
    
    # Display results
    print(f"\n📊 Results:")
    if result["success"]:
        print(f"✅ Message sent successfully (silently)!")
        print(f"🔇 Broadcast to UI: {result.get('broadcast_to_ui', False)}")
        print(f"💬 Agent Response: {result['response'][:100]}...")
        print(f"\n🌐 This message should NOT appear on the UI!")
    else:
        print(f"❌ Failed to send message!")
        print(f"   Error: {result.get('error', 'Unknown error')}")

async def main():
    """Main function to run all tests."""
    print("🌐 Starting WebSocket Broadcasting Tests...")
    print("📝 Make sure you have the UI open at http://localhost:9000 to see the broadcasts!")
    
    try:
        # Test single message with WebSocket broadcast
        await test_websocket_push()
        
        # Test multiple messages with WebSocket broadcast
        await test_multiple_broadcasts()
        
        # Test without broadcast for comparison
        await test_without_broadcast()
        
        print("\n🎉 WebSocket broadcasting tests completed!")
        print("🌐 Check your UI to see which messages appeared!")
        
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 
