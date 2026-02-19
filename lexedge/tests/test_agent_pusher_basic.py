#!/usr/bin/env python
"""
Test script to demonstrate the agent pusher utility functions.
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

def test_single_message():
    """Test pushing a single message to the agent."""
    print("\n=== Testing Single Message Push ===")
    
    from lexedge.utils.agent_pusher import push_message_to_agent
    
    # Test message
    message = "Hello, who are you?"
    
    # Push message to agent
    result = asyncio.run(push_message_to_agent(message))
    
    if result["success"]:
        print(f"✅ Message sent successfully!")
        print(f"📝 Message: {result['message']}")
        print(f"🤖 Agent: {result['agent_name']}")
        print(f"💬 Response: {result['response'][:200]}...")
        print(f"🔍 Session ID: {result['session_id']}")
    else:
        print(f"❌ Failed to send message: {result['error']}")

def test_batch_messages():
    """Test pushing multiple messages to the agent."""
    print("\n=== Testing Batch Message Push ===")
    
    from lexedge.utils.agent_pusher import batch_push_messages
    
    # Test messages
    messages = [
        "Hello, who are you?",
        "Can you help me find a job?",
        "Show me all available jobs"
    ]
    
    # Push messages to agent
    results = asyncio.run(batch_push_messages(messages))
    
    print(f"📦 Batch processed {len(results)} messages:")
    
    for i, result in enumerate(results):
        if result["success"]:
            print(f"✅ Message {i+1}: Success")
            print(f"   📝 Query: {result['message']}")
            print(f"   💬 Response: {result['response'][:100]}...")
        else:
            print(f"❌ Message {i+1}: Failed - {result['error']}")

def test_session_creation():
    """Test creating a session with multiple messages."""
    print("\n=== Testing Session Creation with Messages ===")
    
    from lexedge.utils.agent_pusher import create_test_session_with_messages
    
    # Test messages to build conversation context
    messages = [
        "Hello, I'm looking for a job",
        "I'm interested in software engineering positions",
        "What jobs are available?"
    ]
    
    # Create session with messages
    result = asyncio.run(create_test_session_with_messages(messages))
    
    if result["success"]:
        print(f"✅ Session created successfully!")
        print(f"📊 Messages sent: {result['messages_sent']}")
        print(f"✅ Successful: {result['successful_messages']}")
        print(f"❌ Failed: {result['failed_messages']}")
        
        if result["session_info"]:
            session_info = result["session_info"]
            print(f"🔍 Session ID: {session_info['session_id']}")
            print(f"👤 User ID: {session_info['user_id']}")
            print(f"🤖 Agent: {session_info['agent_name']}")
            
        # Show last response
        successful_results = [r for r in result["results"] if r.get("success")]
        if successful_results:
            last_result = successful_results[-1]
            print(f"💬 Last Response: {last_result['response'][:200]}...")
    else:
        print(f"❌ Failed to create session: {result['error']}")

def main():
    """Main function to run all tests."""
    print("🚀 Starting Agent Pusher Tests...")
    
    try:
        # Test single message
        test_single_message()
        
        # Test batch messages  
        test_batch_messages()
        
        # Test session creation
        test_session_creation()
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    main() 
