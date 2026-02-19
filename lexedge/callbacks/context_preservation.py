"""
Context preservation callbacks for agent interactions.

These callbacks ensure that context is maintained between agent transfers,
allowing for more natural and coherent conversations.
"""

import json
import logging
import re
from typing import Optional, Dict, Any, List

from google.adk.agents.callback_context import CallbackContext
from google.genai import types

logger = logging.getLogger(__name__)

def before_model_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Before model callback that loads relevant context for the current model.
    
    This callback runs before an agent processes a request and loads any
    stored context for the agent from previous interactions.
    
    Args:
        callback_context: The context for the callback with access to session state
        
    Returns:
        Optional[types.Content]: None to allow normal processing
    """
    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    logger.info(f"[CALLBACK] Before agent callback triggered for {agent_name} in invocation {invocation_id}")
    
    # Get user message
    user_message = extract_user_message(callback_context)
    if not user_message:
        return None
    
    # Always inject context for all queries, not just follow-up questions
    # This ensures context is maintained across all interactions
    
    # For candidate search agent, always include candidate context
    if agent_name == "lexedge_candidate_search":
        # Try to get candidate list from state or global context
        candidate_list = callback_context.state.get("candidate_list")
        if not candidate_list:
            # Try to get from global context
            agent_context = agent_context_manager.get_context(agent_name)
            if agent_context:
                candidate_list = agent_context.get("candidate_list")
        
        # If we have a candidate list, include it in the prompt
        if candidate_list:
            logger.info(f"[CALLBACK] Found candidate list with {len(candidate_list) if isinstance(candidate_list, list) else 'unknown'} candidates")
            
            # Format candidate list as a string
            formatted_candidates = "\n\nAvailable candidates:\n" + candidate_list if isinstance(candidate_list, str) else "\n\nAvailable candidates: [candidate data available]"
            
            # Modify the request to include the candidate list
            modified_message = f"{formatted_candidates}\n\nUser query: {user_message}"
            
            # Store the modified message in the state
            callback_context.state["modified_user_message"] = modified_message
            logger.info(f"[CALLBACK] Added candidate list to user message")
        
        # Check for specific candidate context
        current_candidate = callback_context.state.get("current_candidate")
        if not current_candidate:
            # Try to get from global context
            agent_context = agent_context_manager.get_context(agent_name)
            if agent_context:
                current_candidate = agent_context.get("current_candidate")
        
        # If we have a specific candidate, include it in the prompt
        if current_candidate and isinstance(current_candidate, dict):
            logger.info(f"[CALLBACK] Found specific candidate info: {list(current_candidate.keys()) if isinstance(current_candidate, dict) else 'non-dict'}")
            
            # Format candidate info
            formatted_candidate = format_candidate_context(current_candidate)
            
            # Get existing modified message or use original
            existing_message = callback_context.state.get("modified_user_message", user_message)
            
            # Add candidate info to the message
            modified_message = f"Current candidate details:\n{formatted_candidate}\n\nUser query: {user_message}"
            
            # Store the modified message in the state
            callback_context.state["modified_user_message"] = modified_message
            callback_context.state["current_candidate"] = current_candidate
            logger.info(f"[CALLBACK] Added specific candidate info to user message")
    
    # For job search agent, always include job context
    elif agent_name == "lexedge_job_search":
        # Similar implementation for job context
        current_job = callback_context.state.get("current_job")
        if current_job and isinstance(current_job, dict):
            formatted_job = format_job_context(current_job)
            modified_message = f"Current job details:\n{formatted_job}\n\nUser query: {user_message}"
            callback_context.state["modified_user_message"] = modified_message
    
    # For company info agent, always include company context
    elif agent_name == "lexedge_company_info":
        # Similar implementation for company context
        current_company = callback_context.state.get("current_company")
        if current_company and isinstance(current_company, dict):
            formatted_company = format_company_context(current_company)
            modified_message = f"Current company details:\n{formatted_company}\n\nUser query: {user_message}"
            callback_context.state["modified_user_message"] = modified_message
    
    # Load all stored context into state
    agent_context = agent_context_manager.get_context(agent_name)
    if agent_context:
        logger.info(f"[CALLBACK] Loading stored context for {agent_name}: {list(agent_context.keys())}")
        for key, value in agent_context.items():
            if callback_context.state.get(key) is None:
                callback_context.state[key] = value
    
    return None

def after_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    After agent callback that stores context from the current agent interaction.
    
    This callback runs after an agent processes a request and stores any
    context that might be needed in future interactions.
    
    Args:
        callback_context: The context for the callback with access to session state
        
    Returns:
        Optional[types.Content]: None to allow normal processing
    """
    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    logger.info(f"[CALLBACK] After agent callback triggered for {agent_name} in invocation {invocation_id}")
    
    # Extract context to store
    context_to_store = {}
    
    # Get user message and agent response for conversation history
    user_message = extract_user_message(callback_context)
    agent_response = ""
    
    # Try to extract agent response from state if available
    agent_response_state = callback_context.state.get("agent_response")
    if agent_response_state and isinstance(agent_response_state, str):
        agent_response = agent_response_state
    
    # If not in state, try other possible locations
    if not agent_response:
        # Check if there's a response object in the context
        if hasattr(callback_context, "response") and callback_context.response:
            if hasattr(callback_context.response, "text"):
                agent_response = callback_context.response.text
        
        # Check if there's a response_text in the state
        response_text = callback_context.state.get("response_text")
        if not agent_response and response_text and isinstance(response_text, str):
            agent_response = response_text
        
        # Check if there's an output_text in the state
        output_text = callback_context.state.get("output_text")
        if not agent_response and output_text and isinstance(output_text, str):
            agent_response = output_text
    
    # Store conversation history if we have both user message and agent response
    if user_message and agent_response:
        agent_context_manager.add_conversation_entry(agent_name, user_message, agent_response)
    
    # Handle different agent types and their specific context
    if agent_name == "lexedge_candidate_search":
        # Check if this is a candidate list response
        if agent_response and (
            "Location:" in agent_response and 
            "Key Skills:" in agent_response and 
            "Email:" in agent_response
        ):
            # This looks like a candidate list response
            logger.info(f"[CALLBACK] Detected candidate list response")
            
            # Store the raw response as candidate_list
            context_to_store["candidate_list"] = agent_response
            
            # Try to extract individual candidate information
            candidate_info = extract_candidate_info(callback_context)
            if candidate_info:
                context_to_store["current_candidate"] = candidate_info
                logger.info(f"[CALLBACK] Extracted candidate info: {list(candidate_info.keys())}")
            
            # Store the candidate list in the global context
            agent_context_manager.update_context(agent_name, {"candidate_list": agent_response})
            logger.info(f"[CALLBACK] Stored candidate list in global context")
        
        # Check if this is a specific candidate details response
        elif agent_response and (
            "Here are the details for" in agent_response or 
            "Full Name:" in agent_response or
            "Years of Experience:" in agent_response
        ):
            # This looks like a specific candidate details response
            logger.info(f"[CALLBACK] Detected specific candidate details response")
            
            # Extract candidate information
            candidate_info = extract_candidate_info(callback_context)
            if not candidate_info and agent_response:
                # Try to extract from the agent response directly
                candidate = {}
                
                # Extract name
                name_match = re.search(r"Here are the details for ([\w\s]+):", agent_response)
                if name_match:
                    candidate["name"] = name_match.group(1).strip()
                
                # Extract common fields using regex patterns
                field_patterns = {
                    "full_name": r"Full Name:\s*([^\n]+)",
                    "location": r"Location:\s*([^\n]+)",
                    "email": r"Email:\s*([^\n]+)",
                    "experience_years": r"Years of Experience:\s*(\d+)",
                    "current_role": r"Current/Recent (Role|Title):\s*([^\n]+)",
                    "summary": r"Professional Summary:\s*([^\n]+)",
                    "education": r"Education:\s*([^\n]+)",
                    "skills": r"Key Skills:\s*([^\n]+)",
                    "languages": r"Languages:\s*([^\n]+)"
                }
                
                for field, pattern in field_patterns.items():
                    match = re.search(pattern, agent_response)
                    if match:
                        if field == "current_role":
                            # Special case for current role which has group(2)
                            value = match.group(2).strip()
                        else:
                            value = match.group(1).strip()
                        
                        # Convert numeric fields
                        if field == "experience_years" and value.isdigit():
                            value = int(value)
                        
                        # Convert list fields
                        if field == "skills" and "," in value:
                            value = [skill.strip() for skill in value.split(",")]
                        
                        candidate[field] = value
                
                if candidate:
                    candidate_info = candidate
            
            if candidate_info:
                # Store in state and context
                context_to_store["current_candidate"] = candidate_info
                callback_context.state["current_candidate"] = candidate_info
                
                # Store in global context
                agent_context_manager.update_context(agent_name, {"current_candidate": candidate_info})
                logger.info(f"[CALLBACK] Stored candidate details in global context: {list(candidate_info.keys())}")
    
    elif agent_name == "lexedge_job_search":
        # Extract and store job information
        job_info = callback_context.state.get("current_job")
        if job_info:
            context_to_store["current_job"] = job_info
            agent_context_manager.update_context(agent_name, {"current_job": job_info})
            logger.info(f"[CALLBACK] Stored job context: {list(job_info.keys()) if isinstance(job_info, dict) else 'non-dict'}")
    
    elif agent_name == "lexedge_company_info":
        # Extract and store company information
        company_info = callback_context.state.get("current_company")
        if company_info:
            context_to_store["current_company"] = company_info
            agent_context_manager.update_context(agent_name, {"current_company": company_info})
            logger.info(f"[CALLBACK] Stored company context: {list(company_info.keys()) if isinstance(company_info, dict) else 'non-dict'}")
    
    # Store common context types that might be present in any agent
    context_keys = [
        "auth_context", "user_context", "search_context", 
        "query_context", "user_preferences", "session_data"
    ]
    
    for key in context_keys:
        value = callback_context.state.get(key)
        if value is not None:
            context_to_store[key] = value
    
    # Store all context
    if context_to_store:
        logger.info(f"[CALLBACK] Storing context for {agent_name}: {list(context_to_store.keys())}")
        agent_context_manager.update_context(agent_name, context_to_store)
    
    return None

