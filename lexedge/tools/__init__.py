"""
LexEdge Tools Package (Simplified)
"""

def generate_action_suggestions(**kwargs):
    return {"suggestions": []}

def format_response_with_clickable_links(text):
    return text

def login(*args, **kwargs):
    return {"status": "success", "token": "demo_token"}

def token_login(*args, **kwargs):
    return {"status": "success", "token": "demo_token", "user": {"id": "demo_user", "name": "Demo User"}}

def logout(*args, **kwargs):
    return {"status": "success"}

def get_available_agents_and_tools():
    return {}

from .welcome_message import generate_welcome_message

__all__ = [
    'generate_action_suggestions',
    'format_response_with_clickable_links',
    'login',
    'token_login',
    'logout',
    'get_available_agents_and_tools',
    'generate_welcome_message'
]
