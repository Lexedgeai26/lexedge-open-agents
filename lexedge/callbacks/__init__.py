"""
Callback handlers for agent events.
"""

# Callbacks package for Appliview agent system

# Import callback implementations
from .login import after_login_callback, BeforeLoginCallback, AfterLoginCallback

__all__ = ["after_login_callback", "BeforeLoginCallback", "AfterLoginCallback"] 