def extract_user_message(callback_context: CallbackContext) -> str:
    """
    Extract the user message from the callback context.
    
    Args:
        callback_context: The callback context
        
    Returns:
        str: The extracted user message or empty string
    """
    # In Google ADK, the user message might be in the state
    user_message = callback_context.state.get("user_message")
    if user_message and isinstance(user_message, str):
        return user_message
    
    # Try to get the message from the invocation content
    invocation_content = callback_context.state.get("invocation_content")
    if invocation_content:
        if isinstance(invocation_content, str):
            return invocation_content
        elif isinstance(invocation_content, dict) and "text" in invocation_content:
            return invocation_content["text"]
    
    # Try to get from the request if it exists
    if hasattr(callback_context, "request") and callback_context.request:
        request = callback_context.request
        if hasattr(request, "contents") and request.contents:
            # Find the last user message
            for content in reversed(request.contents):
                if hasattr(content, "role") and content.role == "user" and hasattr(content, "parts") and content.parts:
                    for part in content.parts:
                        if hasattr(part, "text") and part.text:
                            return part.text
    
    # If we can't find the user message, check if there's a raw text in the state
    raw_text = callback_context.state.get("raw_text")
    if raw_text and isinstance(raw_text, str):
        return raw_text
    
    # Last resort: try to get from input_text if it exists
    input_text = callback_context.state.get("input_text")
    if input_text and isinstance(input_text, str):
        return input_text
    
    return ""

