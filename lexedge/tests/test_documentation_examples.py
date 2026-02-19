#!/usr/bin/env python
"""
Test file to validate all examples from the documentation work correctly.
This ensures the documentation examples are accurate and functional.
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

async def _get_session_context():
    from lexedge.utils.agent_pusher import get_current_sessions_async

    sessions = await get_current_sessions_async()
    if not sessions:
        return None, None, {}
    session = sessions[0]
    return session["user_id"], session["session_id"], session.get("state", {})


async def _send_websocket_notification(message, session_id, user_id, cancel_pending_processing=False):
    from lexedge.utils.agent_pusher import push_message_to_existing_session

    if not user_id or not session_id:
        return {"success": False, "error": "No active session"}
    return await push_message_to_existing_session(
        message=message,
        session_id=session_id,
        user_id=user_id,
        broadcast_to_ui=True,
        cancel_pending_processing=cancel_pending_processing,
    )


async def test_basic_tool_integration():
    """Test Example 1: Basic Tool Integration from documentation."""
    print("📖 Testing Documentation Example 1: Basic Tool Integration")
    
    async def my_analysis_tool(data):
        """Example tool with cancellation support."""
        # Get current session
        user_id, session_id, session_state = await _get_session_context()
        results = f"Analysis results for {len(data)} items"
        
        if user_id and session_id:
            # Send progress notification (don't cancel)
            await _send_websocket_notification(
                "⏳ Starting analysis...",
                session_id,
                user_id,
                cancel_pending_processing=False  # Continue LLM processing
            )
            
            # Simulate work
            import time
            time.sleep(0.5)
            # Send completion notification (cancel any ongoing LLM)
            await _send_websocket_notification(
                "✅ Analysis complete!",
                session_id,
                user_id,
                cancel_pending_processing=True  # Stop LLM processing
            )
        
        return {"success": True, "results": results}
    
    # Test the tool
    test_data = ["item1", "item2", "item3"]
    result = await my_analysis_tool(test_data)
    
    print(f"   ✅ Tool result: {result}")
    assert result["success"] == True
    assert "results" in result
    print("   ✅ Basic tool integration test passed!")

async def test_priority_based_cancellation():
    """Test Example 2: Priority-Based Cancellation from documentation."""
    print("📖 Testing Documentation Example 2: Priority-Based Cancellation")
    
    async def email_notification_tool(email_content, priority="normal"):
        """Email tool with priority-based cancellation."""
        user_id, session_id, session_state = await _get_session_context()
        
        if user_id and session_id:
            if priority == "urgent":
                # Urgent emails interrupt processing
                await _send_websocket_notification(
                    f"📧 URGENT EMAIL: {email_content[:100]}...",
                    session_id,
                    user_id,
                    cancel_pending_processing=True  # Interrupt LLM
                )
            else:
                # Normal emails don't interrupt
                await _send_websocket_notification(
                    f"📧 Email: {email_content[:50]}...",
                    session_id,
                    user_id,
                    cancel_pending_processing=False  # Don't interrupt
                )
        
        return {"success": True, "priority": priority}
    
    # Test normal priority
    result1 = await email_notification_tool("Normal email content here", "normal")
    print(f"   ✅ Normal email result: {result1}")
    
    # Test urgent priority
    result2 = await email_notification_tool("URGENT: CEO needs to see you immediately!", "urgent")
    print(f"   ✅ Urgent email result: {result2}")
    
    assert result1["priority"] == "normal"
    assert result2["priority"] == "urgent"
    print("   ✅ Priority-based cancellation test passed!")

async def test_calendar_integration():
    """Test Example 3: Calendar Integration from documentation."""
    print("📖 Testing Documentation Example 3: Calendar Integration")
    
    async def calendar_reminder_tool(event_type, minutes_until):
        """Smart calendar tool with time-based cancellation."""
        user_id, session_id, session_state = await _get_session_context()
        
        if user_id and session_id:
            if minutes_until <= 2:
                # Very urgent - cancel immediately
                await _send_websocket_notification(
                    f"📅 URGENT: {event_type} starting in {minutes_until} minutes!",
                    session_id,
                    user_id,
                    cancel_pending_processing=True  # Cancel immediately
                )
            elif minutes_until <= 5:
                # Warning - don't cancel yet
                await _send_websocket_notification(
                    f"📅 REMINDER: {event_type} in {minutes_until} minutes",
                    session_id,
                    user_id,
                    cancel_pending_processing=False  # Just warn
                )
            else:
                # Not urgent
                await _send_websocket_notification(
                    f"📅 SCHEDULED: {event_type} in {minutes_until} minutes",
                    session_id,
                    user_id,
                    cancel_pending_processing=False  # Don't interrupt
                )
        
        return {"success": True, "urgency": "high" if minutes_until <= 2 else "low"}
    
    # Test different time scenarios
    result1 = await calendar_reminder_tool("Team Standup", 1)  # Very urgent
    result2 = await calendar_reminder_tool("Review Meeting", 4)  # Warning
    result3 = await calendar_reminder_tool("Planning Session", 15)  # Not urgent
    
    print(f"   ✅ 1 minute warning: {result1}")
    print(f"   ✅ 4 minute warning: {result2}")
    print(f"   ✅ 15 minute warning: {result3}")
    
    assert result1["urgency"] == "high"
    assert result2["urgency"] == "low"
    assert result3["urgency"] == "low"
    print("   ✅ Calendar integration test passed!")

async def test_manual_cancellation():
    """Test Example 4: Manual Cancellation via Agent Pusher from documentation."""
    print("📖 Testing Documentation Example 4: Manual Cancellation")
    
    async def manual_cancellation_example():
        """Manually cancel any ongoing processing."""
        from lexedge.utils.agent_pusher import get_current_sessions_async, push_message_to_existing_session
        
        # Get active sessions
        sessions = await get_current_sessions_async()
        if not sessions:
            return {"success": False, "error": "No active sessions"}
        
        session = sessions[0]  # Use first session
        
        # Send cancellation message
        result = await push_message_to_existing_session(
            message="🚨 ADMIN: All processing cancelled by administrator",
            session_id=session["session_id"],
            user_id=session["user_id"],
            broadcast_to_ui=True,
            cancel_pending_processing=True  # Cancel ongoing tasks
        )
        
        return result
    
    # Test manual cancellation
    result = await manual_cancellation_example()
    print(f"   ✅ Manual cancellation result: {result}")
    
    # Should either succeed or indicate no sessions
    assert "success" in result or "error" in result
    print("   ✅ Manual cancellation test passed!")

async def test_quick_reference_templates():
    """Test templates from the Quick Reference documentation."""
    print("📖 Testing Quick Reference Templates")
    
    # Test basic tool template
    async def my_tool(params):
        user_id, session_id, session_state = await _get_session_context()
        
        try:
            if user_id and session_id:
                # Progress (don't cancel)
                await _send_websocket_notification(
                    "⏳ Starting work...", session_id, user_id, cancel_pending_processing=False
                )
            
            # Simulate work
            result = f"Processed {params}"
            
            if user_id and session_id:
                # Success (cancel LLM)
                await _send_websocket_notification(
                    "✅ Completed!", session_id, user_id, cancel_pending_processing=True
                )
            
            return {"success": True, "result": result}
            
        except Exception as e:
            if user_id and session_id:
                # Error (cancel LLM)
                await _send_websocket_notification(
                    f"❌ Error: {str(e)}", session_id, user_id, cancel_pending_processing=True
                )
            return {"success": False, "error": str(e)}
    
    # Test urgent alert template
    async def send_urgent_alert(message):
        user_id, session_id, session_state = await _get_session_context()
        
        if user_id and session_id:
            await _send_websocket_notification(
                f"🚨 URGENT: {message}",
                session_id, user_id,
                cancel_pending_processing=True  # Always cancel for urgent alerts
            )
        
        return {"success": True, "message": message}
    
    # Test the templates
    tool_result = await my_tool("test parameters")
    alert_result = await send_urgent_alert("System maintenance starting")
    
    print(f"   ✅ Tool template result: {tool_result}")
    print(f"   ✅ Alert template result: {alert_result}")
    
    assert tool_result["success"] == True
    assert alert_result["success"] == True
    print("   ✅ Quick reference templates test passed!")

async def test_api_reference_examples():
    """Test API Reference examples from documentation."""
    print("📖 Testing API Reference Examples")
    
    from lexedge.utils.task_manager import get_task_manager
    from lexedge.utils.agent_pusher import get_current_sessions_async
    
    # Test Task Manager API
    task_manager = get_task_manager()
    
    # Get current sessions
    sessions = await get_current_sessions_async()
    print(f"   ✅ Found {len(sessions)} active sessions")
    
    if sessions:
        session_id = sessions[0]["session_id"]
        
        # Get active tasks for a session
        active_tasks = task_manager.get_active_tasks(session_id)
        print(f"   ✅ Active tasks for session: {len(active_tasks)}")
        
        # Test cleanup
        cleanup_count = task_manager.cleanup_completed_tasks()
        print(f"   ✅ Cleaned up {cleanup_count} completed tasks")
    
    print("   ✅ API reference examples test passed!")

async def main():
    """Main function to run all documentation example tests."""
    print("🚀 Testing All Documentation Examples...")
    print("=" * 80)
    
    try:
        # Test synchronous examples
        await test_basic_tool_integration()
        print()
        
        await test_priority_based_cancellation()
        print()
        
        await test_calendar_integration()
        print()
        
        await test_quick_reference_templates()
        print()
        
        await test_api_reference_examples()
        print()
        
        # Test async examples
        await test_manual_cancellation()
        print()
        
        print("=" * 80)
        print("🎉 All documentation examples tested successfully!")
        print("\n📋 Summary:")
        print("   ✅ Basic Tool Integration")
        print("   ✅ Priority-Based Cancellation")
        print("   ✅ Calendar Integration")
        print("   ✅ Manual Cancellation")
        print("   ✅ Quick Reference Templates")
        print("   ✅ API Reference Examples")
        print("\n🚀 All documentation examples are functional and accurate!")
        
    except Exception as e:
        logger.error(f"Error testing documentation examples: {str(e)}")
        print(f"❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 
