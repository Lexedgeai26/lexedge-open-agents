"""
Guardrail implementations for Appliview agents.

This module contains guardrail implementations for various agents in the Appliview system.
Guardrails are responsible for enforcing business rules and safety guidelines.
"""

import logging
import re
from typing import Optional, List

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types

try:
    # Package import
    from .config import COMPANY_INFO
except ImportError:
    # Direct import when running from applivew directory
    from config import COMPANY_INFO

logger = logging.getLogger(__name__)

# Define inappropriate language patterns
INAPPROPRIATE_PATTERNS = [
    r'\b(fuck|shit|ass|bitch|cunt|damn|dick|cock|pussy|asshole|whore|slut)\b',
    r'\b(sex|porn|explicit|nude|naked|erotic|XXX)\b',
    r'\b(kill|murder|attack|bomb|terrorist|suicide|weapon)\b',
    r'\b(illegal|hack|steal|drug|cocaine|heroin|meth)\b'
]

# Define company information keywords based on COMPANY_INFO dictionary
COMPANY_INFO_KEYWORDS = [
    COMPANY_INFO["name"].lower(),
    "company", "business", "organization", 
    "services", "product", "platform", "solution",
    "talent", "acquisition", "recruiting", "recruitment",
    "contact", "email", "phone", "address", "location",
    "founded", "founder", "founding", "history", "about",
    "mission", "vision", "values", "technology", "website", "url",
    "lexedge"
]

def extract_user_message(llm_request: LlmRequest) -> str:
    """
    Extract the last user message from an LLM request.
    
    Args:
        llm_request: The LLM request to extract from
        
    Returns:
        str: The extracted message or empty string if none found
    """
    # Initialize empty message
    user_message = ""
    
    # Extract user message from request contents
    if llm_request.contents and llm_request.contents[-1].role == 'user':
        if llm_request.contents[-1].parts:
            part_text = llm_request.contents[-1].parts[0].text
            if part_text is not None:  # Ensure text is not None
                user_message = part_text
    
    # Safety check - ensure we have a string
    if user_message is None or not isinstance(user_message, str):
        user_message = ""
        
    return user_message

def contains_inappropriate_language(text: str, patterns: List[str] = INAPPROPRIATE_PATTERNS) -> bool:
    """
    Check if text contains inappropriate language.
    
    Args:
        text: The text to check
        patterns: List of regex patterns for inappropriate content
        
    Returns:
        bool: True if inappropriate language is detected
    """
    if not text:
        return False
        
    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True
    
    return False

def is_company_info_query(text: str, keywords: List[str] = COMPANY_INFO_KEYWORDS) -> bool:
    """
    Check if a message is related to company information.
    
    Args:
        text: The text to check
        keywords: List of company-related keywords
        
    Returns:
        bool: True if the message is company-related
    """
    if not text:
        return False
        
    # If the message is very short, give it the benefit of the doubt
    if len(text.split()) <= 3:
        return True
        
    # Check if any company-related keywords are in the message
    text_lower = text.lower()
    
    # Define specific company info patterns
    company_patterns = [
        r'lexedge\s+(company|business|contact|info|information|details)',
        r'(company|business|contact)\s+lexedge',
        r'(about|tell me about)\s+lexedge',
        r'lexedge\'?s?\s+(address|phone|email|contact|founding|founders|history)',
        r'(address|phone|email|website|url)\s+of\s+lexedge',
        r'when\s+(was|is)\s+lexedge\s+founded',
        r'who\s+(founded|created|started|owns)\s+lexedge',
        r'^(what|who|where|when)\s+is\s+lexedge'
    ]
    
    # Define candidate search patterns to exclude from company info
    candidate_patterns = [
        r'(find|search|get|show|list|tell me about)\s+(candidate|candidates|applicant|applicants|resume|resumes)\s+(named|called|with name|with the name)\s+\w+',
        r'(find|search|get|show|list|tell me about)\s+\w+\s+(candidate|candidates|applicant|applicants|resume|resumes)',
        r'(candidate|applicant|resume)\s+(details|information|profile|data)\s+(for|of|about)\s+\w+',
        r'(details|information|profile|data)\s+(about|for|of)\s+\w+',
        r'(who is|tell me about|more about|information on|details on|profile of)\s+\w+\s+\w+',
        r'get\s+candidate\s+details',
        r'get\s+details\s+(for|about)\s+\w+',
        r'(show|find|search|get)\s+\w+\'?s\s+(profile|resume|details|information)',
        r'(show|find|search|get)\s+\w+\s+\w+\'?s\s+(profile|resume|details|information)'
    ]
    
    # Check if this is a candidate search query
    for pattern in candidate_patterns:
        if re.search(pattern, text_lower):
            # If it matches a candidate search pattern, it's not a company info query
            return False
    
    # Check for company info patterns
    for pattern in company_patterns:
        try:
            if re.search(pattern, text_lower):
                return True
        except Exception as e:
            logger.error(f"[Guardrail] Error matching pattern '{pattern}': {e}")
    
    # Check for keywords
    for keyword in keywords:
        if keyword in text_lower:
            return True
            
    return False

