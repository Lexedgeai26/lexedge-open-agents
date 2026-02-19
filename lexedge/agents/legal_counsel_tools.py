"""
Legal counsel tools using the Python Ollama SDK.

These tools are called by the LegalCounselAgent sub-agent.
The root agent (gpt-oss via ADK) delegates to LegalCounselAgent,
which then uses these tools to call Ollama for actual legal work.
"""

import os
import logging
import ollama
from lexedge.prompts.prompt_loader import load_prompt, render_prompt

logger = logging.getLogger(__name__)

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")

PRACTICE_PROMPT_FILES = {
    "criminal": "legal_counsel/practice_criminal.txt",
    "civil": "legal_counsel/practice_civil.txt",
    "property": "legal_counsel/practice_property.txt",
    "family": "legal_counsel/practice_family.txt",
    "corporate": "legal_counsel/practice_corporate.txt",
    "constitutional": "legal_counsel/practice_constitutional.txt",
    "taxation": "legal_counsel/practice_taxation.txt",
    "ip": "legal_counsel/practice_ip.txt",
    "general": "legal_counsel/practice_general.txt"
}

DISCLAIMER = load_prompt("legal_counsel/disclaimer.txt")


def legal_query(query: str, practice_area: str = "general") -> dict:
    """
    Process a legal query using the Ollama LLM.

    Use this tool to answer any legal question. Pick the correct practice_area
    from: criminal, civil, property, family, corporate, constitutional,
    taxation, ip, general.

    Args:
        query: The user's legal question or request.
        practice_area: One of criminal, civil, property, family, corporate,
                       constitutional, taxation, ip, general.

    Returns:
        dict with 'result' containing the legal response text.
    """
    area = practice_area.lower().strip()
    system_prompt = load_prompt(PRACTICE_PROMPT_FILES.get(area, PRACTICE_PROMPT_FILES["general"]))

    logger.info(f"[legal_query] area={area}, model={OLLAMA_MODEL}, query={query[:80]}...")

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            options={"temperature": 0.5},
        )
        content = response.get("message", {}).get("content", "")
        if not content:
            content = "I was unable to generate a response. Please try rephrasing your query."
        logger.info(f"[legal_query] response length={len(content)}")
        return {"result": content + DISCLAIMER}
    except Exception as e:
        logger.error(f"[legal_query] Ollama error [{type(e).__name__}]: {repr(e)}")
        return {
            "result": (
                "I encountered an error processing your request. "
                f"Error: {type(e).__name__}: {e}"
            )
        }


def draft_document(
    document_type: str,
    facts: str,
    practice_area: str = "general",
) -> dict:
    """
    Draft a legal document outline or template.

    Use this tool when the user asks to draft a petition, application,
    plaint, reply, notice, agreement, or any legal document.

    Args:
        document_type: Type of document (e.g. bail application, plaint,
                       writ petition, contract, legal notice).
        facts: Key facts, parties, dates, and context for the document.
        practice_area: One of criminal, civil, property, family, corporate,
                       constitutional, taxation, ip, general.

    Returns:
        dict with 'result' containing the drafted document outline.
    """
    area = practice_area.lower().strip()
    system_prompt = load_prompt(PRACTICE_PROMPT_FILES.get(area, PRACTICE_PROMPT_FILES["general"]))
    system_prompt += "\n\n" + load_prompt("legal_counsel/drafting_mode.txt")

    user_prompt_template = load_prompt("legal_counsel/draft_document_user_prompt.txt")
    user_prompt = render_prompt(
        user_prompt_template,
        document_type=document_type,
        facts=facts
    )

    logger.info(f"[draft_document] type={document_type}, area={area}")

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": 0.3},
        )
        content = response.get("message", {}).get("content", "")
        if not content:
            content = "I was unable to generate the document. Please provide more details."
        return {"result": content + DISCLAIMER}
    except Exception as e:
        logger.error(f"[draft_document] Ollama error [{type(e).__name__}]: {repr(e)}")
        return {
            "result": (
                "I encountered an error drafting the document. "
                f"Error: {type(e).__name__}: {e}"
            )
        }


def analyze_document(document_text: str, analysis_type: str = "review") -> dict:
    """
    Analyze a legal document (contract, agreement, petition, etc.).

    Use this tool when the user uploads or pastes a document for review.

    Args:
        document_text: The full text of the document to analyze.
        analysis_type: Type of analysis - review, risk_scan, summary,
                       or clause_check.

    Returns:
        dict with 'result' containing the analysis.
    """
    system_prompt = load_prompt("legal_counsel/document_analysis_system.txt")

    analysis_instruction_files = {
        "review": "legal_counsel/document_analysis_review.txt",
        "risk_scan": "legal_counsel/document_analysis_risk_scan.txt",
        "summary": "legal_counsel/document_analysis_summary.txt",
        "clause_check": "legal_counsel/document_analysis_clause_check.txt"
    }

    instruction = load_prompt(
        analysis_instruction_files.get(
            analysis_type,
            analysis_instruction_files["review"]
        )
    )
    user_prompt = f"{instruction}\n\n---\n\n{document_text}"

    logger.info(f"[analyze_document] type={analysis_type}, doc_len={len(document_text)}")

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": 0.3},
        )
        content = response.get("message", {}).get("content", "")
        if not content:
            content = "I was unable to analyze the document. Please try again."
        return {"result": content + DISCLAIMER}
    except Exception as e:
        logger.error(f"[analyze_document] Ollama error [{type(e).__name__}]: {repr(e)}")
        return {
            "result": (
                "I encountered an error analyzing the document. "
                f"Error: {type(e).__name__}: {e}"
            )
        }
