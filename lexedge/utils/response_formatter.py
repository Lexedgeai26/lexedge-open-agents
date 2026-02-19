#!/usr/bin/env python
"""
Response Formatter Utility for LexEdge
Formats LexEdge AI responses for proper display in the client.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def format_educational_template(data: dict) -> str:
    """Format general medical information into a clean educational template."""
    topic = data.get("topic", "Medical Information")
    summary = data.get("explanation", data.get("summary", ""))
    key_points = data.get("key_points", [])
    related = data.get("related_topics", [])
    
    html = f"""
    <div class="educational-card" style="border-left: 3px solid #3b82f6; padding: 8px 10px; margin: 2px 0; border-radius: 8px; background: #ffffff;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            <span style="background: #3b82f6; color: white; padding: 2px 8px; border-radius: 999px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;">
                ℹ️ {topic}
            </span>
        </div>
        
        <div style="margin-bottom: 6px;">
            <p style="color: #334155; font-size: 0.85rem; line-height: 1.4; margin: 0;">{summary}</p>
        </div>
    """
    
    if key_points:
        html += f"""
        <div style="margin-bottom: 6px;">
            <strong style="color: #1e293b; display: block; margin-bottom: 2px; font-size: 0.78rem;">📌 Key Points</strong>
            <ul style="margin: 0; padding-left: 12px; font-size: 0.8rem; line-height: 1.35;">
                {' '.join([f'<li>{point}</li>' for point in key_points])}
            </ul>
        </div>
        """
        
    if related:
        html += f"""
        <div style="margin-top: 6px; border-top: 1px dashed #cbd5e1; padding-top: 4px;">
            <strong style="color: #64748b; font-size: 0.75rem;">Related: </strong>
            <span style="color: #475569; font-size: 0.75rem;">{', '.join(related)}</span>
        </div>
        """

    html += "</div>"
    html += '<p style="font-size: 0.68rem; color: #94a3b8; margin: 4px 0 0; font-style: italic;">Disclaimer: For informational purposes only. Consult a physician.</p>'
    return html

def format_diagnosis_template(data: dict) -> str:
    """Format a specific diagnostic result with confidence and treatment plan."""
    conditions = data.get("conditions", []) # List of {name: str, probability: str}
    reasoning = data.get("reasoning", "")
    plan = data.get("treatment_plan", [])
    
    html = f"""
    <div class="diagnosis-card" style="border-left: 3px solid #8b5cf6; padding: 8px 10px; margin: 2px 0; border-radius: 8px; background: #ffffff;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span style="background: #8b5cf6; color: white; padding: 2px 8px; border-radius: 999px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;">
                🔬 Potential Diagnosis
            </span>
        </div>
    """
    
    if conditions:
        html += '<div style="margin-bottom: 8px; display: flex; flex-direction: column; gap: 4px;">'
        for cond in conditions:
            name = cond.get("name", cond) if isinstance(cond, dict) else cond
            prob = cond.get("probability", "") if isinstance(cond, dict) else ""
            prob_badge = f'<span style="font-size: 0.7rem; color: #64748b; background: #f1f5f9; padding: 1px 6px; border-radius: 4px;">{prob}</span>' if prob else ""
            
            html += f"""
            <div style="display: flex; justify-content: space-between; align-items: center; background: #f5f3ff; padding: 6px 8px; border-radius: 6px;">
                <span style="color: #4c1d95; font-weight: 600; font-size: 0.85rem;">{name}</span>
                {prob_badge}
            </div>
            """
        html += '</div>'

    if reasoning:
        html += f"""
        <div style="margin-bottom: 8px;">
            <p style="color: #4b5563; font-size: 0.8rem; line-height: 1.4; margin: 0;">{reasoning}</p>
        </div>
        """

    if plan:
        html += f"""
        <div style="margin-top: 6px; border-top: 1px dashed #e2e8f0; padding-top: 6px;">
            <strong style="color: #4b5563; display: block; margin-bottom: 4px; font-size: 0.75rem;">📋 Suggested Approach</strong>
            <ul style="margin: 0; padding-left: 12px; font-size: 0.8rem; line-height: 1.35; color: #334155;">
                {' '.join([f'<li>{item}</li>' for item in plan])}
            </ul>
        </div>
        """

    html += "</div>"
    html += '<p style="font-size: 0.68rem; color: #94a3b8; margin: 4px 0 0; font-style: italic;">Disclaimer: Consult a specialist for confirmation.</p>'
    return html

def format_media_template(data: dict) -> str:
    """Format radiology or image analysis findings."""
    modality = data.get("modality", "Imaging").upper()
    findings = data.get("findings", [])
    impression = data.get("impression", "")
    severity = str(data.get("severity", "routine")).lower()
    
    severity_colors = {"emergency": "#ef4444", "urgent": "#f97316", "routine": "#22c55e", "normal": "#22c55e"}
    color = severity_colors.get(severity, "#64748b")
    
    html = f"""
    <div class="media-card" style="border-left: 3px solid {color}; padding: 8px 10px; margin: 2px 0; border-radius: 8px; background: #ffffff;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 999px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">
                📷 {modality} Analysis
            </span>
        </div>
    """
    
    if impression:
        html += f"""
        <div style="margin-bottom: 8px; background: #f8fafc; padding: 6px 8px; border-radius: 6px; border: 1px solid #e2e8f0;">
            <strong style="display: block; color: #0f172a; font-size: 0.8rem; margin-bottom: 2px;">Impression</strong>
            <p style="margin: 0; color: #334155; font-size: 0.8rem; line-height: 1.4;">{impression}</p>
        </div>
        """
        
    if findings:
        html += f"""
        <div style="margin-bottom: 4px;">
            <strong style="color: #475569; display: block; margin-bottom: 2px; font-size: 0.75rem;">Key Findings</strong>
            <ul style="margin: 0; padding-left: 12px; font-size: 0.8rem; line-height: 1.35; color: #334155;">
                {' '.join([f'<li>{f}</li>' for f in findings])}
            </ul>
        </div>
        """
        
    html += "</div>"
    html += '<p style="font-size: 0.68rem; color: #94a3b8; margin: 4px 0 0; font-style: italic;">Disclaimer: AI visualization analysis. Not a radiologist report.</p>'
    return html

def format_general_template(data: dict) -> str:
    """Format a generic response for unknown intents."""
    content = data.get("content", data.get("text", ""))
    
    html = f"""
    <div class="general-card" style="padding: 4px 0;">
        <p style="color: #1e293b; font-size: 0.9rem; line-height: 1.5; margin: 0;">{content}</p>
    </div>
    """
    return html

def format_premium_template(data: dict) -> str:
    """
    Dispatch structured JSON data to the appropriate specialized Premium Template.
    Supports: Assessment (Default), Diagnosis, Educational, Media, General.
    """
    if not data:
        return ""
        
    # DISPATCHER
    rtype = data.get("response_type", "assessment").lower()
    
    if rtype == "educational":
        return format_educational_template(data)
    elif rtype == "diagnosis":
        return format_diagnosis_template(data)
    elif rtype == "media":
        return format_media_template(data)
    elif rtype == "general":
        return format_general_template(data)
    
    # Default fallback to Assessment Template (existing logic)
    # Extract data with defaults
    patterns = data.get("suspected_patterns", [])
    risk = str(data.get("risk_signal", data.get("risk_level", "low"))).lower()
    findings = data.get("clinical_findings", data.get("refined_symptoms", []))
    missing = data.get("missing_details", data.get("missing_information", []))
    red_flags = data.get("red_flags", [])
    decision = data.get("decision", data.get("next_action", "PROCEED"))
    follow_up = data.get("recommended_follow_up", data.get("follow_up_questions", []))
    summary = data.get("clinical_summary", data.get("consultant_summary", ""))

    # Styling for risk level
    risk_colors = {
        "emergency": "#ef4444", # Red
        "high": "#f97316",      # Orange
        "moderate": "#eab308",  # Yellow
        "low": "#22c55e"        # Green
    }
    risk_color = risk_colors.get(risk, "#64748b")
    
    html = f"""
    <div class="premium-assessment" style="border-left: 3px solid {risk_color}; padding: 8px 10px; margin: 2px 0; border-radius: 8px; background: #ffffff;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            <span style="background: {risk_color}; color: white; padding: 2px 8px; border-radius: 999px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;">
                {risk} Risk Signal
            </span>
        </div>
    """

    if patterns:
        html += f"""
        <div style="margin-bottom: 4px;">
            <strong style="color: #1e293b; display: block; margin-bottom: 2px; font-size: 0.78rem;">🧬 Suspected Patterns</strong>
            <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                {' '.join([f'<span style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 1px 6px; border-radius: 4px; font-size: 0.78rem;">{p}</span>' for p in (patterns if isinstance(patterns, list) else [patterns])])}
            </div>
        </div>
        """

    if red_flags:
        html += f"""
        <div style="background: #fef2f2; border: 1px solid #fee2e2; border-radius: 6px; padding: 6px 8px; margin-bottom: 4px;">
            <strong style="color: #991b1b; display: block; margin-bottom: 2px; font-size: 0.78rem;">🚨 Red Flags Detected</strong>
            <ul style="margin: 0; padding-left: 12px; color: #b91c1c; font-size: 0.8rem; line-height: 1.35;">
                {' '.join([f'<li>{flag}</li>' for flag in (red_flags if isinstance(red_flags, list) else [red_flags])])}
            </ul>
        </div>
        """

    if findings:
        html += f"""
        <div style="margin-bottom: 4px;">
            <strong style="color: #1e293b; display: block; margin-bottom: 2px; font-size: 0.78rem;">📊 Clinical Findings</strong>
            <ul style="margin: 0; padding-left: 12px; font-size: 0.8rem; line-height: 1.35;">
                {' '.join([f'<li>{item}</li>' for item in (findings if isinstance(findings, list) else [findings])])}
            </ul>
        </div>
        """

    if missing:
        html += f"""
        <div style="background: #f0f9ff; border: 1px solid #e0f2fe; border-radius: 6px; padding: 6px 8px; margin-bottom: 4px;">
            <strong style="color: #0369a1; display: block; margin-bottom: 2px; font-size: 0.78rem;">❓ Missing Information</strong>
            <ul style="margin: 0; padding-left: 12px; color: #075985; font-size: 0.8rem; line-height: 1.35;">
                {' '.join([f'<li>{m}</li>' for m in (missing if isinstance(missing, list) else [missing])])}
            </ul>
        </div>
        """

    if follow_up:
        html += f"""
        <div style="margin-top: 4px; border-top: 1px dashed #e2e8f0; padding-top: 4px;">
            <strong style="color: #4f46e5; display: block; margin-bottom: 2px; font-size: 0.82rem;">🎯 Recommended Follow-up</strong>
            <p style="color: #4338ca; font-size: 0.88rem; font-weight: 600; margin: 0; line-height: 1.35;">
                {follow_up[0] if isinstance(follow_up, list) and follow_up else follow_up}
            </p>
        </div>
        """
    elif summary:
        html += f"""
        <div style="margin-top: 4px; border-top: 1px solid #e2e8f0; padding-top: 4px;">
            <p style="color: #475569; font-size: 0.82rem; line-height: 1.35; margin: 0;">{summary}</p>
        </div>
        """

    html += "</div>"
    html += '<p style="font-size: 0.68rem; color: #94a3b8; margin: 4px 0 0; font-style: italic;">Disclaimer: AI-assisted insight. Consult a physician.</p>'
    
    return html


def format_medical_response(response: str) -> str:
    """
    Format a legal response from LexEdge AI for proper display.
    Detects if response is JSON and uses the premium template.
    """
    if not response:
        return response
    
    # Try to detect JSON
    stripped = response.strip()
    if (stripped.startswith('{') and stripped.endswith('}')) or (stripped.startswith('```json') and stripped.endswith('```')):
        try:
            # Clean markdown code blocks if present
            json_str = stripped
            if json_str.startswith('```json'):
                json_str = json_str[7:-3].strip()
            
            data = json.loads(json_str)
            return format_premium_template(data)
        except Exception as e:
            logger.warning(f"Failed to parse JSON response for premium formatting: {e}")
            # Fall back to standard formatting
    
    formatted = response
    
    # Convert **bold** to <strong>bold</strong>
    formatted = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', formatted)
    
    # Convert *italic* to <em>italic</em> (but not bullet points)
    formatted = re.sub(r'(?<!\n)(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', formatted)
    
    # Convert markdown bullet points to HTML list items
    lines = formatted.split('\n')
    result_lines = []
    in_list = False
    
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('*   ') or stripped_line.startswith('* ') or stripped_line.startswith('- '):
            if not in_list:
                result_lines.append('<ul style="padding-left: 12px; margin: 4px 0; line-height: 1.35;">')
                in_list = True
            
            if stripped_line.startswith('*   '): content = stripped_line[4:]
            elif stripped_line.startswith('* '): content = stripped_line[2:]
            else: content = stripped_line[2:]
            
            result_lines.append(f'<li>{content}</li>')
        else:
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            result_lines.append(line)
    
    if in_list:
        result_lines.append('</ul>')
    
    formatted = '\n'.join(result_lines)
    
    # Convert double newlines to paragraph breaks
    formatted = re.sub(r'\n\n+', '</p><p>', formatted)
    
    if not formatted.startswith('<p>'):
        formatted = f'<p style="margin: 0 0 4px; line-height: 1.35;">{formatted}</p>'

    formatted = formatted.replace('</p><p>', '</p><p style="margin: 0 0 4px; line-height: 1.35;">')
    
    return formatted


def format_medical_response_markdown(response: str) -> str:
    """
    Clean up and normalize markdown formatting in a medical response.
    
    This version preserves markdown format but ensures consistency:
    - Normalizes bold markers
    - Normalizes bullet points
    - Ensures proper spacing
    
    Args:
        response: Raw response text from LexEdge AI
        
    Returns:
        str: Cleaned markdown response
    """
    if not response:
        return response
    
    formatted = response
    
    # Normalize bullet points (ensure consistent spacing)
    formatted = re.sub(r'^\*\s+', '• ', formatted, flags=re.MULTILINE)
    formatted = re.sub(r'^-\s+', '• ', formatted, flags=re.MULTILINE)
    
    # Ensure proper spacing after bullet points
    formatted = re.sub(r'•\s*', '• ', formatted)
    
    # Clean up excessive whitespace
    formatted = re.sub(r'\n{3,}', '\n\n', formatted)
    
    return formatted.strip()


def format_for_websocket(response: str, format_type: str = "html") -> dict:
    """
    Format a response for WebSocket delivery with metadata.
    
    Args:
        response: Raw response text
        format_type: "html" for HTML formatting, "markdown" for markdown cleanup
        
    Returns:
        dict: Formatted response with metadata
    """
    if format_type == "html":
        formatted_text = format_medical_response(response)
    else:
        formatted_text = format_medical_response_markdown(response)
    
    return {
        "text": formatted_text,
        "raw_text": response,
        "format": format_type,
        "has_formatting": formatted_text != response
    }
