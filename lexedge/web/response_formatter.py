"""Response formatting framework for structured HTML output with follow-up suggestions."""

import re
import json
import logging
from typing import List, Dict, Optional, Tuple, Any
import markdown

logger = logging.getLogger(__name__)


def markdown_to_html(text: str) -> str:
    """Convert markdown text to HTML with proper styling classes."""
    if not text:
        return ""
    
    # Configure markdown with extensions
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'nl2br'])
    html = md.convert(text)
    
    # Add Tailwind classes to elements
    html = html.replace('<table>', '<table class="w-full border-collapse text-sm my-4">')
    html = html.replace('<thead>', '<thead class="bg-slate-100">')
    html = html.replace('<th>', '<th class="border border-slate-300 px-3 py-2 text-left font-semibold text-slate-700">')
    html = html.replace('<td>', '<td class="border border-slate-300 px-3 py-2 text-slate-600">')
    html = html.replace('<tr>', '<tr class="hover:bg-slate-50">')
    
    html = html.replace('<h1>', '<h1 class="text-xl font-bold text-legal-navy mt-6 mb-3">')
    html = html.replace('<h2>', '<h2 class="text-lg font-bold text-legal-navy mt-5 mb-2 border-b border-slate-200 pb-1">')
    html = html.replace('<h3>', '<h3 class="text-base font-semibold text-slate-800 mt-4 mb-2">')
    html = html.replace('<h4>', '<h4 class="text-sm font-semibold text-slate-700 mt-3 mb-1">')
    
    html = html.replace('<p>', '<p class="text-slate-700 mb-3 leading-relaxed">')
    html = html.replace('<ul>', '<ul class="list-disc list-inside space-y-1 mb-3 text-slate-700">')
    html = html.replace('<ol>', '<ol class="list-decimal list-inside space-y-1 mb-3 text-slate-700">')
    html = html.replace('<li>', '<li class="ml-2">')
    
    html = html.replace('<strong>', '<strong class="font-semibold text-slate-800">')
    html = html.replace('<em>', '<em class="italic text-slate-600">')
    html = html.replace('<code>', '<code class="bg-slate-100 px-1 py-0.5 rounded text-sm font-mono text-slate-700">')
    html = html.replace('<pre>', '<pre class="bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto my-4 text-sm">')
    
    html = html.replace('<blockquote>', '<blockquote class="border-l-4 border-legal-blue pl-4 italic text-slate-600 my-4">')
    html = html.replace('<hr>', '<hr class="border-slate-200 my-6">')
    
    return html


