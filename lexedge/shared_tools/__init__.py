"""
LexEdge Shared Tools Library

Canonical tool implementations for the legal multi-agent system.
These tools are shared across all practice-area lead agents.

Tools:
1. statute_mapper - Map legal issues to statutory provisions (BNS/BNSS/BSA)
2. case_law_research - Search SC/HC case law
3. citation_verifier - Validate legal citations
4. court_drafting - Generate court-ready documents
5. document_analyzer - Analyze legal documents
6. argument_builder - Construct legal arguments
7. prompt_refiner - Refine user prompts
8. quality_gatekeeper - Validate outputs
"""

from .statute_mapper import map_statute_sections
from .case_law_research import research_case_law
from .citation_verifier import verify_citation
from .document_analyzer import analyze_document
from .argument_builder import build_arguments
from .prompt_refiner import refine_prompt
from .quality_gatekeeper import validate_output

__all__ = [
    "map_statute_sections",
    "research_case_law",
    "verify_citation",
    "analyze_document",
    "build_arguments",
    "refine_prompt",
    "validate_output",
]
