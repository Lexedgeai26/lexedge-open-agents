"""A minimal callback module to disable context and history.
"""

import logging
from typing import Optional, Any

from google.adk.agents.callback_context import CallbackContext
from google.genai import types

# Configure logger
logger = logging.getLogger(__name__)

def before_model_callback(callback_context: CallbackContext, llm_request: Any) -> Optional[types.Content]:
    """Callback before the model is called. Does nothing."""
    logger.info(f"[CONTEXT] Before model callback for {callback_context.agent_name}. No context will be injected.")
    return None

def after_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """Callback after the agent runs. Does nothing."""
    logger.info(f"[CONTEXT] After agent callback for {callback_context.agent_name}. No context will be saved.")
    return None

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """Callback before the agent runs. Does nothing."""
    logger.info(f"[CONTEXT] Before agent callback for {callback_context.agent_name}. No context will be loaded.")
    return None
