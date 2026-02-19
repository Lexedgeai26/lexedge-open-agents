"""
Context preservation callbacks for agent interactions.

These callbacks ensure that context is maintained between agent transfers,
allowing for more natural and coherent conversations.
"""

import json
import logging
import re
import sys
from typing import Optional, Dict, Any, List

from google.adk.agents.callback_context import CallbackContext
from google.genai import types

# Configure colored logging
class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log messages"""
    COLORS = {
        'DEBUG': '\033[94m',  # Blue
        'INFO': '\033[92m',    # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[95m', # Purple
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        log_message = super().format(record)
        level_name = record.levelname
        if level_name in self.COLORS:
            return f"{self.COLORS[level_name]}{log_message}{self.COLORS['RESET']}"
        return log_message

# Configure logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

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

def extract_agent_response(callback_context: CallbackContext) -> str:
    """
    Extract the agent response from the callback context.
    
    Args:
        callback_context: The callback context
        
    Returns:
        str: The extracted agent response or empty string
    """
    # Try to extract agent response from state if available
    agent_response = callback_context.state.get("agent_response")
    if agent_response and isinstance(agent_response, str):
        return agent_response
    
    # Check if there's a response object in the context
    if hasattr(callback_context, "response") and callback_context.response:
        if hasattr(callback_context.response, "text"):
            return callback_context.response.text
    
    # Check if there's a response_text in the state
    response_text = callback_context.state.get("response_text")
    if response_text and isinstance(response_text, str):
        return response_text
    
    # Check if there's an output_text in the state
    output_text = callback_context.state.get("output_text")
    if output_text and isinstance(output_text, str):
        return output_text
    
    return ""

def extract_all_candidates_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract information for all candidates from a text containing multiple candidate entries.
    
    Args:
        text: The text to extract from, typically containing multiple candidate entries
        
    Returns:
        List[Dict[str, Any]]: List of extracted candidate information dictionaries
    """
    if not text:
        return []
    
    candidates = []
    
    # Try to split the text into candidate entries
    # Look for numbered entries like "1. Name" or "- Name"
    candidate_entries = re.split(r'\n\s*(?:\d+\.\s+|\-\s+)(?=[A-Z])', text)
    
    # If we couldn't split by numbers, try to split by double newlines
    if len(candidate_entries) <= 1:
        candidate_entries = re.split(r'\n\n+', text)
    
    # Process each candidate entry
    for entry in candidate_entries:
        if not entry.strip():
            continue
            
        # Extract candidate info from this entry
        candidate = extract_candidate_info_from_text(entry)
        if candidate:
            candidates.append(candidate)
    
    # If we still don't have any candidates, try one more approach
    if not candidates and "Location:" in text and "Email:" in text:
        # Try to extract candidate blocks using location and email as anchors
        blocks = re.findall(r'([^\n]+)\s*\n\s*-\s*Location:[^\n]+\n[^\n]*Email:[^\n]+', text)
        for block in blocks:
            name = block.strip()
            if name:
                # Find the corresponding section for this candidate
                section_pattern = re.escape(name) + r'\s*\n\s*-\s*Location:[^\n]+\n[^\n]*Email:[^\n]+'  
                section_match = re.search(section_pattern, text)
                if section_match:
                    section_text = section_match.group(0)
                    candidate = {
                        "name": name
                    }
                    
                    # Extract location
                    location_match = re.search(r'Location:\s*([^\n|]+)', section_text)
                    if location_match:
                        candidate["location"] = location_match.group(1).strip()
                    
                    # Extract email
                    email_match = re.search(r'Email:\s*([^\n]+)', section_text)
                    if email_match:
                        candidate["email"] = email_match.group(1).strip()
                    
                    # Extract experience
                    exp_match = re.search(r'(\d+)\s*years?\s*experience', section_text, re.IGNORECASE)
                    if exp_match:
                        candidate["experience_years"] = int(exp_match.group(1))
                    
                    # Extract skills
                    skills_match = re.search(r'Key Skills:\s*([^\n]+)', section_text)
                    if skills_match:
                        skills_text = skills_match.group(1).strip()
                        candidate["skills"] = [skill.strip() for skill in skills_text.split(",")]
                    
                    candidates.append(candidate)
    
    logger.debug(f"[CONTEXT] 🔍 Extracted {len(candidates)} candidates from text")
    return candidates