def generate_followup_suggestions(
    content: str,
    agent_type: str,
    context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """
    Generate context-aware follow-up suggestions based on the response content.
    
    Returns a list of suggestion dicts with 'text' and 'command' keys.
    """
    suggestions = []
    content_lower = content.lower()
    
    # Criminal follow-ups
    if agent_type == "criminal":
        suggestions.extend([
            {
                "text": "Anticipatory bail strategy",
                "command": "Provide an anticipatory bail strategic roadmap with key grounds and analysis.",
                "icon": "shield"
            },
            {
                "text": "Quashing petition analysis",
                "command": "Analyze grounds for a quashing petition (BNSS 528) and identify procedural requirements.",
                "icon": "list"
            },
            {
                "text": "Map BNS/BNSS sections",
                "command": "Map applicable BNS/BNSS sections and analyze key ingredients.",
                "icon": "book-open"
            }
        ])

    # Civil follow-ups
    elif agent_type == "civil":
        suggestions.extend([
            {
                "text": "Analyze plaint structure",
                "command": "Analyze a plaint structure and provide a roadmap for cause of action and reliefs.",
                "icon": "file-text"
            },
            {
                "text": "Injunction strategic test",
                "command": "Apply the triad test for injunction and identify strategic evidence requirements.",
                "icon": "scale"
            },
            {
                "text": "Limitation analysis",
                "command": "Analyze limitation and compute the filing window based on the provided dates.",
                "icon": "calendar"
            }
        ])

    # Property follow-ups
    elif agent_type == "property":
        suggestions.extend([
            {
                "text": "Title/possession analysis",
                "command": "Create a title and possession analysis checklist for this dispute.",
                "icon": "folder"
            },
            {
                "text": "Partition suit strategy",
                "command": "Analyze a partition suit strategy including schedules and prayers.",
                "icon": "file-text"
            }
        ])

    # Family follow-ups
    elif agent_type == "family":
        suggestions.extend([
            {
                "text": "Divorce petition checklist",
                "command": "Provide a divorce petition checklist with required annexures.",
                "icon": "clipboard"
            },
            {
                "text": "Maintenance factors",
                "command": "List key factors and documents needed for maintenance calculation.",
                "icon": "coins"
            }
        ])

    # Corporate follow-ups
    elif agent_type == "corporate":
        suggestions.extend([
            {
                "text": "Contract risk scan",
                "command": "Scan for key contract risks and suggest redline priorities.",
                "icon": "alert-triangle"
            },
            {
                "text": "NCLT filing checklist",
                "command": "Provide a basic NCLT filing checklist and timeline.",
                "icon": "list"
            }
        ])

    # Constitutional follow-ups
    elif agent_type == "constitutional":
        suggestions.extend([
            {
                "text": "Writ petition analysis",
                "command": "Analyze a writ petition structure including prayers and interim relief strategy.",
                "icon": "file-text"
            },
            {
                "text": "Maintainability assessment",
                "command": "Assess maintainability and potential alternative remedy objections.",
                "icon": "shield"
            }
        ])

    # Taxation follow-ups
    elif agent_type == "taxation":
        suggestions.extend([
            {
                "text": "Notice response checklist",
                "command": "Create a checklist for responding to the tax notice with documents.",
                "icon": "check-square"
            },
            {
                "text": "Appeal timeline",
                "command": "Outline the appeal timeline and required forms.",
                "icon": "calendar"
            }
        ])

    # IP follow-ups
    elif agent_type == "ip":
        suggestions.extend([
            {
                "text": "Trademark strategy roadmap",
                "command": "Identify strategic grounds for a trademark objection response.",
                "icon": "file-text"
            },
            {
                "text": "Infringement analysis checklist",
                "command": "Provide a checklist for infringement analysis and evidence.",
                "icon": "search"
            }
        ])

    # Orchestrator follow-ups
    elif agent_type == "intake_router":
        suggestions.extend([
            {
                "text": "Provide missing facts",
                "command": "Here are the key facts and documents I can share:",
                "icon": "message-circle"
            }
        ])
    elif agent_type == "prompt_coach":
        suggestions.extend([
            {
                "text": "Answer missing info",
                "command": "Here are the missing details you asked for:",
                "icon": "message-circle"
            }
        ])
    elif agent_type == "gatekeeper":
        suggestions.extend([
            {
                "text": "Apply fixes",
                "command": "Revise the draft incorporating the listed fixes.",
                "icon": "edit"
            }
        ])

    # Contract-related follow-ups
    elif agent_type == "contract" or "contract" in content_lower:
        if "risk" in content_lower or "liability" in content_lower:
            suggestions.append({
                "text": "Analyze liability clauses in detail",
                "command": "Please provide a detailed analysis of the liability and indemnification clauses, including recommendations for negotiation.",
                "icon": "shield"
            })
        if "payment" in content_lower or "fee" in content_lower:
            suggestions.append({
                "text": "Review payment terms",
                "command": "Analyze the payment terms and suggest a milestone-based payment schedule.",
                "icon": "dollar-sign"
            })
        if "termination" in content_lower:
            suggestions.append({
                "text": "Explain termination provisions",
                "command": "Provide detailed guidance on the termination provisions and notice requirements.",
                "icon": "x-circle"
            })
        if "ip" in content_lower or "intellectual property" in content_lower:
            suggestions.append({
                "text": "Clarify IP ownership",
                "command": "Explain the intellectual property ownership and licensing terms in detail.",
                "icon": "file-text"
            })
        if not suggestions:
            suggestions.append({
                "text": "Identify amendment grounds",
                "command": "Identify specific grounds for amendments for the key issues identified in this contract.",
                "icon": "edit"
            })
            suggestions.append({
                "text": "Summarize key risks",
                "command": "Provide a concise executive summary of the top 5 risks in this contract.",
                "icon": "alert-triangle"
            })
    
    # Research-related follow-ups
    elif agent_type == "research":
        suggestions.append({
            "text": "Find more case law",
            "command": "Search for additional relevant case law and precedents on this topic.",
            "icon": "search"
        })
        suggestions.append({
            "text": "Check recent statutes",
            "command": "Are there any recent statutory changes or pending legislation that could affect this matter?",
            "icon": "book-open"
        })
    
    # Compliance-related follow-ups
    elif agent_type == "compliance":
        suggestions.append({
            "text": "Create compliance checklist",
            "command": "Generate a detailed compliance checklist based on this assessment.",
            "icon": "check-square"
        })
        suggestions.append({
            "text": "Identify remediation steps",
            "command": "What specific steps should be taken to address the compliance gaps identified?",
            "icon": "tool"
        })
    
    # Case management follow-ups
    elif agent_type == "case_management":
        suggestions.append({
            "text": "Generate timeline",
            "command": "Create a detailed case timeline with all key deadlines and milestones.",
            "icon": "calendar"
        })
        suggestions.append({
            "text": "List action items",
            "command": "What are the immediate action items and who should be responsible for each?",
            "icon": "list"
        })
    
    # General follow-ups
    else:
        if "recommend" in content_lower or "suggest" in content_lower:
            suggestions.append({
                "text": "Explain recommendations",
                "command": "Please elaborate on the recommendations and provide specific implementation steps.",
                "icon": "info"
            })
        suggestions.append({
            "text": "Ask a follow-up question",
            "command": "What else should I consider regarding this matter?",
            "icon": "help-circle"
        })

    file_info = (context or {}).get("file_info")
    if not file_info:
        suggestions.append({
            "text": "Upload a document for analysis",
            "command": "",
            "action": "trigger-upload",
            "icon": "paperclip"
        })
    
    # Limit to 4 suggestions
    return suggestions[:4]


def format_response(
    content: str,
    agent_type: str = "general",
    agent_name: str = "LexEdge Counsel",
    context: Optional[Dict[str, Any]] = None
) -> Dict:
    """
    Format a response with HTML content and follow-up suggestions.
    
    Returns a dict with:
    - html_content: Formatted HTML
    - suggestions: List of follow-up suggestions
    - has_tables: Whether the content contains tables
    - has_code: Whether the content contains code blocks
    """
    # Convert markdown to HTML
    html_content = markdown_to_html(content)
    
    # Generate follow-up suggestions
    suggestions = generate_followup_suggestions(content, agent_type, context)
    
    # Detect content features
    has_tables = '<table' in html_content
    has_code = '<pre' in html_content or '<code' in html_content
    has_lists = '<ul' in html_content or '<ol' in html_content
    
    return {
        "html_content": html_content,
        "raw_content": content,
        "suggestions": suggestions,
        "has_tables": has_tables,
        "has_code": has_code,
        "has_lists": has_lists,
        "agent_type": agent_type,
        "agent_name": agent_name
    }
