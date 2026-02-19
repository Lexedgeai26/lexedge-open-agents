"""FastAPI routes for HTMX-based LexEdge Legal AI frontend."""

import json
import logging
from typing import Optional
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pathlib

from lexedge.config import LEGAL_SETTINGS, get_legal_context_string
from lexedge.agent_runner import run_agent
from lexedge.session import session_service
from lexedge.web.file_processor import (
    process_uploaded_file, 
    format_document_context, 
    is_supported_file,
    is_image_file
)
from lexedge.utils.ollama_client import get_legal_response
from lexedge.web.response_formatter import format_response, markdown_to_html

logger = logging.getLogger(__name__)

# Setup templates
TEMPLATE_DIR = pathlib.Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

router = APIRouter(prefix="/app", tags=["web"])

# Legal agent bootstrap commands
LEGAL_COMMANDS = {
    "intake_router": {
        "id": "intake_router",
        "icon": "🧭",
        "title": "Intake Router",
        "description": "Classify matter, set forum/urgency, route to practice lead",
        "command": "Please classify this matter and route it to the right practice lead.",
        "agent": "IntakeRouterAgent"
    },
    "prompt_coach": {
        "id": "prompt_coach",
        "icon": "🧪",
        "title": "Prompt Coach",
        "description": "Refine vague requests into court-usable prompts",
        "command": "Refine my request into a complete legal prompt with missing info list.",
        "agent": "PromptCoachAgent"
    },
    "gatekeeper": {
        "id": "gatekeeper",
        "icon": "🛡️",
        "title": "Quality Gatekeeper",
        "description": "Validate analysis, flag citation/section risks, add disclaimer",
        "command": "Review this analysis for risks and missing elements.",
        "agent": "QualityGatekeeperAgent"
    },
    "criminal": {
        "id": "criminal",
        "icon": "🚔",
        "title": "Criminal Lead",
        "description": "FIR, bail, quashing, discharge, NI 138, trial strategy",
        "command": "I need help with a criminal matter: FIR/bail/quashing.",
        "agent": "CriminalLawLeadAgent"
    },
    "civil": {
        "id": "civil",
        "icon": "⚖️",
        "title": "Civil Litigation Lead",
        "description": "Analysis of Plaint/WS, injunctions, appeals, execution, limitation",
        "command": "I need a strategic analysis for a civil suit or injunction.",
        "agent": "CivilLitigationLeadAgent"
    },
    "property": {
        "id": "property",
        "icon": "🏠",
        "title": "Property Lead",
        "description": "Title, partition, specific performance, eviction, mutation",
        "command": "I need help with a property dispute or title issue.",
        "agent": "PropertyDisputesLeadAgent"
    },
    "family": {
        "id": "family",
        "icon": "👪",
        "title": "Family & Divorce Lead",
        "description": "Divorce, maintenance, custody, DV proceedings",
        "command": "I need help with a family or divorce matter.",
        "agent": "FamilyDivorceLeadAgent"
    },
    "corporate": {
        "id": "corporate",
        "icon": "🏢",
        "title": "Corporate Lead",
        "description": "Contracts, governance, NCLT, employment, due diligence",
        "command": "I need help with a corporate contract or governance issue.",
        "agent": "CorporateCommercialLeadAgent"
    },
    "constitutional": {
        "id": "constitutional",
        "icon": "📜",
        "title": "Constitutional Lead",
        "description": "Writs (226/32), PIL, interim relief, contempt",
        "command": "I need help with a writ petition or constitutional issue.",
        "agent": "ConstitutionalWritsLeadAgent"
    },
    "taxation": {
        "id": "taxation",
        "icon": "🧾",
        "title": "Tax Lead",
        "description": "IT/GST notices, appeals, stays, rectification",
        "command": "I need help with an income tax or GST matter.",
        "agent": "TaxationLeadAgent"
    },
    "ip": {
        "id": "ip",
        "icon": "🧠",
        "title": "IP Lead",
        "description": "Trademarks, patents, infringement, licensing",
        "command": "I need help with a trademark or IP matter.",
        "agent": "IntellectualPropertyLeadAgent"
    },
    "case_mgmt": {
        "id": "case_mgmt",
        "icon": "📋",
        "title": "Case Management",
        "description": "Deadlines, timelines, task tracking, filings",
        "command": "Help me track case deadlines and tasks.",
        "agent": "CaseManagementAgent"
    },
    "compliance": {
        "id": "compliance",
        "icon": "✅",
        "title": "Compliance",
        "description": "Regulatory compliance audits and risk assessment",
        "command": "I need a compliance audit or regulatory assessment.",
        "agent": "ComplianceAgent"
    },
    "correspondence": {
        "id": "correspondence",
        "icon": "✉️",
        "title": "Correspondence",
        "description": "Strategic analysis for legal notices, letters, and replies",
        "command": "Analyze requirements for a legal notice or technical reply.",
        "agent": "LegalCorrespondenceAgent"
    }
}


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main landing page."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "legal_settings": LEGAL_SETTINGS,
        "commands": LEGAL_COMMANDS
    })


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, session_id: Optional[str] = None):
    """Render the chat interface."""
    if not session_id:
        session_id = f"session_{id(request)}"
    
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "session_id": session_id,
        "legal_settings": LEGAL_SETTINGS,
        "commands": LEGAL_COMMANDS
    })