def extract_candidate_info_from_text(text: str) -> Dict[str, Any]:
    """
    Extract candidate information from text.
    
    Args:
        text: The text to extract from
        
    Returns:
        Dict[str, Any]: The extracted candidate information or empty dict
    """
    if not text:
        return {}
    
    candidate = {}
    
    # Extract name
    name_match = re.search(r"(?:Here are the details for|Here are key details about) ([\w\s]+):", text)
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
        match = re.search(pattern, text)
        if match:
            if field == "current_role" and len(match.groups()) > 1:
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
    
    return candidate if candidate else {}

def extract_job_info_from_text(text: str) -> Dict[str, Any]:
    """
    Extract job information from text using regex patterns.
    
    Args:
        text: Text containing job information
        
    Returns:
        Dict[str, Any]: Extracted job information or empty dict if not found
    """
    if not text or not isinstance(text, str):
        return {}
    
    job = {}
    
    # Extract job title
    title_match = re.search(r"(Job Title|Title|Position):\s*([^\n]+)", text, re.IGNORECASE)
    if title_match:
        job["title"] = title_match.group(2).strip()
    
    # Extract company name
    company_match = re.search(r"(Company|Organization|Employer):\s*([^\n]+)", text, re.IGNORECASE)
    if company_match:
        job["company"] = company_match.group(2).strip()
    
    # Extract location
    location_match = re.search(r"(Location|Place|Work Location):\s*([^\n]+)", text, re.IGNORECASE)
    if location_match:
        job["location"] = location_match.group(2).strip()
    
    # Extract salary
    salary_match = re.search(r"(Salary|Compensation|Pay):\s*([^\n]+)", text, re.IGNORECASE)
    if salary_match:
        job["salary"] = salary_match.group(2).strip()
    
    # Extract description
    description_match = re.search(r"(Description|About|Summary):\s*([^\n]+)", text, re.IGNORECASE)
    if description_match:
        job["description"] = description_match.group(2).strip()
    
    # Extract requirements
    requirements_match = re.search(r"(Requirements|Qualifications|Skills Required):\s*([^\n]+)", text, re.IGNORECASE)
    if requirements_match:
        requirements_text = requirements_match.group(2).strip()
        # Split by commas if they exist
        if "," in requirements_text:
            job["requirements"] = [req.strip() for req in requirements_text.split(",")]
        else:
            job["requirements"] = requirements_text
    
    # Extract experience
    experience_match = re.search(r"(Experience|Years Required):\s*([^\n]+)", text, re.IGNORECASE)
    if experience_match:
        job["experience"] = experience_match.group(2).strip()
    
    # Extract job type
    job_type_match = re.search(r"(Job Type|Employment Type|Type):\s*([^\n]+)", text, re.IGNORECASE)
    if job_type_match:
        job["job_type"] = job_type_match.group(2).strip()
    
    return job

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

