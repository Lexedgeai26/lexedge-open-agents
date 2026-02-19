#!/usr/bin/env python
"""
Agent runner module for the LexEdge Legal AI application.
Provides functions to run agents and handle streaming responses.
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, AsyncGenerator

from google.adk.runners import Runner
from google.genai import types
from .session import session_service, bind_session_context, reset_session_context
from .root_agent import root_agent
from .sub_agents.lawyer.lawyer_agent import LawyerAgent
from .sub_agents.legal_docs.legal_docs_agent import LegalDocsAgent
from .sub_agents.contract_analysis.contract_analysis_agent import ContractAnalysisAgent
from .sub_agents.legal_research.legal_research_agent import LegalResearchAgent
from .sub_agents.case_management.case_management_agent import CaseManagementAgent
from .sub_agents.compliance.compliance_agent import ComplianceAgent
from .sub_agents.case_intake.case_intake_agent import CaseIntakeAgent
from .sub_agents.legal_correspondence.legal_correspondence_agent import LegalCorrespondenceAgent
from .utils.agent_names import get_agent_friendly_name

logger = logging.getLogger(__name__)

def _get_task_manager():
    """Lazy import of task manager to avoid circular imports."""
    try:
        from .utils.task_manager import get_task_manager
        return get_task_manager()
    except ImportError as e:
        logger.debug(f"Task manager not available: {e}")
        return None


def _filter_technical_details(response: str) -> str:
    """
    Filter out technical details from agent responses that shouldn't be shown to users.
    
    Args:
        response: The raw response from the agent
        
    Returns:
        str: Cleaned response without technical details
    """
    if not response or not isinstance(response, str):
        return response
    
    import re

    # ── Strip leaked system-prompt / disclaimer text ──────────────────────────
    # These strings should never appear in user-facing responses.
    # They come from GLOBAL_SAFETY_PROMPT and STANDARD_DISCLAIMER in system_prompts.py.
    
    # Remove the full GLOBAL_SAFETY_PROMPT block if echoed
    system_prompt_markers = [
        # Exact opening line of GLOBAL_SAFETY_PROMPT
        r"You are a Legal AI Sub-Agent\..*?(?=\n\n|\Z)",
        # Numbered rules block that leaks through
        r"You must:\s*\n(?:\d+\..+\n?)+",
        # Disclaimer line  
        r"Note: This (?:analysis/research|research/analysis) is AI-assisted and for professional review\.[^\n]*",
        # Gatekeeper disclaimer variant
        r"Note: This analysis/research is AI-assisted[^\n]*Manupatra\)[^\n]*",
    ]
    for marker in system_prompt_markers:
        response = re.sub(marker, '', response, flags=re.IGNORECASE | re.DOTALL)
    # ─────────────────────────────────────────────────────────────────────────

    # List of technical patterns to filter out
    technical_patterns = [
        # Agent delegation patterns
        r'\[transfertoagent\([^)]*\)\]',
        r'\[transfer_to_agent\([^)]*\)\]',
        r'transfer_to_agent\([^)]*\)',
        r'transfertoagent\([^)]*\)',
        
        # Function call patterns
        r'\[function_call:[^]]*\]',
        r'\[tool_call:[^]]*\]',
        
        # Agent system messages
        r'\[agent:[^]]*\]',
        r'\[system:[^]]*\]',
        
        # Error traces that might leak through
        r'Traceback \(most recent call last\):.*',
        r'File "[^"]*", line \d+.*',
        
        # Other technical indicators
        r'agent_name=.*',
        r'session_id=.*',
        r'task_id=.*'
    ]
    
    # Apply filters
    filtered_response = response
    for pattern in technical_patterns:
        filtered_response = re.sub(pattern, '', filtered_response, flags=re.IGNORECASE | re.DOTALL)
    
    # Clean up extra whitespace and empty lines
    filtered_response = re.sub(r'\n\s*\n', '\n', filtered_response)
    filtered_response = filtered_response.strip()
    
    # If the response became empty after filtering, provide a fallback
    if not filtered_response or filtered_response.isspace():
        return "I'm working on your request. Please try rephrasing your query or contact support if you need assistance."
    
    return filtered_response


def _is_legal_query(query: Optional[str]) -> bool:
    """
    Determine if a query is legal-related.
    
    Args:
        query: The user's query text
        
    Returns:
        bool: True if the query is legal-related
    """
    if not query:
        return False
    
    text = query.lower()
    
    # Legal keywords that indicate the query is legal-related
    legal_keywords = [
        # Legal documents
        "contract", "agreement", "nda", "non-disclosure", "lease",
        "deed", "will", "trust", "power of attorney", "affidavit",
        "motion", "brief", "complaint", "petition", "subpoena",
        
        # Legal actions
        "lawsuit", "sue", "litigation", "arbitration", "mediation",
        "settlement", "negotiate", "file", "filing", "appeal",
        "deposition", "discovery", "trial", "hearing", "verdict",
        
        # Legal concepts
        "liability", "negligence", "breach", "damages", "indemnity",
        "jurisdiction", "statute", "regulation", "compliance",
        "intellectual property", "trademark", "patent", "copyright",
        
        # Legal professionals
        "lawyer", "attorney", "counsel", "legal", "law firm",
        "paralegal", "judge", "court", "plaintiff", "defendant",
        
        # Legal areas
        "corporate", "employment", "real estate", "immigration",
        "criminal", "family law", "divorce", "custody", "bankruptcy",
        "tax law", "securities", "antitrust", "environmental",
        
        # Legal research
        "case law", "precedent", "statute of limitations", "legal research",
        "case citation", "legal opinion", "legal advice"
    ]
    
    for kw in legal_keywords:
        if kw in text:
            return True
    
    return False


def _route_agent(query: Optional[str]):
    """Route text-only queries to a sub-agent without LLM delegation."""
    if not query:
        return root_agent

    text = query.lower()

    # Contract analysis queries - route to ContractAnalysisAgent
    contract_keywords = [
        "contract", "agreement", "nda", "non-disclosure", "lease agreement",
        "service agreement", "employment contract", "review contract",
        "draft contract", "contract terms", "contract clause", "redline",
        "negotiate terms", "contract risk"
    ]
    for kw in contract_keywords:
        if kw in text:
            return ContractAnalysisAgent

    # Legal document queries - route to LegalDocsAgent
    legal_docs_keywords = [
        "legal document", "analyze document", "document analysis",
        "motion", "brief", "complaint", "petition", "filing",
        "legal filing", "court document", "pleading", "affidavit"
    ]
    for kw in legal_docs_keywords:
        if kw in text:
            return LegalDocsAgent

    # Legal research queries - route to LegalResearchAgent
    research_keywords = [
        "case law", "legal research", "precedent", "statute",
        "regulation", "legal citation", "case citation", "find cases",
        "research law", "legal analysis"
    ]
    for kw in research_keywords:
        if kw in text:
            return LegalResearchAgent

    # Case management queries - route to CaseManagementAgent
    case_mgmt_keywords = [
        "case status", "deadline", "filing deadline", "case timeline",
        "court date", "hearing date", "case task", "case update"
    ]
    for kw in case_mgmt_keywords:
        if kw in text:
            return CaseManagementAgent

    # Compliance queries - route to ComplianceAgent
    compliance_keywords = [
        "compliance", "gdpr", "sox", "hipaa", "regulatory",
        "audit", "policy review", "compliance risk"
    ]
    for kw in compliance_keywords:
        if kw in text:
            return ComplianceAgent

    # Case intake queries - route to CaseIntakeAgent
    intake_keywords = [
        "new case", "new client", "client intake", "engagement letter",
        "conflict check", "case profile", "onboard client"
    ]
    for kw in intake_keywords:
        if kw in text:
            return CaseIntakeAgent

    # Legal correspondence queries - route to LegalCorrespondenceAgent
    correspondence_keywords = [
        "demand letter", "legal notice", "client letter", "settlement proposal",
        "draft letter", "legal correspondence", "formal notice"
    ]
    for kw in correspondence_keywords:
        if kw in text:
            return LegalCorrespondenceAgent

    # General legal queries - route to LawyerAgent
    legal_keywords = [
        "legal", "lawyer", "attorney", "lawsuit", "sue", "litigation",
        "liability", "negligence", "breach", "damages", "legal advice",
        "legal opinion", "case strategy"
    ]
    for kw in legal_keywords:
        if kw in text:
            return LawyerAgent

    return root_agent


async def run_agent(
    user_id: str,
    query: str,
    session_id: Optional[str] = None,
    app_name: str = "lexedge",
    previous_context: Optional[Dict[str, Any]] = None,
    retry_count: int = 0,
    max_retries: int = 2,
    message_data: Optional[Dict[str, Any]] = None,
    force_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the agent with the given query and return the response.
    
    Args:
        user_id: The user ID
        query: The user's query
        session_id: Optional session ID. If not provided, a new session will be created
        app_name: The application name
        previous_context: Optional previous context
        retry_count: Current retry attempt (for internal use)
        max_retries: Maximum number of retry attempts
        message_data: Optional structured data (e.g. images) attached to the message
        force_agent: Optional agent name to force (bypasses routing)
        
    Returns:
        Dict[str, Any]: The agent response containing session_id, response, agent, etc.
    """
    # Generate unique task ID for this agent run
    task_id = f"agent_run_{uuid.uuid4().hex[:8]}"
    if retry_count > 0:
        task_id = f"{task_id}_retry_{retry_count}"
    task_manager = _get_task_manager()
    context_token = None
    
    try:
        # Get or create session
        if session_id:
            try:
                session = await session_service.get_session(
                    app_name=app_name,
                    user_id=user_id,
                    session_id=session_id
                )
            except Exception:
                # Session not found. Keep the provided session_id for routing so
                # tool notifications continue to target the correct open socket.
                logger.warning(
                    f"Session {session_id} not found for user {user_id} - creating backing session with provided id"
                )
                try:
                    # Create a backing session record using the provided session_id
                    session = await session_service.create_session(
                        app_name=app_name,
                        user_id=user_id,
                        session_id=session_id,
                        state={
                            "user_name": user_id,
                            "interaction_history": [],
                            "last_query": None,
                            "last_response": None,
                            "is_authenticated": False
                        }
                    )
                except Exception as create_err:
                    logger.error(f"Failed to create backing session for {session_id}: {create_err}")
                    # Fallback minimal session-like object to allow binding and progress
                    session = type("_TempSession", (), {"id": session_id, "state": {
                        "user_name": user_id,
                        "is_authenticated": False
                    }})()
        else:
            # Create new session
            session = await session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                state={
                    "user_name": user_id,
                    "interaction_history": [],
                    "last_query": None,
                    "last_response": None,
                    "is_authenticated": False
                }
            )
            session_id = session.id
        
        # Bind session context for downstream tool calls
        try:
            context_token = bind_session_context(
                getattr(session, "user_id", user_id),
                session_id,
            )
        except Exception as ctx_error:
            logger.warning(f"Failed to bind session context: {ctx_error}")
        
        final_response = ""
        response_agent = root_agent.name

        # =============================================================
        # AUTO-IMPROVE PROMPT (PROMPT COACH LOGIC)
        # =============================================================
        from .config import LEGAL_SETTINGS
        from .shared_tools import refine_prompt
        import json

        original_query = query
        is_auto_improve_enabled = LEGAL_SETTINGS.get("auto_improve_prompts", True)
        
        # We don't auto-improve if it's a direct command or very short query
        if is_auto_improve_enabled and query and len(query.strip()) > 10:
            try:
                # Call the prompt refinement tool directly (rule-based part of Prompt Coach)
                # This ensures the best-effort structure is used before sending to lead agents
                refinement_json = refine_prompt(query)
                refinement_result = json.loads(refinement_json)
                
                improved_query = refinement_result.get("improved_prompt")
                if improved_query and len(improved_query) > len(query):
                    query = improved_query
                    logger.info(f"✨ [AUTO-IMPROVE] Prompt improved for better agent performance")
                    logger.debug(f"[AUTO-IMPROVE] Original: {original_query}")
                    logger.debug(f"[AUTO-IMPROVE] Refined: {query}")
            except Exception as e:
                logger.warning(f"⚠️ [AUTO-IMPROVE] Failed to refine prompt: {e}")
                # Fallback to original query on error

        # =============================================================
        # BYPASS LLM FOR IMAGES ONLY
        # Images must bypass LLM because LLM cannot pass binary data to tools.
        # Text queries go through LLM for routing, but tool responses go
        # directly to WebSocket (handled in the tools themselves).
        # =============================================================
        direct_response = None
        
        # Check if user is selecting analysis type for a pending image
        from lexedge.context_manager import agent_context_manager
        query_lower = (query or "").lower()
        pending_image = agent_context_manager.get_context("PendingImageUpload")
        
        if pending_image.get("image_b64") and not (message_data and message_data.get("image_b64")):
            # User is responding to image upload options
            # For LexEdge, we can suggest legal document analysis or OCR
            pass
        
        # Check if this is an image upload - MUST bypass LLM
        has_image = False
        image_b64 = None
        if message_data and isinstance(message_data, dict):
            image_b64 = message_data.get("image_b64") or message_data.get("image_data_b64")
            has_image = bool(image_b64)
            if has_image:
                logger.info(f"[BYPASS] Image detected, length: {len(image_b64)}")
        
        # BYPASS PATH: Document processing - extract text locally to avoid binary LLM issues
        # (LLM cannot pass image data to tools, so we must bypass)
        if has_image:
            # For LexEdge, we handle documents by extracting text to avoid LLM binary issues
            query_lower = (query or "").lower()
            
            # Check if this is likely a PDF or document based on mime_type or content
            mime_type = message_data.get("mime_type", "").lower()
            logger.info(f"[BYPASS] Processing image/document with mime_type: {mime_type}")
            
            # Map mime_type to extension for the processor
            mime_to_ext = {
                'application/pdf': 'pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
                'application/msword': 'doc',
                'application/word': 'doc',
                'text/plain': 'txt',
                'text/markdown': 'txt',
                'image/png': 'png',
                'image/jpeg': 'jpg',
                'image/jpg': 'jpg'
            }
            ext = mime_to_ext.get(mime_type)
            if not ext:
                if 'pdf' in mime_type: ext = 'pdf'
                elif 'word' in mime_type or 'document' in mime_type: ext = 'docx'
                elif 'text' in mime_type: ext = 'txt'
            
            # Only attempt extraction for document types
            is_document = ext in ['pdf', 'docx', 'doc', 'txt'] or any(kw in query_lower for kw in ["analyze", "review", "read", "assessment"])
            
            if is_document:
                try:
                    from lexedge.web.file_processor import process_uploaded_file, format_document_context
                    import base64
                    
                    if image_b64.startswith("data:"):
                        header, encoded = image_b64.split(",", 1)
                        image_bytes = base64.b64decode(encoded)
                    else:
                        image_bytes = base64.b64decode(image_b64)
                    
                    # Process as document using the identified extension (fallback to pdf)
                    temp_filename = f"uploaded_document.{ext or 'pdf'}"
                    content_type, extracted_text = await process_uploaded_file(temp_filename, image_bytes)
                    
                    # Only override query and strip binary if we actually got meaningful text
                    if content_type == "text" and extracted_text and len(extracted_text.strip()) > 20:
                        logger.info(f"[BYPASS] Successfully extracted text from {temp_filename}, length: {len(extracted_text)}")
                        query = format_document_context(temp_filename, "text", extracted_text) + "\n\n" + (query or "Please analyze this document.")
                        message_data = None 
                        has_image = False
                        logger.info(f"[BYPASS] Using extracted text for LLM")
                    else:
                        logger.warning(f"[BYPASS] Extraction failed or returned too little text for {temp_filename}")
                        
                        # If it's a regular image (png/jpg), or if the extraction failed but we want to try multimodal
                        # Note: OpenAI Assistants API supports PDF but Chat Completions (gpt-4o) expects images or text.
                        # We cannot send PDF binary to Chat Completions Vision.
                        
                        if ext in ['png', 'jpg', 'jpeg', 'webp']:
                            logger.info("[BYPASS] Keeping as image for multimodal LLM")
                            # Ensure mime_type is set correctly for OpenAI
                            if not message_data.get("mime_type") and ext:
                                message_data["mime_type"] = f"image/{ext if ext != 'jpg' else 'jpeg'}"
                        else:
                            # It is a PDF/Doc that failed text extraction (e.g. Scanned PDF).
                            # We CANNOT send it as binary to OpenAI Chat Completions.
                            # We MUST strip it to avoid the crash.
                            message_data = None 
                            has_image = False
                            
                            error_msg = extracted_text if extracted_text and "[Error" in extracted_text else "Text extraction returned empty content."
                            
                            query = (query or "") + f"\n\n[SYSTEM NOTE: The user attached a document which could not be read (Reason: {error_msg}). It may be a scanned PDF or encrypted. Please ask the user to provide the text content directly.]"
                            
                            logger.info("[BYPASS] Document stripped due to extraction failure to prevent API crash.")
                except Exception as doc_err:
                    logger.error(f"[BYPASS] Document processing failed: {doc_err}")

        if direct_response is not None:
            final_response = direct_response
            logger.info(f"[BYPASS] Direct response received from {response_agent}, length: {len(final_response)}")
        else:
            # Text queries go through LLM for routing
            # Tool responses will be sent directly to WebSocket by the tools themselves
            
            # Check if a specific agent is forced (from bootstrap command selection)
            forced_agent_obj = None
            if force_agent:
                logger.info(f"[FORCE_AGENT] Forcing agent: {force_agent}")
                agent_map = {
                    "LawyerAgent": LawyerAgent,
                    "LegalDocsAgent": LegalDocsAgent,
                    "ContractAnalysisAgent": ContractAnalysisAgent,
                    "LegalResearchAgent": LegalResearchAgent,
                    "CaseManagementAgent": CaseManagementAgent,
                    "ComplianceAgent": ComplianceAgent,
                    "CaseIntakeAgent": CaseIntakeAgent,
                    "LegalCorrespondenceAgent": LegalCorrespondenceAgent,
                }
                forced_agent_obj = agent_map.get(force_agent)
                if forced_agent_obj:
                    response_agent = force_agent
                    logger.info(f"[FORCE_AGENT] Using forced agent: {force_agent}")
            
            # Get or create runner with forced agent or root_agent
            target_agent = forced_agent_obj or root_agent
            runner = await session_service.get_runner(app_name=app_name)
            if not runner or forced_agent_obj:
                runner = await session_service.create_runner(app_name=app_name, agent=target_agent)

            # Create message with query
            content = session_service.create_message(content=query, data=message_data)

            # Create cancellable agent task
            async def agent_processing_task():
                nonlocal response_agent
                final_response = ""
                tool_response_text = ""

                # Run the agent with async streaming
                async for event in runner.run_async(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=content
                ):
                    # Check for cancellation during processing
                    if asyncio.current_task().cancelled():
                        logger.info(f"🛑 Agent task {task_id} was cancelled during LLM processing")
                        raise asyncio.CancelledError("Agent processing was cancelled")

                    if hasattr(event, "get_function_responses"):
                        for function_response in event.get_function_responses() or []:
                            response_payload = function_response.response or {}
                            if isinstance(response_payload, dict):
                                tool_response_text = (
                                    response_payload.get("result")
                                    or response_payload.get("response")
                                    or response_payload.get("status")
                                    or tool_response_text
                                )
                            elif response_payload:
                                tool_response_text = str(response_payload)
                            if tool_response_text:
                                response_agent = getattr(event, "author", response_agent)

                    if hasattr(event, 'content') and event.content:
                        # Get the response text and accumulate it
                        if isinstance(event.content, types.Content) and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    # Accumulate the response text instead of overwriting
                                    final_response += part.text
                                    response_agent = getattr(event, "author", response_agent)
                                elif getattr(part, "function_response", None):
                                    response_payload = part.function_response.response or {}
                                    if isinstance(response_payload, dict):
                                        tool_response_text = (
                                            response_payload.get("result")
                                            or response_payload.get("response")
                                            or response_payload.get("status")
                                            or tool_response_text
                                        )
                                    elif response_payload:
                                        tool_response_text = str(response_payload)
                                    if tool_response_text:
                                        response_agent = getattr(event, "author", response_agent)
                        elif isinstance(event.content, str):
                            # Accumulate string content instead of overwriting
                            final_response += event.content
                            response_agent = getattr(event, "author", response_agent)

                return final_response or tool_response_text

            # Create asyncio task and register with task manager
            processing_task = asyncio.create_task(agent_processing_task())

            if task_manager:
                task_manager.register_task(
                    task_id,
                    session_id,
                    user_id,
                    processing_task,
                    f"Agent processing: {query[:50]}..."
                )

            try:
                # Wait for agent processing (can be cancelled)
                final_response = await processing_task
                logger.info(f"✅ Agent task {task_id} completed successfully")

            except asyncio.CancelledError:
                logger.info(f"🛑 Agent task {task_id} was cancelled")
                # Return user-friendly completion message since API response was already sent
                final_response = ""

            finally:
                # Always unregister the task
                if task_manager:
                    task_manager.unregister_task(task_id)
        
        # Extract response from result (no fallback string)
        response_text = final_response or ""
        
        logger.info(f"[AGENT DEBUG] Response from agent: {response_text[:300]}")
        logger.info(f"[AGENT DEBUG] Response type: {type(response_text)}")
        logger.info(f"[AGENT DEBUG] Response length: {len(response_text)}")
        
        # If task was cancelled, return simple response without suggestions
        if "Thank you for your patience" in response_text:
            logger.info(f"🛑 Agent task was cancelled, returning simple response without suggestions")
            return {
                "session_id": session_id,
                "response": response_text,
                "formatted_response": response_text,
                "agent": get_agent_friendly_name(response_agent),
                "is_authenticated": False,
                "user_name": user_id,
                "role": "",
                "action_suggestions": {"suggestions": []},
                "login_failed": False,
                "login_error": None,
                "login_error_code": 0,
                "login_error_type": "",
                "task_id": task_id
            }
        
    except Exception as e:
        import traceback
        logger.error(f"Error running agent: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Unregister task on error
        if task_manager:
            task_manager.unregister_task(task_id)
        
        # Even if agent fails, save the user query to maintain history
        try:
            from lexedge.session import add_user_query_to_history
            await add_user_query_to_history(
                session_service=session_service,
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
                query=query
            )
        except Exception as save_error:
            logger.error(f"Failed to save user query during error handling: {save_error}")
        
        # Check if this is a retryable error and we haven't exceeded max retries
        if retry_count < max_retries and _is_retryable_error(e):
            logger.warning(f"Retryable error occurred (attempt {retry_count + 1}/{max_retries + 1}): {str(e)}")
            
            # Calculate delay with exponential backoff (1s, 2s, 4s, etc.)
            delay = 2 ** retry_count
            logger.info(f"Waiting {delay}s before retry...")
            await asyncio.sleep(delay)
            
            # Retry the request
            return await run_agent(
                user_id=user_id,
                query=query,
                session_id=session_id,
                app_name=app_name,
                previous_context=previous_context,
                retry_count=retry_count + 1,
                max_retries=max_retries
            )
        
        # Handle different types of errors with user-friendly messages
        error_response = _handle_agent_error(e, query, user_id, session_id, task_id, retry_count, max_retries)
        logger.error(f"Error running agent: {str(e)}")
        return error_response
    
    finally:
        if context_token:
            try:
                reset_session_context(context_token)
            except Exception as ctx_reset_error:
                logger.warning(f"Failed to reset session context: {ctx_reset_error}")
    
    # Update session state (moved outside try/except so it always executes for successful runs)
    try:
        session = await session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        state = session.state
        state["last_query"] = query
        state["last_response"] = response_text
        
        # Add to interaction history
        interaction_history = state.get("interaction_history", [])
        interaction_history.append({
            "role": "user",
            "content": query,
            "timestamp": asyncio.get_event_loop().time()
        })
        interaction_history.append({
            "role": "agent", 
            "agent_name": root_agent.name,
            "content": response_text,
            "timestamp": asyncio.get_event_loop().time()
        })
        state["interaction_history"] = interaction_history
        
        # Update session
        await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            state=state
        )
    except Exception as session_error:
        logger.error(f"Failed to update session state: {session_error}")
        # Use fallback state if session update fails
        state = {
            "is_authenticated": False,
            "user_name": user_id,
            "role": ""
        }
    
    # Return result without suggestions or complex formatting
    return {
        "session_id": session_id,
        "response": response_text,
        "formatted_response": response_text,
        "agent": get_agent_friendly_name(response_agent),
        "is_authenticated": state.get("is_authenticated", False),
        "user_name": state.get("user_name", user_id),
        "role": state.get("role", ""),
        "action_suggestions": {"suggestions": []},
        "login_failed": False,
        "login_error": None,
        "login_error_code": 0,
        "login_error_type": "",
        "task_id": task_id
    }