def clean_gpt_oss_response(text: str) -> str:
    """Clean up gpt-oss chain-of-thought reasoning from response text."""
    if not text:
        return text
    
    # Common patterns where gpt-oss shows its reasoning
    reasoning_markers = [
        "User:", "User says:", "They haven't", "According to instruction",
        "Let's do that.", "So respond", "So we must", "So I should",
        "But also if", "Let's see", "We are ", "No contract provided",
        "can respond directly", "must ask them", "thinking", "reasoning"
    ]
    
    # Check if response contains reasoning
    has_reasoning = any(marker in text for marker in reasoning_markers)
    
    if has_reasoning:
        # Try to extract just the actual response
        # Look for common response starters after reasoning
        response_starters = [
            "Sure!", "Sure,", "Of course!", "I'd be happy", "I would be happy",
            "Please", "Could you", "To get started", "To help", "To begin",
            "Thank you", "Certainly", "Absolutely", "Great", "Hello",
            "Welcome", "I can help", "Let me help", "I'll help",
            "To analyze", "For a", "In order to"
        ]
        
        for starter in response_starters:
            if starter in text:
                idx = text.find(starter)
                clean_text = text[idx:].strip()
                # Remove any trailing reasoning that might appear
                for marker in ["We are ", "So we ", "According to"]:
                    if marker in clean_text:
                        clean_text = clean_text.split(marker)[0].strip()
                return clean_text
        
        # If no clear starter, try to get text after common reasoning endings
        reasoning_endings = [
            "Let's do that.", "So:", "respond directly.", 
            "must ask them to provide", "contract details.\""
        ]
        for ending in reasoning_endings:
            if ending in text:
                parts = text.split(ending)
                if len(parts) > 1:
                    remaining = parts[-1].strip()
                    if remaining:
                        return remaining
    
    return text.strip()


@router.post("/send-message", response_class=HTMLResponse)
async def send_message(
    request: Request,
    message: str = Form(""),
    session_id: str = Form(...),
    force_agent: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """Process a message with optional file upload and return the response as HTML."""
    try:
        query = message
        file_info = None
        
        # Process uploaded file if present
        if file and file.filename:
            if not is_supported_file(file.filename):
                return templates.TemplateResponse("partials/error_response.html", {
                    "request": request,
                    "error": f"Unsupported file type. Supported: PDF, DOCX, TXT, PNG, JPG, GIF"
                })
            
            file_content = await file.read()
            content_type, extracted_content = await process_uploaded_file(file.filename, file_content)
            
            if content_type == "error":
                return templates.TemplateResponse("partials/error_response.html", {
                    "request": request,
                    "error": extracted_content
                })
            
            # Format document context and append to query
            doc_context = format_document_context(file.filename, content_type, extracted_content)
            
            if message.strip():
                query = f"{message}\n\n{doc_context}"
            else:
                query = f"Please analyze this document:\n\n{doc_context}"
            
            file_info = {
                "filename": file.filename,
                "type": content_type,
                "is_image": is_image_file(file.filename)
            }
            
            # Force to LegalDocsAgent for document analysis
            if not force_agent:
                force_agent = "LegalDocsAgent"
        
        if not query.strip():
            return templates.TemplateResponse("partials/error_response.html", {
                "request": request,
                "error": "Please enter a message or upload a file."
            })
        
        # Map force_agent to agent type for Ollama
        agent_type_map = {
            "IntakeRouterAgent": "intake_router",
            "PromptCoachAgent": "prompt_coach",
            "QualityGatekeeperAgent": "gatekeeper",
            "CriminalLawLeadAgent": "criminal",
            "CivilLitigationLeadAgent": "civil",
            "PropertyDisputesLeadAgent": "property",
            "FamilyDivorceLeadAgent": "family",
            "CorporateCommercialLeadAgent": "corporate",
            "ConstitutionalWritsLeadAgent": "constitutional",
            "TaxationLeadAgent": "taxation",
            "IntellectualPropertyLeadAgent": "ip",
            "ContractAnalysisAgent": "contract",
            "LegalResearchAgent": "research",
            "ComplianceAgent": "compliance",
            "CaseManagementAgent": "case_management",
            "CaseIntakeAgent": "intake",
            "LegalCorrespondenceAgent": "correspondence",
            "LawyerAgent": "general",
            "LegalDocsAgent": "contract"
        }
        agent_type = agent_type_map.get(force_agent, "general")
        agent_name = "LexEdge Counsel"
        if force_agent:
            for command in LEGAL_COMMANDS.values():
                if command.get("agent") == force_agent:
                    agent_name = command.get("title", agent_name)
                    break
        else:
            agent_name = LEGAL_COMMANDS.get(agent_type, {}).get("title", agent_name)
        
        # Use Ollama directly for better gpt-oss compatibility
        try:
            response_text = await get_legal_response(query, agent_type=agent_type)
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            response_text = f"I apologize, but I'm having trouble processing your request. Please try again."
        
        # Clean up and format the response
        cleaned_text = clean_gpt_oss_response(response_text)
        
        # Format response with HTML and follow-up suggestions
        formatted = format_response(
            content=cleaned_text,
            agent_type=agent_type,
            agent_name=agent_name,
            context={"file_info": file_info}
        )
        
        return templates.TemplateResponse("partials/message_response.html", {
            "request": request,
            "user_message": message if message else (f"[Uploaded: {file.filename}]" if file and file.filename else ""),
            "response": formatted,
            "response_type": "formatted",
            "agent_name": agent_name
        })
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return templates.TemplateResponse("partials/error_response.html", {
            "request": request,
            "error": str(e)
        })


@router.get("/command/{command_id}", response_class=HTMLResponse)
async def get_command_guidance(request: Request, command_id: str):
    """Get guidance for a specific command."""
    command = LEGAL_COMMANDS.get(command_id)
    if not command:
        return HTMLResponse("<p class='text-red-500'>Command not found</p>")
    
    return templates.TemplateResponse("partials/command_guidance.html", {
        "request": request,
        "command": command
    })


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Render the settings page."""
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "legal_settings": LEGAL_SETTINGS
    })