def extract_candidate_info(callback_context: CallbackContext) -> Dict[str, Any]:
    """
    Extract candidate information from the session state.
    
    Args:
        callback_context: The callback context
        
    Returns:
        Dict[str, Any]: The extracted candidate information or empty dict
    """
    # In the Google ADK, we don't have direct access to the response in the callback_context
    # Instead, we need to look for candidate information in the session state
    
    # Check if candidate information is already in the state
    current_candidate = callback_context.state.get("current_candidate")
    if current_candidate is not None:
        return current_candidate
    
    # Check if there's a message from the agent that contains candidate details
    # This handles cases where the agent sends candidate details in a structured message
    agent_message = callback_context.state.get("agent_message")
    if agent_message and isinstance(agent_message, str):
        # Try to extract candidate information from the message
        if "Here are the details for" in agent_message:
            candidate = {}
            
            # Extract name
            name_match = re.search(r"Here are the details for ([\w\s]+):", agent_message)
            if name_match:
                candidate["name"] = name_match.group(1).strip()
            
            # Extract common fields using regex patterns
            field_patterns = {
                "full_name": r"Full Name:\s*([^\n]+)",
                "location": r"Location:\s*([^\n]+)",
                "email": r"Email:\s*([^\n]+)",
                "experience_years": r"Years of Experience:\s*(\d+)",
                "current_role": r"Current/Recent Role:\s*([^\n]+)",
                "summary": r"Professional Summary:\s*([^\n]+)",
                "education": r"Education:\s*([^\n]+)",
                "skills": r"Key Skills:\s*([^\n]+)",
                "languages": r"Languages:\s*([^\n]+)"
            }
            
            for field, pattern in field_patterns.items():
                match = re.search(pattern, agent_message)
                if match:
                    value = match.group(1).strip()
                    
                    # Convert numeric fields
                    if field == "experience_years" and value.isdigit():
                        value = int(value)
                    
                    # Convert list fields
                    if field == "skills" and "," in value:
                        value = [skill.strip() for skill in value.split(",")]
                    
                    candidate[field] = value
            
            if candidate:
                # Store the extracted candidate in the state for future use
                callback_context.state["current_candidate"] = candidate
                return candidate
    
    # Try to find candidate information in specific state variables
    # In Google ADK, we can't iterate through state, so we check specific keys
    candidate_keys = [
        "candidate", "candidate_data", "candidate_info", "current_candidate",
        "selected_candidate", "candidate_details", "resume", "resume_data"
    ]
    
    for key in candidate_keys:
        value = callback_context.state.get(key)
        if isinstance(value, dict) and any(k in value for k in ["name", "full_name", "email"]):
            # This looks like candidate data
            candidate_data = {}
            
            # Extract common fields
            for field in ["name", "full_name", "email", "location", "experience_years", "skills", "education", "languages"]:
                if field in value:
                    candidate_data[field] = value[field]
            
            if candidate_data:
                return candidate_data
    
    # If we couldn't find candidate info, return an empty dict
    return {}

