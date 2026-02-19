"""
LexEdge Practice-Area Lead Agents

Specialized agents for different areas of legal practice.

Phase 1 (P0):
- CriminalLawLeadAgent
- CivilLitigationLeadAgent
- CorporateCommercialLeadAgent

Phase 2 (P1):
- PropertyDisputesLeadAgent
- FamilyDivorceLeadAgent
- ConstitutionalWritsLeadAgent
- TaxationLeadAgent

Phase 3 (P2):
- IntellectualPropertyLeadAgent
"""

# Phase 1 - Core Practice Leads
from .criminal.criminal_lead_agent import CriminalLawLeadAgent
from .civil.civil_lead_agent import CivilLitigationLeadAgent
from .corporate.corporate_lead_agent import CorporateCommercialLeadAgent

# Phase 2 - Extended Practice Leads (uncomment when implemented)
from .property.property_lead_agent import PropertyDisputesLeadAgent
from .family.family_lead_agent import FamilyDivorceLeadAgent
from .constitutional.constitutional_lead_agent import ConstitutionalWritsLeadAgent
from .taxation.taxation_lead_agent import TaxationLeadAgent

# Phase 3 - Specialized Practice Leads (uncomment when implemented)
from .ip.ip_lead_agent import IntellectualPropertyLeadAgent

__all__ = [
    # Phase 1
    "CriminalLawLeadAgent",
    "CivilLitigationLeadAgent",
    "CorporateCommercialLeadAgent",
    # Phase 2
    "PropertyDisputesLeadAgent",
    "FamilyDivorceLeadAgent",
    "ConstitutionalWritsLeadAgent",
    "TaxationLeadAgent",
    # Phase 3
    "IntellectualPropertyLeadAgent",
]
