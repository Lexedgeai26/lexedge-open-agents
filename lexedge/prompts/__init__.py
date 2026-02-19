"""
LexEdge Prompts Library

Canonical prompts for the legal multi-agent system.
These prompts are authoritative and should not be modified at runtime.

Modules:
- system_prompts: Global safety and professionalism prompts
- tool_prompts: Tool-specific prompt templates
- agent_prompts: Agent instruction templates
"""

from .system_prompts import (
    GLOBAL_SAFETY_PROMPT,
    STANDARD_DISCLAIMER,
    JURISDICTION_PROMPT
)

from .agent_prompts import (
    get_router_agent_prompt,
    get_gatekeeper_agent_prompt,
    get_prompt_coach_prompt,
    get_criminal_lead_prompt,
    get_civil_lead_prompt,
    get_corporate_lead_prompt,
    get_property_lead_prompt,
    get_family_lead_prompt,
    get_constitutional_lead_prompt,
    get_taxation_lead_prompt,
    get_ip_lead_prompt
)

__all__ = [
    "GLOBAL_SAFETY_PROMPT",
    "STANDARD_DISCLAIMER",
    "JURISDICTION_PROMPT",
    "get_router_agent_prompt",
    "get_gatekeeper_agent_prompt",
    "get_prompt_coach_prompt",
    "get_criminal_lead_prompt",
    "get_civil_lead_prompt",
    "get_corporate_lead_prompt",
    "get_property_lead_prompt",
    "get_family_lead_prompt",
    "get_constitutional_lead_prompt",
    "get_taxation_lead_prompt",
    "get_ip_lead_prompt"
]
