#!/usr/bin/env python
# runner.py

import asyncio
import os
import sys
from dotenv import load_dotenv
from .agent_runner import run_agent
from .session import session_service, display_state

# Load environment variables
load_dotenv()

def print_welcome_message():
    """Print welcome message and session limits."""
    print("\n===== LexEdge Legal AI Agent Runner with SQLite Persistence =====")
    print(f"- Maximum {session_service.max_sessions_per_user} sessions per user")
    print(f"- Maximum {session_service.max_messages_per_session} messages per session")
    print(f"- Database: {session_service.db_path}")
    print("\nType 'exit' or 'quit' to end the conversation.")
    print("Type 'list' to see all your sessions.")
    print("Type 'resume <session_id>' to resume a previous session.")

def list_user_sessions(user_id):
    """List all sessions for a user."""
    try:
        sessions = session_service.list_sessions(user_id=user_id)
        if not sessions:
            print(f"\nNo sessions found for user '{user_id}'")
            return
        
        print(f"\n===== Sessions for user '{user_id}' =====")
        for i, session in enumerate(sessions, 1):
            print(f"{i}. Session ID: {session.id}")
            print(f"   App: {session.app_name}")
            if "last_query" in session.state and session.state["last_query"]:
                print(f"   Last query: {session.state['last_query']}")
            print(f"   Last updated: {session.last_update_time}")
            print()
    except Exception as e:
        print(f"Error listing sessions: {e}")

async def interactive_session():
    """Run an interactive session with the agent."""
    print_welcome_message()
    
    # Setup
    app_name = "lexedge"
    user_id = input("Enter your user ID: ").strip() or "default_user"
    session_id = None
    
    # Check if we have any command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_user_sessions(user_id)
            return
        elif len(sys.argv) > 2 and sys.argv[1] == "resume":
            session_id = sys.argv[2]
            try:
                # Verify session exists
                session = session_service.get_session(
                    app_name=app_name,
                    user_id=user_id,
                    session_id=session_id
                )
                print(f"\nResuming session: {session_id}")
                display_state(session_service, app_name, user_id, session_id, "Session State")
            except Exception as e:
                print(f"Error resuming session: {e}")
                session_id = None
    
    # Create new session if needed
    if not session_id:
        session = session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            state={
                "user_name": user_id,
                "interaction_history": [],
                "last_query": None,
                "last_response": None
            }
        )
        session_id = session.id
        print(f"\nCreated new session: {session_id}")
    
    print(f"User ID: {user_id}")
    print(f"Session ID: {session_id}")
    print("Ready for your queries!")
    
    # Main interaction loop
    while True:
        # Get user input
        user_input = input("\nYou: ").strip().lower()
        
        # Check for commands
        if user_input in ["exit", "quit", "q"]:
            print("Ending session. Goodbye!")
            break
        
        if user_input == "list":
            list_user_sessions(user_id)
            continue
        
        if user_input.startswith("resume "):
            parts = user_input.split(" ", 1)
            if len(parts) > 1:
                new_session_id = parts[1].strip()
                try:
                    # Verify session exists
                    session = session_service.get_session(
                        app_name=app_name,
                        user_id=user_id,
                        session_id=new_session_id
                    )
                    session_id = new_session_id
                    print(f"\nResuming session: {session_id}")
                    display_state(session_service, app_name, user_id, session_id, "Session State")
                    continue
                except Exception as e:
                    print(f"Error resuming session: {e}")
                    continue
        
        # Process through agent
        result = await run_agent(
            user_id=user_id,
            query=user_input,
            session_id=session_id,
            app_name=app_name
        )
        
        # Display response
        response = result.get("response", "No response received.")
        agent = result.get("agent", "Unknown")
        print(f"\n{agent}: {response}")

def main():
    """Main entry point."""
    try:
        asyncio.run(interactive_session())
    except KeyboardInterrupt:
        print("\nSession terminated by user.")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main() 