def format_candidate_context(candidate: Dict[str, Any]) -> str:
    """
    Format candidate context as a readable string.
    
    Args:
        candidate: The candidate information
        
    Returns:
        str: Formatted candidate information
    """
    lines = []
    
    # Add name
    if "name" in candidate:
        lines.append(f"Here are key details about the candidate named {candidate['name']}:")
    elif "full_name" in candidate:
        lines.append(f"Here are key details about the candidate named {candidate['full_name']}:")
    else:
        lines.append("Here are key details about the candidate:")
    
    # Add email
    if "email" in candidate:
        lines.append(f"- Email: {candidate['email']}")
    
    # Add location
    if "location" in candidate:
        lines.append(f"- Location: {candidate['location']}")
    
    # Add experience
    if "experience_years" in candidate:
        lines.append(f"- Experience: {candidate['experience_years']} years")
    elif "experience" in candidate:
        if isinstance(candidate["experience"], int):
            lines.append(f"- Experience: {candidate['experience']} years")
        elif isinstance(candidate["experience"], str):
            lines.append(f"- Experience: {candidate['experience']}")
    
    # Add skills
    if "skills" in candidate:
        if isinstance(candidate["skills"], list):
            lines.append(f"- Skills: {', '.join(candidate['skills'])}")
        else:
            lines.append(f"- Skills: {candidate['skills']}")
    
    # Add education
    if "education" in candidate:
        if isinstance(candidate["education"], list):
            education_str = "; ".join(candidate["education"])
        else:
            education_str = candidate["education"]
        lines.append(f"- Education: {education_str}")
    
    return "\n".join(lines)