def lexedge_guardrail(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Guardrail implementation for Appliview that:
    1. Blocks inappropriate language
    2. Detects company information queries for proper handling
    3. Allows candidate name searches to proceed
    
    This callback runs before the model call and can block inappropriate queries
    by returning an LlmResponse object or allow the request to proceed by returning None.
    """
    agent_name = callback_context.agent_name
    logger.info(f"[Guardrail] Before model call for agent: {agent_name}")

    # Extract the last user message
    last_user_message = extract_user_message(llm_request)
    logger.info(f"[Guardrail] Inspecting user message: '{last_user_message}'")
    
    # Only proceed with checks if we have a non-empty message
    if not last_user_message:
        logger.warning("[Guardrail] Empty user message, proceeding with LLM call")
        return None
    
    # Check for inappropriate language - block this regardless of authentication
    if contains_inappropriate_language(last_user_message):
        logger.warning(f"[Guardrail] Inappropriate language detected")
        # Return an LlmResponse to skip the LLM call
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="I'm sorry, I cannot respond to questions containing inappropriate language. Please rephrase your question professionally.")],
            )
        )
    
    # Define candidate search patterns to allow through the guardrail
    candidate_patterns = [
        r'(find|search|get|show|list|tell me about)\s+(candidate|candidates|applicant|applicants|resume|resumes)\s+(named|called|with name|with the name)\s+\w+',
        r'(find|search|get|show|list|tell me about)\s+\w+\s+(candidate|candidates|applicant|applicants|resume|resumes)',
        r'(candidate|applicant|resume)\s+(details|information|profile|data)\s+(for|of|about)\s+\w+',
        r'(details|information|profile|data)\s+(about|for|of)\s+\w+',
        r'(who is|tell me about|more about|information on|details on|profile of)\s+\w+\s+\w+',
        r'get\s+candidate\s+details',
        r'get\s+details\s+(for|about)\s+\w+',
        r'(show|find|search|get)\s+\w+\'?s\s+(profile|resume|details|information)',
        r'(show|find|search|get)\s+\w+\s+\w+\'?s\s+(profile|resume|details|information)'
    ]
    
    # Check if this is a candidate search query
    text_lower = last_user_message.lower()
    for pattern in candidate_patterns:
        if re.search(pattern, text_lower):
            # If it matches a candidate search pattern, allow it to proceed
            logger.info("[Guardrail] Candidate search query detected - proceeding with LLM call")
            return None
    
    # Check if this is a company info query
    if is_company_info_query(last_user_message):
        logger.info("[Guardrail] Company information query detected - transferring to CompanyInfo agent")
        
        # Return a response that mimics the model calling the transfer_to_agent function
        # The response contains both text and a function call that will be parsed by the runner
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[
                    types.Part(text="I'll transfer you to our CompanyInfo agent to get information about Appliview."),
                    types.Part(
                        function_call=types.FunctionCall(
                            name="transfer_to_agent",
                            args={"agent_name": "lexedge_company_info"}
                        )
                    )
                ]
            )
        )
    
    # Allow the model call to proceed
    logger.info("[Guardrail] Proceeding with LLM call")
    return None

def company_info_guardrail(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Guardrail that enforces:
    1. Only company information related discussions are allowed
    2. No inappropriate or abusive language is permitted
    3. Allows candidate name searches to proceed
    
    This callback runs before the model call and can block the LLM call entirely
    by returning an LlmResponse object if guardrail conditions are violated.
    """
    agent_name = callback_context.agent_name
    logger.info(f"[Guardrail] Before model call for agent: {agent_name}")

    # Extract the last user message
    last_user_message = extract_user_message(llm_request)
    logger.info(f"[Guardrail] Inspecting user message: '{last_user_message}'")
    
    # Only proceed with checks if we have a non-empty message
    if not last_user_message:
        logger.warning("[Guardrail] Empty user message, proceeding with LLM call")
        return None
    
    # Check for inappropriate language
    if contains_inappropriate_language(last_user_message):
        logger.warning(f"[Guardrail] Inappropriate language detected")
        # Return an LlmResponse to skip the actual LLM call
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="I'm sorry, I can only respond to appropriate questions about Appliview company. Please rephrase your question in a professional manner.")],
            )
        )
    
    # Define candidate search patterns to allow through the guardrail
    candidate_patterns = [
        r'(find|search|get|show|list|tell me about)\s+(candidate|candidates|applicant|applicants|resume|resumes)\s+(named|called|with name|with the name)\s+\w+',
        r'(find|search|get|show|list|tell me about)\s+\w+\s+(candidate|candidates|applicant|applicants|resume|resumes)',
        r'(candidate|applicant|resume)\s+(details|information|profile|data)\s+(for|of|about)\s+\w+',
        r'(details|information|profile|data)\s+(about|for|of)\s+\w+',
        r'(who is|tell me about|more about|information on|details on|profile of)\s+\w+\s+\w+',
        r'get\s+candidate\s+details',
        r'get\s+details\s+(for|about)\s+\w+',
        r'(show|find|search|get)\s+\w+\'?s\s+(profile|resume|details|information)',
        r'(show|find|search|get)\s+\w+\s+\w+\'?s\s+(profile|resume|details|information)'
    ]
    
    # Check if this is a candidate search query
    text_lower = last_user_message.lower()
    for pattern in candidate_patterns:
        if re.search(pattern, text_lower):
            # If it matches a candidate search pattern, allow it to proceed
            logger.info("[Guardrail] Candidate search query detected - proceeding with LLM call")
            return None
    
    # Check if message is related to company information
    if not is_company_info_query(last_user_message):
        logger.warning(f"[Guardrail] Non-company related query detected")
        # Return an LlmResponse to skip the actual LLM call
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="I'm here to provide information about Appliview company. Please ask me something about Appliview, its services, contact information, or history.")],
            )
        )
    
    # Allow the LLM call to proceed by returning None
    logger.info("[Guardrail] Request passed guardrails, proceeding with LLM call")
    return None 