async def stream_agent_response(
    user_id: str,
    query: str,
    session_id: Optional[str] = None,
    app_name: str = "lexedge"
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stream agent responses.
    
    Args:
        user_id: The user ID
        query: The user's query
        session_id: Optional session ID
        app_name: The application name
        
    Yields:
        Dict[str, Any]: Streaming response chunks
    """
    try:
        # For now, just run the agent and yield the complete response
        # This can be enhanced later for true streaming
        result = await run_agent(
            user_id=user_id,
            query=query,
            session_id=session_id,
            app_name=app_name
        )
        
        yield {
            "type": "response",
            "session_id": result["session_id"],
            "response": result["response"],
            "formatted_response": result.get("formatted_response"),
            "agent": result["agent"],
            "is_authenticated": result.get("is_authenticated", False),
            "stream_complete": True
        }
        
    except Exception as e:
        logger.error(f"Error streaming agent response: {str(e)}")
        yield {
            "type": "error",
            "error": str(e)
        } 

def _handle_agent_error(error: Exception, query: str, user_id: str, session_id: str, task_id: str, *args, **kwargs) -> Dict[str, Any]:
    """Handle agent errors with simple, user-friendly messages."""
    error_str = str(error).lower()
    error_type = type(error).__name__
    
    if any(term in error_str for term in ["agent", "not found", "delegation", "transfer"]):
        msg = "🤖 **Service Issue**\n\nI'm having trouble connecting to the right specialist for your request. Please try again."
        error_type = "delegation"
    elif any(term in error_str for term in ["connection", "network", "unreachable", "httpx"]):
        msg = "🌐 **Connection Issue**\n\nUnable to connect to the service. Please check your internet connection."
        error_type = "connection"
    elif "timeout" in error_str or "timeouterror" in error_type.lower():
        msg = "⏱️ **Request Timeout**\n\nThe request took too long. Please try again."
        error_type = "timeout"
    elif "litellm" in error_str or "openai" in error_str or "badrequest" in error_type.lower():
        return _handle_litellm_error(error, query, user_id, session_id, task_id)
    else:
        msg = "❌ **Unexpected Error**\n\nSomething went wrong while processing your request. Please try again."
        error_type = "generic"

    return {
        "session_id": session_id,
        "response": msg,
        "formatted_response": msg,
        "agent": "error_handler",
        "is_authenticated": False,
        "action_suggestions": {"suggestions": []},
        "error_type": error_type,
        "task_id": task_id
    }


def _handle_litellm_error(error: Exception, query: str, user_id: str, session_id: str, task_id: str) -> Dict[str, Any]:
    """Handle model errors with simple messages."""
    error_str = str(error)
    if "Invalid file data" in error_str or "unsupported MIME type" in error_str:
        msg = "📄 **Document Analysis Issue**\n\nThe AI model had trouble processing the attached file. Please ensure it's a valid PDF or image, or try copying the text directly into the chat."
    elif "model_not_found" in error_str or "model 'gpt-4o' not found" in error_str:
        msg = "🤖 **Configuration Issue**\n\nThe requested AI model is not available. Please check your API key and configuration."
    else:
        msg = "🤖 **AI Processing Error**\n\nThe AI model encountered an issue understanding your request. Let's try a different approach."
    
    return {
        "session_id": session_id,
        "response": msg,
        "formatted_response": msg,
        "agent": "error_handler",
        "is_authenticated": False,
        "action_suggestions": {"suggestions": []},
        "error_type": "litellm",
        "task_id": task_id
    }





def _is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable (transient) or permanent.
    
    Args:
        error: The exception to check
        
    Returns:
        bool: True if the error is retryable, False otherwise
    """
    error_str = str(error).lower()
    
    # Retryable LiteLLM/OpenRouter errors
    retryable_patterns = [
        "timeout",
        "rate limit",
        "server error",
        "service unavailable",
        "bad gateway",
        "gateway timeout", 
        "connection error",
        "network error",
        "temporary failure",
        "try again",
        "parameters are missing"  # Sometimes this is a transient model issue
    ]
    
    # Check if any retryable pattern matches
    for pattern in retryable_patterns:
        if pattern in error_str:
            return True
    
    # Check for specific HTTP status codes that are retryable
    if "502" in error_str or "503" in error_str or "504" in error_str:
        return True
    
    return False 
