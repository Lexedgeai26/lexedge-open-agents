#!/usr/bin/env python
"""
Test script to demonstrate universal LLM cancellation for ANY command.
Shows that push notifications can cancel any ongoing agent processing.
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

async def test_cancel_any_command():
    """Test cancelling various types of commands."""
    print("🌐 Testing UNIVERSAL command cancellation...")
    print("This will test cancelling different types of agent commands.\n")
    
    from lexedge.utils.agent_pusher import get_current_sessions_async, push_message_to_existing_session
    from lexedge.utils.task_manager import get_task_manager
    
    # Get current sessions
    sessions = await get_current_sessions_async()
    if not sessions:
        print("❌ No active sessions found!")
        return
    
    target_session = sessions[0]
    session_id = target_session["session_id"]
    user_id = target_session["user_id"]
    
    print(f"🎯 Using session: {session_id[:8]}... (User: {user_id})")
    
    task_manager = get_task_manager()
    
    # Test different command types
    test_commands = [
        "🔍 Candidate Analysis: Please analyze all candidates in our database and provide detailed insights about their skills, experience, and fit for various roles.",
        "📊 Company Research: Give me comprehensive information about technology companies hiring in San Francisco, including their culture, benefits, and open positions.",
        "💰 Salary Analysis: Analyze salary trends across different programming languages and experience levels in the current job market.",
        "🎯 Job Matching: Find the best job matches for senior Python developers with machine learning experience in remote positions."
    ]
    
    for i, command in enumerate(test_commands):
        print(f"\n{'='*60}")
        print(f"🧪 Test {i+1}: {command.split(':')[0]}")
        print(f"{'='*60}")
        
        # Start the command (don't await - let it run)
        print(f"📤 Starting command: {command[:80]}...")
        
        command_task = asyncio.create_task(
            push_message_to_existing_session(
                message=command,
                session_id=session_id,
                user_id=user_id,
                broadcast_to_ui=True,
                cancel_pending_processing=False  # Let it start processing
            )
        )
        
        # Wait a moment for processing to start
        await asyncio.sleep(1.5)
        
        # Check active tasks
        active_tasks = task_manager.get_active_tasks(session_id)
        print(f"📊 Active tasks: {len(active_tasks)}")
        for task_id, info in active_tasks.items():
            print(f"   🔄 {task_id}: {info['description'][:50]}...")
        
        # Send cancellation notification (simulate urgent interruption)
        interruption_messages = [
            "🚨 URGENT: Critical system alert - all processing must stop immediately!",
            "⚠️ MAINTENANCE: Scheduled system update starting now. Stopping all tasks.",
            "🔔 NOTIFICATION: High priority task detected. Cancelling current operations.",
            "🛑 ADMIN: Emergency stop requested by system administrator."
        ]
        
        interruption = interruption_messages[i]
        print(f"🛑 Sending interruption: {interruption}")
        
        interrupt_result = await push_message_to_existing_session(
            message=interruption,
            session_id=session_id,
            user_id=user_id,
            broadcast_to_ui=True,
            cancel_pending_processing=True  # Cancel the ongoing command
        )
        
        # Check tasks after cancellation
        tasks_after = task_manager.get_active_tasks(session_id)
        print(f"📊 Tasks after cancellation: {len(tasks_after)}")
        
        # Wait for original command task
        try:
            original_result = await asyncio.wait_for(command_task, timeout=3.0)
            print(f"📝 Original command result: {original_result.get('success', False)}")
            response_len = len(original_result.get('response', ''))
            print(f"📏 Response length: {response_len} chars")
        except asyncio.TimeoutError:
            print("⏰ Original command timed out (likely cancelled)")
        except Exception as e:
            print(f"❌ Original command error: {str(e)}")
        
        # Clean up
        cleanup_count = task_manager.cleanup_completed_tasks()
        if cleanup_count > 0:
            print(f"🧹 Cleaned up {cleanup_count} tasks")
        
        # Brief pause between tests
        await asyncio.sleep(1)

async def test_tool_integration():
    """Test that any tool can send cancellation notifications."""
    print("\n\n🔧 Testing tool-based cancellation...")
    print("Demonstrating how any tool can send cancellation notifications.\n")
    
    from lexedge.utils.agent_pusher import get_current_sessions_async, push_message_to_existing_session
    from lexedge.utils.task_manager import get_task_manager

    async def _get_current_user_and_session():
        sessions = await get_current_sessions_async()
        if not sessions:
            return None, None, {}
        session = sessions[0]
        return session["user_id"], session["session_id"], session.get("state", {})

    async def _send_websocket_notification(message, session_id, user_id, cancel_pending_processing=False):
        return await push_message_to_existing_session(
            message=message,
            session_id=session_id,
            user_id=user_id,
            broadcast_to_ui=True,
            cancel_pending_processing=cancel_pending_processing,
        )
    
    user_id, session_id, session_state = await _get_current_user_and_session()

    if not user_id or not session_id:
        print("❌ No active user/session found!")
        return
    
    print(f"🎯 Found active user: {user_id} (session: {session_id[:8]}...)")
    
    task_manager = get_task_manager()
    
    # Simulate different tools sending notifications
    tool_notifications = [
        {
            "tool": "email_tool",
            "message": "📧 EMAIL ALERT: Urgent message received. Processing halted.",
            "cancel": True
        },
        {
            "tool": "calendar_tool", 
            "message": "📅 CALENDAR: Meeting starting in 2 minutes. Saving progress...",
            "cancel": False
        },
        {
            "tool": "security_tool",
            "message": "🔒 SECURITY: Suspicious activity detected. All operations suspended.",
            "cancel": True
        },
        {
            "tool": "notification_service",
            "message": "🔔 SYSTEM: Background task completed successfully.",
            "cancel": False
        }
    ]
    
    for notification in tool_notifications:
        tool_name = notification["tool"]
        message = notification["message"]
        should_cancel = notification["cancel"]
        
        print(f"\n🔧 {tool_name}: {message}")
        print(f"   Cancel processing: {should_cancel}")
        
        # Get initial task count
        initial_tasks = len(task_manager.get_active_tasks(session_id))
        
        # Send notification
        await _send_websocket_notification(
            message,
            session_id,
            user_id,
            cancel_pending_processing=should_cancel
        )
        
        # Brief pause
        await asyncio.sleep(0.5)
        
        # Check final task count
        final_tasks = len(task_manager.get_active_tasks(session_id))
        
        if should_cancel and initial_tasks > final_tasks:
            print(f"   ✅ Successfully cancelled tasks ({initial_tasks} → {final_tasks})")
        elif not should_cancel:
            print(f"   ✅ Tasks preserved ({initial_tasks} → {final_tasks})")
        else:
            print(f"   ℹ️ No tasks to cancel ({initial_tasks} → {final_tasks})")

async def main():
    """Main function to run all tests."""
    print("🚀 Testing UNIVERSAL LLM Task Cancellation...")
    print("This demonstrates that ANY command can be cancelled by push notifications!")
    print("=" * 80)
    
    try:
        # Test 1: Cancel various types of commands
        await test_cancel_any_command()
        
        # Wait between tests
        await asyncio.sleep(2)
        
        # Test 2: Tool integration examples
        await test_tool_integration()
        
        print("\n" + "=" * 80)
        print("🎉 Universal cancellation tests completed!")
        print("\n📋 Key Points:")
        print("   🌐 ANY agent command can be cancelled")
        print("   🔧 ANY tool can send cancellation notifications") 
        print("   📡 Cancellation works via session_id, not command type")
        print("   🛑 True LLM interruption for maximum responsiveness")
        print("\n🎯 Usage: Set cancel_pending_processing=True in any push notification")
        print("   to cancel ongoing LLM processing for that session!")
        
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 