def format_job_context(job: Dict[str, Any]) -> str:
    """
    Format job context as a readable string.
    
    Args:
        job: The job information
        
    Returns:
        str: Formatted job information
    """
    lines = []
    
    # Add title
    if "title" in job:
        lines.append(f"Here are key details about the job position: {job['title']}")
    else:
        lines.append("Here are key details about the job position:")
    
    # Add company
    if "company" in job:
        lines.append(f"- Company: {job['company']}")
    
    # Add location
    if "location" in job:
        lines.append(f"- Location: {job['location']}")
    
    # Add salary
    if "salary" in job:
        lines.append(f"- Salary: {job['salary']}")
    
    # Add requirements
    if "requirements" in job:
        if isinstance(job["requirements"], list):
            lines.append(f"- Requirements: {', '.join(job['requirements'])}")
        else:
            lines.append(f"- Requirements: {job['requirements']}")
    
    # Add description
    if "description" in job:
        lines.append(f"- Description: {job['description']}")
    
    return "\n".join(lines)


def format_company_context(company: Dict[str, Any]) -> str:
    """
    Format company context as a readable string.
    
    Args:
        company: The company information
        
    Returns:
        str: Formatted company information
    """
    lines = []
    
    # Add name
    if "name" in company:
        lines.append(f"Here are key details about the company: {company['name']}")
    else:
        lines.append("Here are key details about the company:")
    
    # Add industry
    if "industry" in company:
        lines.append(f"- Industry: {company['industry']}")
    
    # Add location
    if "location" in company:
        lines.append(f"- Location: {company['location']}")
    
    # Add size
    if "size" in company:
        lines.append(f"- Size: {company['size']}")
    
    # Add description
    if "description" in company:
        lines.append(f"- Description: {company['description']}")
    
    return "\n".join(lines)


def is_followup_question(message: str, context_type: str) -> bool:
    """
    Check if a message is a follow-up question about a specific context type.
    
    Args:
        message: The message to check
        context_type: The type of context (e.g., "candidate", "job", "company")
        
    Returns:
        bool: True if the message is a follow-up question about the specified context
    """
    # Convert to lowercase for case-insensitive matching
    message_lower = message.lower()
    
    # Common patterns for all context types
    common_patterns = [
        r"tell me (more|about)",
        r"can you (provide|give|share) (more|additional) (details|information)",
        r"what (is|are) the",
        r"how (much|many)"
    ]
    
    # Context-specific patterns
    context_patterns = {
        "candidate": [
            r"what (is|are) (his|her|their) (experience|skills|education|background)",
            r"how (much|many) (experience|years|skills) (does|do) (he|she|they) have",
            r"where (is|are|did) (he|she|they) (located|based|work|study)",
            r"\b(he|she|they|his|her|their|them)\b",
            r"\bthis (candidate|person|individual)\b",
            r"\b(experience|skills|education|background|resume)\b",
            r"what are the key skills",
            r"main skills",
            r"key skills",
            r"primary skills"
        ],
        "job": [
            r"what (is|are) the (requirements|qualifications|responsibilities)",
            r"how (much|many) (years|experience) (is|are) required",
            r"where (is|are) the (job|position) (located|based)",
            r"\bthis (job|position|role|opportunity)\b",
            r"\b(salary|compensation|benefits|remote|onsite|hybrid)\b"
        ],
        "company": [
            r"what (is|are) the (company|organization) (size|culture|values)",
            r"where (is|are) the (company|headquarters) (located|based)",
            r"how (many) (employees|people) (does|do) (it|they) have",
            r"\bthis (company|organization|employer)\b",
            r"\b(industry|sector|founded|established)\b"
        ]
    }
    
    # Check common patterns first
    for pattern in common_patterns:
        if re.search(pattern, message_lower):
            return True
            
    # Check context-specific patterns
    if context_type in context_patterns:
        for pattern in context_patterns[context_type]:
            if re.search(pattern, message_lower):
                return True
                
    return False


def is_candidate_followup_question(message: str) -> bool:
    """
    Check if a message is a follow-up question about a candidate.
    
    Args:
        message: The message to check
        
    Returns:
        bool: True if the message is a follow-up question about a candidate
    """
    # Use the generic followup question checker with candidate context type
    return is_followup_question(message, "candidate")
