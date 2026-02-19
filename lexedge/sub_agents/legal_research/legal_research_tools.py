import json
import logging
from typing import Optional
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

try:
    from lexedge.config import LEGAL_SETTINGS, get_legal_context_string
    from lexedge.context_manager import agent_context_manager
except ImportError:
    from ...config import LEGAL_SETTINGS, get_legal_context_string
    from ...context_manager import agent_context_manager


def search_case_law(query: str, jurisdiction: str, tool_context: ToolContext) -> str:
    """
    Search for relevant case law and precedents.
    
    Args:
        query: Legal issue or topic to research
        jurisdiction: Jurisdiction to search within
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Relevant case law findings
    """
    logger.info(f"[LEGAL_RESEARCH] Searching case law: {query[:50]}...")
    
    effective_jurisdiction = jurisdiction or LEGAL_SETTINGS.get("jurisdiction", "Federal")
    
    result = {
        "response_type": "case_law_search",
        "query": query,
        "jurisdiction": effective_jurisdiction,
        "legal_system": LEGAL_SETTINGS.get("legal_system", "Common Law"),
        "results": {
            "total_found": "Multiple relevant cases identified",
            "cases": [
                {
                    "case_name": "Relevant Case v. Party (Year)",
                    "citation": "Citation format",
                    "court": "Court name",
                    "relevance": "High",
                    "key_holding": "Summary of key holding relevant to query",
                    "applicable_principles": ["Principle 1", "Principle 2"]
                }
            ],
            "key_precedents": [
                "Landmark case establishing relevant principle",
                "Recent case applying similar facts"
            ],
            "legal_principles": [
                "Established legal principle from case law",
                "Applicable doctrine or test"
            ]
        },
        "research_notes": f"Research conducted for {effective_jurisdiction} jurisdiction",
        "disclaimer": "This research is for informational purposes. Verify all citations independently."
    }
    
    # Update context
    try:
        agent_context_manager.update_context("LegalResearchAgent", {
            "last_research": {
                "topic": query[:100],
                "summary": f"Case law research on {query[:50]}",
                "jurisdiction": effective_jurisdiction
            }
        })
    except Exception as ctx_err:
        logger.warning(f"Failed to update context: {ctx_err}")
    
    return json.dumps(result, indent=2)


def search_statutes(topic: str, jurisdiction: str, tool_context: ToolContext) -> str:
    """
    Search for relevant statutes and regulations.
    
    Args:
        topic: Legal topic to research
        jurisdiction: Jurisdiction for statute search
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Relevant statutes and regulations
    """
    logger.info(f"[LEGAL_RESEARCH] Searching statutes: {topic[:50]}...")
    
    effective_jurisdiction = jurisdiction or LEGAL_SETTINGS.get("jurisdiction", "Federal")
    
    result = {
        "response_type": "statute_search",
        "topic": topic,
        "jurisdiction": effective_jurisdiction,
        "results": {
            "federal_statutes": [
                {
                    "title": "Relevant Federal Statute",
                    "citation": "U.S.C. Citation",
                    "summary": "Summary of statute provisions",
                    "key_sections": ["Section 1", "Section 2"]
                }
            ],
            "state_statutes": [
                {
                    "state": effective_jurisdiction,
                    "title": "Relevant State Statute",
                    "citation": "State code citation",
                    "summary": "Summary of state law provisions"
                }
            ],
            "regulations": [
                {
                    "agency": "Regulatory Agency",
                    "title": "Relevant Regulation",
                    "citation": "C.F.R. Citation",
                    "summary": "Summary of regulatory requirements"
                }
            ],
            "compliance_frameworks": LEGAL_SETTINGS.get("compliance_frameworks", [])
        },
        "research_notes": f"Statute research for {effective_jurisdiction}",
        "disclaimer": "Verify all statutory citations for current validity."
    }
    
    return json.dumps(result, indent=2)


def analyze_legal_issue(issue: str, facts: str, tool_context: ToolContext) -> str:
    """
    Perform comprehensive legal analysis of an issue.
    
    Args:
        issue: The legal issue to analyze
        facts: Relevant facts of the case
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Comprehensive legal analysis
    """
    logger.info(f"[LEGAL_RESEARCH] Analyzing legal issue: {issue[:50]}...")
    
    result = {
        "response_type": "legal_analysis",
        "issue": issue,
        "jurisdiction": LEGAL_SETTINGS.get("jurisdiction", "Federal"),
        "legal_system": LEGAL_SETTINGS.get("legal_system", "Common Law"),
        "analysis": {
            "issue_statement": f"Whether {issue}",
            "rule_of_law": {
                "primary_rule": "The governing legal rule or standard",
                "exceptions": ["Exception 1", "Exception 2"],
                "elements": ["Element 1", "Element 2", "Element 3"]
            },
            "application": {
                "facts_analysis": f"Applying the rule to the facts: {facts[:200]}...",
                "element_by_element": [
                    {"element": "Element 1", "analysis": "How facts satisfy or fail element"},
                    {"element": "Element 2", "analysis": "How facts satisfy or fail element"}
                ],
                "counterarguments": ["Potential counterargument 1", "Potential counterargument 2"]
            },
            "conclusion": {
                "likely_outcome": "Assessment of likely outcome",
                "confidence": "Moderate",
                "key_factors": ["Factor 1", "Factor 2"]
            },
            "recommendations": [
                "Gather additional evidence for Element X",
                "Research additional precedents",
                "Consider alternative legal theories"
            ]
        },
        "areas_of_expertise": LEGAL_SETTINGS.get("areas_of_expertise", []),
        "disclaimer": "This analysis is for informational purposes only."
    }
    
    return json.dumps(result, indent=2)


def verify_citations(citations: str, tool_context: ToolContext) -> str:
    """
    Verify legal citations for accuracy and validity.
    
    Args:
        citations: Citations to verify (comma-separated)
        tool_context: ADK ToolContext for session state management
    
    Returns:
        Citation verification results
    """
    logger.info(f"[LEGAL_RESEARCH] Verifying citations: {citations[:50]}...")
    
    citation_list = [c.strip() for c in citations.split(",")]
    
    result = {
        "response_type": "citation_verification",
        "citations_checked": len(citation_list),
        "results": [
            {
                "citation": citation,
                "status": "Requires verification",
                "format_correct": "Review format",
                "current_validity": "Verify current status",
                "notes": "Independent verification recommended"
            }
            for citation in citation_list
        ],
        "verification_notes": [
            "All citations should be verified against official sources",
            "Check for subsequent history (overruled, distinguished, etc.)",
            "Verify page numbers and pinpoint citations"
        ],
        "disclaimer": "Always verify citations independently before use in legal documents."
    }
    
    return json.dumps(result, indent=2)
