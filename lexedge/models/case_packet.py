"""
Case Packet Model

Standard I/O contract for agent communication in LexEdge.
All agents should return consistent structures for reliable orchestration.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import json


class PracticeArea(Enum):
    """Legal practice areas."""
    CRIMINAL = "criminal"
    CIVIL = "civil"
    PROPERTY = "property"
    FAMILY = "family"
    CORPORATE = "corporate"
    CONSTITUTIONAL = "constitutional"
    TAX = "tax"
    IP = "ip"
    GENERAL = "general"


class DeliverableType(Enum):
    """Types of deliverables agents can produce."""
    DRAFT = "draft"
    RESEARCH_MEMO = "research_memo"
    ARGUMENTS = "arguments"
    CHECKLIST = "checklist"
    ANALYSIS = "analysis"
    OPINION = "opinion"
    NOTICE = "notice"
    REPLY = "reply"


class TimeSensitivity(Enum):
    """Urgency levels for legal matters."""
    URGENT = "urgent"
    STANDARD = "standard"
    LOW = "low"


class VerificationStatus(Enum):
    """Status of citation/information verification."""
    VERIFIED = "verified"
    NEEDS_VERIFICATION = "needs_verification"
    INVALID = "invalid"
    UNKNOWN = "unknown"


@dataclass
class Citation:
    """Legal citation with verification status."""
    case_name: str
    citation: str
    court: str = ""
    year: Optional[int] = None
    ratio: str = ""
    status: VerificationStatus = VerificationStatus.NEEDS_VERIFICATION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_name": self.case_name,
            "citation": self.citation,
            "court": self.court,
            "year": self.year,
            "ratio": self.ratio,
            "status": self.status.value
        }


@dataclass
class CasePacket:
    """
    Standard case information structure.

    This is the primary data structure passed between agents
    to maintain consistent case context.
    """
    # Jurisdiction and Forum
    jurisdiction: str = "India"
    forum: str = ""  # e.g., "Sessions Court, Pune", "High Court of Bombay"
    state: str = ""  # e.g., "Maharashtra", "Delhi"

    # Practice Area
    practice_area: PracticeArea = PracticeArea.GENERAL

    # Parties
    parties: List[str] = field(default_factory=list)
    petitioner: str = ""
    respondent: str = ""

    # Case Details
    case_number: str = ""
    fir_number: str = ""
    police_station: str = ""

    # Facts and Timeline
    facts: List[str] = field(default_factory=list)
    timeline: List[Dict[str, str]] = field(default_factory=list)  # [{date, event}]

    # Documents
    documents: List[str] = field(default_factory=list)

    # Legal Provisions
    statutes: List[str] = field(default_factory=list)  # e.g., ["BNS 103", "BNSS 482"]
    old_statutes: List[str] = field(default_factory=list)  # e.g., ["IPC 302", "CrPC 438"]

    # Relief and Issues
    relief_sought: str = ""
    legal_issues: List[str] = field(default_factory=list)

    # Urgency
    time_sensitivity: TimeSensitivity = TimeSensitivity.STANDARD
    deadline: Optional[str] = None

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["practice_area"] = self.practice_area.value
        data["time_sensitivity"] = self.time_sensitivity.value
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CasePacket":
        """Create CasePacket from dictionary."""
        if "practice_area" in data and isinstance(data["practice_area"], str):
            data["practice_area"] = PracticeArea(data["practice_area"])
        if "time_sensitivity" in data and isinstance(data["time_sensitivity"], str):
            data["time_sensitivity"] = TimeSensitivity(data["time_sensitivity"])
        return cls(**data)

    def add_fact(self, fact: str, date: str = None):
        """Add a fact to the case."""
        self.facts.append(fact)
        if date:
            self.timeline.append({"date": date, "event": fact})
        self.updated_at = datetime.now().isoformat()

    def add_statute(self, statute: str, is_new_code: bool = True):
        """Add a statutory provision."""
        if is_new_code:
            if statute not in self.statutes:
                self.statutes.append(statute)
        else:
            if statute not in self.old_statutes:
                self.old_statutes.append(statute)
        self.updated_at = datetime.now().isoformat()


@dataclass
class Deliverable:
    """Output deliverable from an agent."""
    type: DeliverableType
    content: str
    title: str = ""
    format: str = "text"  # text, markdown, pdf
    attachments: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "content": self.content,
            "title": self.title,
            "format": self.format,
            "attachments": self.attachments
        }


@dataclass
class AgentResponse:
    """
    Standard response structure from agents.

    All practice-area leads and orchestrators should return
    this structure for consistent handling.
    """
    # Core content
    case_packet: CasePacket
    deliverable: Deliverable

    # Citations
    citations_verified: List[Citation] = field(default_factory=list)
    citations_unverified: List[Citation] = field(default_factory=list)

    # Risk Assessment
    risks: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Follow-up
    next_questions: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)

    # Metadata
    agent_name: str = ""
    status: str = "completed"  # completed, needs_review, error
    disclaimer: str = "This is AI-assisted output for professional review."

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_packet": self.case_packet.to_dict(),
            "deliverable": self.deliverable.to_dict(),
            "citations": {
                "verified": [c.to_dict() for c in self.citations_verified],
                "needs_verification": [c.to_dict() for c in self.citations_unverified]
            },
            "risks": self.risks,
            "warnings": self.warnings,
            "next_questions": self.next_questions,
            "next_steps": self.next_steps,
            "agent_name": self.agent_name,
            "status": self.status,
            "disclaimer": self.disclaimer
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def add_risk(self, risk: str):
        """Add a risk note."""
        if risk not in self.risks:
            self.risks.append(risk)

    def add_citation(self, citation: Citation, verified: bool = False):
        """Add a citation."""
        if verified:
            self.citations_verified.append(citation)
        else:
            self.citations_unverified.append(citation)


# Factory functions
def create_case_packet(
    practice_area: str,
    facts: List[str],
    forum: str = "",
    parties: List[str] = None,
    statutes: List[str] = None,
    relief: str = "",
    urgent: bool = False
) -> CasePacket:
    """Create a new CasePacket with common defaults."""
    return CasePacket(
        jurisdiction="India",
        forum=forum,
        practice_area=PracticeArea(practice_area) if isinstance(practice_area, str) else practice_area,
        parties=parties or [],
        facts=facts,
        statutes=statutes or [],
        relief_sought=relief,
        time_sensitivity=TimeSensitivity.URGENT if urgent else TimeSensitivity.STANDARD
    )


def create_agent_response(
    case_packet: CasePacket,
    content: str,
    deliverable_type: str = "analysis",
    agent_name: str = "",
    risks: List[str] = None,
    next_questions: List[str] = None
) -> AgentResponse:
    """Create a new AgentResponse with common defaults."""
    return AgentResponse(
        case_packet=case_packet,
        deliverable=Deliverable(
            type=DeliverableType(deliverable_type) if isinstance(deliverable_type, str) else deliverable_type,
            content=content
        ),
        agent_name=agent_name,
        risks=risks or [],
        next_questions=next_questions or []
    )
