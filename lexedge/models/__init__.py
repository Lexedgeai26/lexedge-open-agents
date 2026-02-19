"""
LexEdge Data Models

Standard data structures for the legal multi-agent system.
"""

from .case_packet import (
    PracticeArea,
    DeliverableType,
    TimeSensitivity,
    VerificationStatus,
    CasePacket,
    Deliverable,
    Citation,
    AgentResponse,
    create_case_packet,
    create_agent_response
)

__all__ = [
    "PracticeArea",
    "DeliverableType",
    "TimeSensitivity",
    "VerificationStatus",
    "CasePacket",
    "Deliverable",
    "Citation",
    "AgentResponse",
    "create_case_packet",
    "create_agent_response"
]