def before_model_callback(callback_context: CallbackContext, llm_request: Any) -> Optional[types.Content]:
    """
    Before model callback that injects context into the prompt.
    
    This callback runs before the model processes a request and injects
    relevant context into the prompt.
    
    Args:
        callback_context: The context for the callback with access to session state
        llm_request: The LLM request
        
    Returns:
        Optional[types.Content]: None to allow normal processing
    """
    agent_name = callback_context.agent_name
    invocation_id = getattr(callback_context, "invocation_id", "unknown")
    logger.info(f"[CONTEXT] 🔍 Before model callback triggered for {agent_name} in invocation {invocation_id}")
    
    # Log the state keys for debugging
    state_keys = []
    for key in ["current_candidate", "current_candidate_id", "candidate_list", 
               "current_job", "current_job_id", "current_company", "current_company_id"]:
        if callback_context.state.get(key) is not None:
            state_keys.append(key)
    
    if state_keys:
        logger.debug(f"[CONTEXT] 🔑 Available state keys: {', '.join(state_keys)}")
    else:
        logger.warning(f"[CONTEXT] ⚠️ No relevant context keys found in state")
    
    # Check if we have any context to inject
    context_parts = []
    
    # Check for candidate context
    if "current_candidate_id" in callback_context.state:
        candidate_id = callback_context.state.get("current_candidate_id")
        context_parts.append(f"You are currently discussing candidate #{candidate_id}.")
        logger.debug(f"[CONTEXT] 👤 Found candidate ID: {candidate_id}")
    
    # Check for current candidate
    if "current_candidate" in callback_context.state:
        candidate = callback_context.state.get("current_candidate")
        if isinstance(candidate, dict) and candidate:
            formatted_candidate = format_candidate_context(candidate)
            context_parts.append(f"Current candidate details:\n{formatted_candidate}")
            logger.debug(f"[CONTEXT] 📄 Found current candidate details: {list(candidate.keys())}")
            logger.debug(f"[CONTEXT] 📝 Formatted current candidate:\n{formatted_candidate}")
    
    # Check for all candidates dictionary
    if "all_candidates" in callback_context.state:
        all_candidates = callback_context.state.get("all_candidates")
        if isinstance(all_candidates, dict) and all_candidates:
            logger.debug(f"[CONTEXT] 📋 Found all_candidates dictionary with {len(all_candidates)} entries")
            
            # Add a summary of available candidates
            candidate_names = list(all_candidates.keys())
            if candidate_names:
                context_parts.append(f"Available candidates: {', '.join(candidate_names)}")
                
                # If we're discussing a specific candidate, add information about that candidate
                current_candidate_id = callback_context.state.get("current_candidate_id")
                if current_candidate_id and current_candidate_id in all_candidates:
                    # We've already added this above if it's in current_candidate
                    pass
                elif user_message and any(name.lower() in user_message.lower() for name in candidate_names):
                    # Try to find which candidate the user is asking about
                    for name in candidate_names:
                        if name.lower() in user_message.lower():
                            candidate = all_candidates[name]
                            formatted_candidate = format_candidate_context(candidate)
                            context_parts.append(f"Details for candidate {name}:\n{formatted_candidate}")
                            logger.debug(f"[CONTEXT] 👤 Found candidate {name} mentioned in user message")
                            break
    
    # Check for job context
    if "current_job_id" in callback_context.state:
        job_id = callback_context.state.get("current_job_id")
        context_parts.append(f"You are currently discussing job #{job_id}.")
        logger.debug(f"[CONTEXT] 💼 Found job ID: {job_id}")
    
    if "current_job" in callback_context.state:
        job = callback_context.state.get("current_job")
        if isinstance(job, dict) and job:
            job_details = json.dumps(job, indent=2)
            context_parts.append(f"Current job details: {job_details}")
            logger.debug(f"[CONTEXT] 📄 Found job details: {list(job.keys())}")
    
    # Check for company context
    if "current_company_id" in callback_context.state:
        company_id = callback_context.state.get("current_company_id")
        context_parts.append(f"You are currently discussing company #{company_id}.")
        logger.debug(f"[CONTEXT] 🏢 Found company ID: {company_id}")
    
    if "current_company" in callback_context.state:
        company = callback_context.state.get("current_company")
        if isinstance(company, dict) and company:
            company_details = json.dumps(company, indent=2)
            context_parts.append(f"Current company details: {company_details}")
            logger.debug(f"[CONTEXT] 📄 Found company details: {list(company.keys())}")
    
    # Check for candidate list
    if "candidate_list" in callback_context.state:
        candidate_list = callback_context.state.get("candidate_list")
        if isinstance(candidate_list, str) and candidate_list:
            # Only include a summary to avoid making the prompt too long
            context_parts.append(f"You have a list of candidates available. When the user asks about a specific candidate by name, use the information from this list.")
            logger.debug(f"[CONTEXT] 📋 Found candidate list (length: {len(candidate_list)})")
            # Log the first 500 characters of the candidate list for debugging
            logger.debug(f"[CONTEXT] 📋 Candidate list preview:\n{candidate_list[:500]}...")
    
    # Get the original prompt/text for logging
    original_prompt = ""
    if hasattr(llm_request, "prompt"):
        original_prompt = llm_request.prompt
    elif hasattr(llm_request, "text"):
        original_prompt = llm_request.text
    elif hasattr(llm_request, "content"):
        original_prompt = llm_request.content
    
    logger.debug(f"[CONTEXT] 📝 Original prompt:\n{original_prompt[:500]}...")
    
    # If we have context to inject, modify the prompt
    if context_parts:
        # Prepend context to the prompt
        context_text = "\n".join(context_parts)
        logger.info(f"[CONTEXT] 💉 Injecting context ({len(context_parts)} parts, {len(context_text)} chars)")
        logger.info(f"[CONTEXT] 📝 Full context being injected:\n{context_text}")
        
        if hasattr(llm_request, "prompt"):
            llm_request.prompt = f"{context_text}\n\n{llm_request.prompt}"
            logger.info(f"[CONTEXT] ✅ Successfully injected context into prompt")
            # Log the first 200 chars of the modified prompt
            logger.debug(f"[CONTEXT] 📝 Modified prompt preview:\n{llm_request.prompt[:200]}...")
        elif hasattr(llm_request, "text"):
            llm_request.text = f"{context_text}\n\n{llm_request.text}"
            logger.info(f"[CONTEXT] ✅ Successfully injected context into text")
            # Log the first 200 chars of the modified text
            logger.debug(f"[CONTEXT] 📝 Modified text preview:\n{llm_request.text[:200]}...")
        elif hasattr(llm_request, "content"):
            llm_request.content = f"{context_text}\n\n{llm_request.content}"
            logger.info(f"[CONTEXT] ✅ Successfully injected context into content")
            # Log the first 200 chars of the modified content
            logger.debug(f"[CONTEXT] 📝 Modified content preview:\n{llm_request.content[:200]}...")
        else:
            logger.error(f"[CONTEXT] ❌ Could not inject context - no suitable attribute found on llm_request")
            # Log the type and attributes of llm_request
            logger.error(f"[CONTEXT] ℹ️ llm_request type: {type(llm_request)}")
            logger.error(f"[CONTEXT] ℹ️ llm_request attributes: {dir(llm_request)}")
    else:
        logger.warning(f"[CONTEXT] ⚠️ No context to inject")
        
    # Log all state variables for debugging
    try:
        all_state = {}
        for key in dir(callback_context.state):
            if not key.startswith('_') and not callable(getattr(callback_context.state, key)):
                try:
                    value = getattr(callback_context.state, key)
                    if isinstance(value, (str, int, float, bool, list, dict)):
                        all_state[key] = value
                except Exception as e:
                    all_state[key] = f"<Error accessing: {str(e)}>"
        
        logger.debug(f"[CONTEXT] 🔍 All state variables: {json.dumps(all_state, default=str)[:1000]}...")
    except Exception as e:
        logger.error(f"[CONTEXT] ❌ Error logging state variables: {str(e)}")
    
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
    invocation_id = getattr(callback_context, "invocation_id", "unknown")
    logger.info(f"[CONTEXT] 🔄 After agent callback triggered for {agent_name} in invocation {invocation_id}")
    
    # Get agent response
    agent_response = extract_agent_response(callback_context)
    if not agent_response:
        logger.warning(f"[CONTEXT] ⚠️ No agent response found")
        return None
    
    # Store agent response in state for debugging
    callback_context.state["last_agent_response"] = agent_response
    logger.debug(f"[CONTEXT] 📝 Agent response stored (length: {len(agent_response)})")
    
    # Get user message
    user_message = extract_user_message(callback_context)
    logger.debug(f"[CONTEXT] 💬 User message: {user_message[:100]}..." if user_message else "[CONTEXT] ⚠️ No user message found")
    
    # Initialize or get the conversation history
    conversation_history = callback_context.state.get("conversation_history", [])
    
    # Add the current exchange to the history
    if user_message and agent_response:
        conversation_history.append({
            "user": user_message,
            "agent": agent_response,
            "timestamp": getattr(callback_context, "timestamp", "unknown")
        })
        # Limit history size to avoid excessive context
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]
        callback_context.state["conversation_history"] = conversation_history
        logger.info(f"[CONTEXT] 📚 Updated conversation history (now {len(conversation_history)} entries)")
    
    # Initialize or get the candidates dictionary
    all_candidates = callback_context.state.get("all_candidates", {})
    
    # Check if this is a candidate search agent
    if agent_name == "CandidateSearchAgent":
        # Check if the response contains candidate information
        if ("Location:" in agent_response and "Email:" in agent_response) or \
           "Here are the details for" in agent_response or \
           "Full Name:" in agent_response:
            
            # This looks like a candidate response
            logger.info(f"[CONTEXT] 🔍 Detected candidate information in response")
            
            # Store the raw response as candidate_list if it contains multiple candidates
            if "1." in agent_response and "2." in agent_response:
                callback_context.state["candidate_list"] = agent_response
                logger.info(f"[CONTEXT] 📋 Stored candidate list (length: {len(agent_response)})")
                
                # Try to extract all candidates from the list
                candidates = extract_all_candidates_from_text(agent_response)
                if candidates:
                    for candidate in candidates:
                        if "name" in candidate or "full_name" in candidate:
                            name = candidate.get("name", candidate.get("full_name", ""))
                            if name:
                                all_candidates[name] = candidate
                                logger.info(f"[CONTEXT] ➕ Added candidate '{name}' to all_candidates dictionary")
            
            # Try to extract specific candidate information
            candidate_info = extract_candidate_info_from_text(agent_response)
            if candidate_info:
                # Store candidate info in state
                callback_context.state["current_candidate"] = candidate_info
                
                # If we have a candidate name, store it as the current focus
                name = ""
                if "name" in candidate_info:
                    name = candidate_info["name"]
                    callback_context.state["current_candidate_id"] = name
                elif "full_name" in candidate_info:
                    name = candidate_info["full_name"]
                    callback_context.state["current_candidate_id"] = name
                
                # Add to all_candidates dictionary
                if name:
                    all_candidates[name] = candidate_info
                    logger.info(f"[CONTEXT] ➕ Added/updated candidate '{name}' in all_candidates dictionary")
                    
                logger.info(f"[CONTEXT] 💾 Stored current candidate info: {list(candidate_info.keys())}")
    
    # Check if this is a job search agent
    elif agent_name == "lexedge_job_search":
        # Check if the response contains job information
        # This looks like a job response
        logger.info(f"[CONTEXT] 🔍 Detected job response")
        
        # Store the raw response
        callback_context.state["job_list"] = agent_response
        logger.info(f"[CONTEXT] 📋 Stored job list")
        
        # Try to extract job information
        job_info = extract_job_info_from_text(agent_response)
        if job_info:
            # Store job info in state
            callback_context.state["current_job"] = job_info
            logger.info(f"[CONTEXT] 💾 Stored current job info: {list(job_info.keys())}")
    
    # Check if this is a company info agent
    elif agent_name == "lexedge_company_info":
        # Similar logic for company information
        if "company" in agent_response.lower() and "industry" in agent_response.lower():
            # This looks like a company response
            logger.info(f"[CONTEXT] 🔍 Detected company response")
            
            # Store the raw response
            callback_context.state["company_list"] = agent_response
            logger.info(f"[CONTEXT] 📋 Stored company list")
    
    # Check if we need to clear or switch context based on intent
    if user_message:
        # Check if user is asking to switch context
        if re.search(r"(?i)show me (other|different|more) (candidates|jobs|companies)", user_message):
            # Clear current focus but keep the all_candidates dictionary
            if "current_candidate_id" in callback_context.state:
                del callback_context.state["current_candidate_id"]
            if "current_candidate" in callback_context.state:
                del callback_context.state["current_candidate"]
            
            logger.info(f"[CONTEXT] 🔄 Cleared current candidate focus due to context switch")
    
    # Log the current state for debugging
    try:
        state_summary = {
            "has_current_candidate": "current_candidate" in callback_context.state,
            "has_current_candidate_id": "current_candidate_id" in callback_context.state,
            "has_candidate_list": "candidate_list" in callback_context.state,
            "all_candidates_count": len(all_candidates),
            "conversation_history_count": len(conversation_history)
        }
        logger.debug(f"[CONTEXT] 📊 State summary after processing: {json.dumps(state_summary)}")
    except Exception as e:
        logger.error(f"[CONTEXT] ❌ Error creating state summary: {str(e)}")
    
    # Store the updated all_candidates dictionary
    callback_context.state["all_candidates"] = all_candidates
    logger.info(f"[CONTEXT] 📊 All candidates dictionary now has {len(all_candidates)} entries")
    
    return None

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Before agent callback that loads relevant context for the current agent.
    
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
    
    # No specific logic needed here as we're using before_model_callback
    # for context injection
    
    return None
