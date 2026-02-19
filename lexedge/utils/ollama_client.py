"""Ollama client utility using the Python ollama SDK."""

import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any, List
import ollama

logger = logging.getLogger(__name__)

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")


async def chat_completion(
    messages: List[Dict[str, str]],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    format_schema: Optional[Dict] = None
) -> str:
    """
    Send a chat completion request to Ollama.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        system_prompt: Optional system prompt to prepend
        model: Model to use (defaults to OLLAMA_MODEL env var)
        temperature: Temperature for generation
        format_schema: Optional JSON schema for structured output
    
    Returns:
        The model's response text
    """
    model = model or OLLAMA_MODEL
    
    # Build messages list
    all_messages = []
    if system_prompt:
        all_messages.append({"role": "system", "content": system_prompt})
    all_messages.extend(messages)
    
    # Build request payload
    payload = {
        "model": model,
        "messages": all_messages,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }
    
    if format_schema:
        payload["format"] = format_schema
    
    try:
        response = await asyncio.to_thread(
            ollama.chat,
            model=model,
            messages=all_messages,
            options={"temperature": temperature},
        )
        content = response.get("message", {}).get("content", "")
        if not content:
            logger.warning("Ollama returned empty content")
        return content
    except Exception as e:
        logger.error(f"Ollama chat error [{type(e).__name__}]: {repr(e)}")
        raise


async def generate_completion(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7
) -> str:
    """
    Send a generate request to Ollama (simpler than chat).
    
    Args:
        prompt: The prompt text
        system_prompt: Optional system prompt
        model: Model to use
        temperature: Temperature for generation
    
    Returns:
        The model's response text
    """
    model = model or OLLAMA_MODEL
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }
    
    if system_prompt:
        payload["system"] = system_prompt
    
    try:
        response = await asyncio.to_thread(
            ollama.generate,
            model=model,
            prompt=prompt,
            system=system_prompt or "",
            options={"temperature": temperature},
        )
        return response.get("response", "")
    except Exception as e:
        logger.error(f"Ollama generate error [{type(e).__name__}]: {repr(e)}")
        raise


async def analyze_legal_text(
    text: str,
    task: str,
    context: Optional[str] = None
) -> str:
    """
    Analyze legal text using Ollama.
    
    Args:
        text: The legal text to analyze
        task: What to do with the text (e.g., "review contract", "identify risks")
        context: Optional additional context
    
    Returns:
        Analysis result
    """
    system_prompt = """You are an expert legal analyst. Provide clear, professional analysis.
Be direct and helpful. Do not show your reasoning process."""

    user_content = f"Task: {task}\n\n"
    if context:
        user_content += f"Context: {context}\n\n"
    user_content += f"Document:\n{text}"
    
    messages = [{"role": "user", "content": user_content}]
    
    return await chat_completion(messages, system_prompt=system_prompt, temperature=0.3)


async def get_legal_response(
    query: str,
    agent_type: str = "general",
    case_context: Optional[str] = None
) -> str:
    """
    Get a legal response for a user query.
    
    Args:
        query: User's question or request
        agent_type: Type of legal agent (contract, research, compliance, etc.)
        case_context: Optional case context
    
    Returns:
        Legal response
    """
    system_prompts = {
        "criminal": (
            "You are a criminal law drafting and research assistant for India. "
            "Provide structured, court-ready guidance, not legal advice. "
            "Use BNS/BNSS/BSA where applicable and flag citations for verification."
        ),
        "civil": (
            "You are a civil litigation drafting assistant for India. "
            "Handle plaints, WS, injunctions, appeals, and limitation analysis. "
            "Use CPC references and flag verification needs."
        ),
        "property": (
            "You are a property disputes assistant for India. "
            "Handle title, partition, specific performance, eviction, and mutation issues."
        ),
        "family": (
            "You are a family and divorce drafting assistant for India. "
            "Handle divorce, maintenance, custody, and DV proceedings with sensitivity."
        ),
        "corporate": (
            "You are a corporate/commercial drafting assistant for India. "
            "Handle contracts, governance, employment, and NCLT-related matters."
        ),
        "constitutional": (
            "You are a constitutional and writs drafting assistant for India. "
            "Handle Art. 226/32 petitions, PIL, interim relief, and contempt."
        ),
        "taxation": (
            "You are a taxation assistant for India. "
            "Handle IT/GST notices, appeals, stays, and rectification."
        ),
        "ip": (
            "You are an intellectual property assistant for India. "
            "Handle trademarks, patents, infringement, and licensing."
        ),
        "intake_router": (
            "You are an intake router for a legal AI system in India. "
            "Classify the practice area, identify forum/urgency, and list missing details."
        ),
        "prompt_coach": (
            "You are a legal prompt coach. "
            "Rewrite vague legal requests into structured, court-usable prompts."
        ),
        "gatekeeper": (
            "You are a quality gatekeeper for legal drafts in India. "
            "Check completeness, risks, and add verification disclaimers."
        ),
        "contract": "You are an expert contract attorney. Help clients analyze contracts and agreements. Be professional and helpful.",
        "research": "You are a legal research specialist. Help find relevant case law, statutes, and legal precedents.",
        "compliance": "You are a compliance specialist. Help with regulatory compliance and risk assessment.",
        "case_management": "You are a case management specialist. Help track deadlines and manage case workflow.",
        "intake": "You are a client intake specialist. Help gather case information and create client profiles.",
        "correspondence": "You are a legal correspondence specialist. Help draft professional legal letters and notices.",
        "general": "You are a senior legal counsel. Provide helpful legal guidance and analysis."
    }
    
    system_prompt = system_prompts.get(agent_type, system_prompts["general"])
    
    user_content = query
    if case_context:
        user_content = f"Case Context: {case_context}\n\nQuery: {query}"
    
    messages = [{"role": "user", "content": user_content}]
    
    return await chat_completion(messages, system_prompt=system_prompt, temperature=0.5)
