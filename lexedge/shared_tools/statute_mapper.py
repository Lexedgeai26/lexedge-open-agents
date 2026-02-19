"""
TOOL 1: Statute & Section Mapping Tool

Purpose: Identify applicable provisions, map old↔new laws, list ingredients
and procedure, flag limitation/jurisdiction.

Handles mapping between:
- BNS (Bharatiya Nyaya Sanhita) ↔ IPC (Indian Penal Code)
- BNSS (Bharatiya Nagarik Suraksha Sanhita) ↔ CrPC (Code of Criminal Procedure)
- BSA (Bharatiya Sakshya Adhiniyam) ↔ IEA (Indian Evidence Act)
"""

import json
import logging
from typing import Optional, List, Dict
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# Cross-mapping tables for major provisions
BNS_IPC_MAPPING = {
    # Murder and Culpable Homicide
    "BNS 101": {"ipc": "IPC 299", "title": "Culpable homicide", "ingredients": ["Causing death", "Intention or knowledge", "Act likely to cause death"]},
    "BNS 103": {"ipc": "IPC 302", "title": "Murder", "ingredients": ["Causing death", "Intention to cause death", "Knowledge that act will cause death"]},
    "BNS 105": {"ipc": "IPC 304", "title": "Culpable homicide not amounting to murder", "ingredients": ["Causing death without premeditation", "Sudden provocation", "No intention to cause death"]},

    # Hurt and Grievous Hurt
    "BNS 115": {"ipc": "IPC 319", "title": "Hurt", "ingredients": ["Causing bodily pain", "Disease or infirmity", "To any person"]},
    "BNS 117": {"ipc": "IPC 323", "title": "Voluntarily causing hurt", "ingredients": ["Voluntary act", "Causing hurt", "Without provocation"]},
    "BNS 118": {"ipc": "IPC 324", "title": "Voluntarily causing hurt by dangerous weapons", "ingredients": ["Using dangerous weapon", "Causing hurt", "Intentional act"]},
    "BNS 114": {"ipc": "IPC 320", "title": "Grievous hurt", "ingredients": ["Emasculation", "Permanent privation of sight/hearing", "Fracture or dislocation", "Hurt endangering life"]},

    # Kidnapping and Abduction
    "BNS 137": {"ipc": "IPC 359", "title": "Kidnapping", "ingredients": ["Taking person from lawful guardianship", "Without consent of guardian", "Minor under 16/18 years"]},
    "BNS 138": {"ipc": "IPC 362", "title": "Abduction", "ingredients": ["Compelling by force", "Inducing by deceitful means", "To go from any place"]},

    # Sexual Offences
    "BNS 63": {"ipc": "IPC 375", "title": "Rape", "ingredients": ["Sexual intercourse", "Against will/without consent", "With or without consent when under 18"]},
    "BNS 64": {"ipc": "IPC 376", "title": "Punishment for rape", "ingredients": ["Commission of rape", "Rigorous imprisonment not less than 10 years"]},

    # Theft and Robbery
    "BNS 303": {"ipc": "IPC 378", "title": "Theft", "ingredients": ["Dishonest intention", "Moving moveable property", "Out of possession without consent"]},
    "BNS 309": {"ipc": "IPC 392", "title": "Robbery", "ingredients": ["Theft or extortion", "Causing death/hurt/wrongful restraint", "Fear of instant death/hurt"]},
    "BNS 310": {"ipc": "IPC 395", "title": "Dacoity", "ingredients": ["Five or more persons", "Conjointly commit robbery", "Attempt to commit robbery"]},

    # Cheating and Fraud
    "BNS 318": {"ipc": "IPC 415", "title": "Cheating", "ingredients": ["Deception", "Fraudulent/dishonest inducement", "Delivery of property or consent"]},
    "BNS 316": {"ipc": "IPC 420", "title": "Cheating and dishonestly inducing delivery of property", "ingredients": ["Cheating", "Dishonest inducement", "Delivery of property"]},

    # Criminal Breach of Trust
    "BNS 316": {"ipc": "IPC 405", "title": "Criminal breach of trust", "ingredients": ["Entrustment of property", "Dishonest misappropriation", "Conversion or disposal"]},

    # Defamation
    "BNS 356": {"ipc": "IPC 499", "title": "Defamation", "ingredients": ["Imputation", "Harming reputation", "By words, signs, or visible representations"]},

    # Criminal Intimidation
    "BNS 351": {"ipc": "IPC 503", "title": "Criminal intimidation", "ingredients": ["Threatening injury", "To person, reputation, or property", "Intent to cause alarm"]},

    # Forgery
    "BNS 336": {"ipc": "IPC 463", "title": "Forgery", "ingredients": ["Making false document", "Intent to cause damage", "Support any claim or title"]},
}

BNSS_CRPC_MAPPING = {
    # Bail Provisions
    "BNSS 480": {"crpc": "CrPC 436", "title": "Bail in bailable offences", "procedure": ["Right to bail", "Release on bond", "Sureties as required"]},
    "BNSS 481": {"crpc": "CrPC 437", "title": "Bail in non-bailable offences", "procedure": ["Court discretion", "Reasonable grounds", "Conditions may be imposed"]},
    "BNSS 482": {"crpc": "CrPC 438", "title": "Anticipatory bail", "procedure": ["Apprehension of arrest", "High Court/Sessions Court", "Conditions may be imposed"]},
    "BNSS 483": {"crpc": "CrPC 439", "title": "Special powers of High Court/Sessions Court", "procedure": ["Bail application", "Cancellation of bail", "Conditions modification"]},

    # FIR and Investigation
    "BNSS 173": {"crpc": "CrPC 154", "title": "Information in cognizable cases (FIR)", "procedure": ["Written information", "Reduced to writing if oral", "Copy to informant"]},
    "BNSS 175": {"crpc": "CrPC 156", "title": "Police officer's power to investigate", "procedure": ["Cognizable case", "Investigation without order", "Report to Magistrate"]},
    "BNSS 176": {"crpc": "CrPC 157", "title": "Procedure for investigation", "procedure": ["Send report to Magistrate", "Proceed to spot", "Investigation steps"]},

    # Quashing and Inherent Powers
    "BNSS 528": {"crpc": "CrPC 482", "title": "Inherent powers of High Court", "procedure": ["Quashing FIR/proceedings", "Prevent abuse of process", "Secure ends of justice"]},

    # Arrest
    "BNSS 35": {"crpc": "CrPC 41", "title": "When police may arrest without warrant", "procedure": ["Cognizable offence", "Reasonable suspicion", "Credible information"]},
    "BNSS 37": {"crpc": "CrPC 41A", "title": "Notice of appearance before arrest", "procedure": ["7 years or less imprisonment", "Notice before arrest", "Compliance required"]},

    # Remand
    "BNSS 187": {"crpc": "CrPC 167", "title": "Procedure when investigation not completed", "procedure": ["Detention up to 15 days", "Magistrate remand", "Maximum 60/90 days"]},

    # Charge
    "BNSS 230": {"crpc": "CrPC 211", "title": "Contents of charge", "procedure": ["Offence stated", "Law and section", "Name of offence given"]},
    "BNSS 251": {"crpc": "CrPC 227", "title": "Discharge", "procedure": ["No sufficient ground", "Sessions Court", "Record reasons"]},

    # Trial
    "BNSS 262": {"crpc": "CrPC 238", "title": "Compliance with S.207 (now S.230)", "procedure": ["Documents to accused", "Police report copies", "Statements of witnesses"]},
}

BSA_IEA_MAPPING = {
    # Relevancy
    "BSA 3": {"iea": "IEA 5", "title": "Facts which are part of same transaction", "scope": "Res gestae doctrine"},
    "BSA 4": {"iea": "IEA 6", "title": "Relevancy of facts forming part of same transaction", "scope": "Connected facts"},

    # Admissions and Confessions
    "BSA 15": {"iea": "IEA 17", "title": "Admission defined", "scope": "Statement suggesting inference"},
    "BSA 20": {"iea": "IEA 24", "title": "Confession caused by inducement, threat or promise", "scope": "Involuntary confession inadmissible"},
    "BSA 21": {"iea": "IEA 25", "title": "Confession to police officer", "scope": "Not admissible"},
    "BSA 22": {"iea": "IEA 26", "title": "Confession while in custody of police", "scope": "Not admissible unless before Magistrate"},

    # Witnesses
    "BSA 118": {"iea": "IEA 118", "title": "Who may testify", "scope": "Competency of witnesses"},
    "BSA 122": {"iea": "IEA 122", "title": "Communications during marriage", "scope": "Privileged communication"},

    # Documentary Evidence
    "BSA 61": {"iea": "IEA 61", "title": "Proof of contents of documents", "scope": "Primary evidence preferred"},
    "BSA 63": {"iea": "IEA 63", "title": "Primary evidence", "scope": "Document itself produced"},
    "BSA 65": {"iea": "IEA 65", "title": "Cases where secondary evidence admissible", "scope": "Original not available"},

    # Electronic Evidence
    "BSA 63": {"iea": "IEA 65B", "title": "Admissibility of electronic records", "scope": "Certificate required, authenticity"},
}


def map_statute_sections(
    legal_issue: str,
    court_level: str = "Sessions Court",
    old_law_reference: str = None,
    tool_context: ToolContext = None
) -> str:
    """
    Map legal issues to applicable statutory provisions.
    Handles BNS/BNSS/BSA ↔ IPC/CrPC/IEA cross-mapping.

    Args:
        legal_issue: Description of the legal issue
        court_level: Forum/Court level (Sessions Court, High Court, Supreme Court, etc.)
        old_law_reference: Reference to old law section if known (e.g., "IPC 302")
        tool_context: ADK ToolContext for session state

    Returns:
        JSON with section mapping, ingredients, procedural notes, and red flags
    """
    logger.info(f"[STATUTE_MAPPER] Mapping: {legal_issue[:50]}...")

    result = {
        "response_type": "statute_mapping",
        "jurisdiction": "India",
        "court_level": court_level,
        "legal_issue": legal_issue,
        "preference": "BNS / BNSS / BSA (New Criminal Laws effective July 2024)",
        "section_mapping": [],
        "essential_ingredients": [],
        "procedural_notes": [],
        "red_flags": [],
        "disclaimer": "Verify all section mappings on official sources. New codes effective from July 1, 2024."
    }

    # Check for old law reference and map to new
    if old_law_reference:
        old_ref_upper = old_law_reference.upper().strip()

        # Search in BNS-IPC mapping
        for bns_section, details in BNS_IPC_MAPPING.items():
            if details["ipc"].upper() == old_ref_upper:
                result["section_mapping"].append({
                    "old_provision": details["ipc"],
                    "new_provision": bns_section,
                    "title": details["title"],
                    "status": "Mapped"
                })
                result["essential_ingredients"].extend(details.get("ingredients", []))
                break

        # Search in BNSS-CrPC mapping
        for bnss_section, details in BNSS_CRPC_MAPPING.items():
            if details["crpc"].upper() == old_ref_upper:
                result["section_mapping"].append({
                    "old_provision": details["crpc"],
                    "new_provision": bnss_section,
                    "title": details["title"],
                    "status": "Mapped"
                })
                result["procedural_notes"].extend(details.get("procedure", []))
                break

        # Search in BSA-IEA mapping
        for bsa_section, details in BSA_IEA_MAPPING.items():
            if details["iea"].upper() == old_ref_upper:
                result["section_mapping"].append({
                    "old_provision": details["iea"],
                    "new_provision": bsa_section,
                    "title": details["title"],
                    "status": "Mapped"
                })
                break

    # Analyze legal issue for applicable sections
    issue_lower = legal_issue.lower()

    # Criminal matters
    if any(word in issue_lower for word in ["murder", "homicide", "killing", "death"]):
        result["section_mapping"].append({
            "old_provision": "IPC 302/304",
            "new_provision": "BNS 103/105",
            "title": "Murder / Culpable Homicide",
            "status": "Likely Applicable"
        })
        result["essential_ingredients"].extend([
            "Causing death of a human being",
            "Intention to cause death OR",
            "Knowledge that act is likely to cause death",
            "Act done with intention of causing bodily injury likely to cause death"
        ])
        result["procedural_notes"].extend([
            "Non-bailable and non-compoundable offence",
            "Sessions Court trial mandatory",
            "Bail under BNSS 483 (CrPC 439) - very stringent"
        ])

    if any(word in issue_lower for word in ["bail", "anticipatory", "arrest"]):
        result["section_mapping"].append({
            "old_provision": "CrPC 438/439",
            "new_provision": "BNSS 482/483",
            "title": "Anticipatory Bail / Regular Bail",
            "status": "Applicable"
        })
        result["procedural_notes"].extend([
            "Anticipatory bail: High Court or Sessions Court",
            "Regular bail: Court where case is pending",
            "Conditions may be imposed under BNSS 482(2)",
            "Bail bond and sureties required"
        ])

    if any(word in issue_lower for word in ["quash", "quashing", "482", "abuse of process"]):
        result["section_mapping"].append({
            "old_provision": "CrPC 482",
            "new_provision": "BNSS 528",
            "title": "Inherent Powers - Quashing",
            "status": "Applicable"
        })
        result["procedural_notes"].extend([
            "Only High Court has inherent powers",
            "FIR/Chargesheet/Proceedings can be quashed",
            "Apply Bhajan Lal guidelines for quashing",
            "Civil nature of dispute - strong ground"
        ])

    if any(word in issue_lower for word in ["fir", "complaint", "cognizable"]):
        result["section_mapping"].append({
            "old_provision": "CrPC 154/156",
            "new_provision": "BNSS 173/175",
            "title": "FIR and Investigation",
            "status": "Applicable"
        })
        result["procedural_notes"].extend([
            "FIR mandatory for cognizable offences (Lalita Kumari)",
            "Preliminary inquiry permitted in certain cases",
            "Zero FIR provision available",
            "Copy of FIR to informant mandatory"
        ])

    if any(word in issue_lower for word in ["cheating", "fraud", "420", "dishonest"]):
        result["section_mapping"].append({
            "old_provision": "IPC 420/406",
            "new_provision": "BNS 318/316",
            "title": "Cheating / Criminal Breach of Trust",
            "status": "Likely Applicable"
        })
        result["essential_ingredients"].extend([
            "Deception by the accused",
            "Dishonest or fraudulent inducement",
            "Delivery of property or valuable security",
            "Intent to cheat from inception"
        ])

    if any(word in issue_lower for word in ["hurt", "injury", "assault", "beating"]):
        result["section_mapping"].append({
            "old_provision": "IPC 323/324/325",
            "new_provision": "BNS 115/117/118",
            "title": "Hurt / Grievous Hurt",
            "status": "Likely Applicable"
        })
        result["essential_ingredients"].extend([
            "Voluntary causing of hurt",
            "Bodily pain, disease or infirmity",
            "Use of weapon (if 324 equivalent)"
        ])

    # Add red flags
    if "limitation" in issue_lower or "time" in issue_lower:
        result["red_flags"].append("CHECK LIMITATION: Verify if complaint/petition is within limitation period")

    if "jurisdiction" in issue_lower:
        result["red_flags"].append("JURISDICTION ISSUE: Verify territorial and pecuniary jurisdiction")

    if any(word in issue_lower for word in ["delay", "late", "after"]):
        result["red_flags"].append("DELAY IN FIR: Explain delay satisfactorily - may affect credibility")

    # Add general procedural notes based on court level
    if court_level.lower() == "sessions court":
        result["procedural_notes"].append("Sessions Court: Original jurisdiction for offences punishable with death/life/7+ years")
    elif court_level.lower() == "high court":
        result["procedural_notes"].append("High Court: Writ jurisdiction (Art. 226), Appellate, Revisional, Inherent powers (BNSS 528)")
    elif court_level.lower() == "supreme court":
        result["procedural_notes"].append("Supreme Court: SLP (Art. 136), Appeals, Writ (Art. 32), Review")

    # Add disclaimer about verification
    result["red_flags"].append("ALL MAPPINGS REQUIRE VERIFICATION: Cross-check with official BNS/BNSS/BSA texts")

    return json.dumps(result, indent=2, ensure_ascii=False)


def get_section_details(section: str) -> Optional[Dict]:
    """Get details for a specific section."""
    section_upper = section.upper().strip()

    # Check all mappings
    for bns_section, details in BNS_IPC_MAPPING.items():
        if bns_section.upper() == section_upper or details["ipc"].upper() == section_upper:
            return {
                "bns": bns_section,
                "ipc": details["ipc"],
                "title": details["title"],
                "ingredients": details.get("ingredients", [])
            }

    for bnss_section, details in BNSS_CRPC_MAPPING.items():
        if bnss_section.upper() == section_upper or details["crpc"].upper() == section_upper:
            return {
                "bnss": bnss_section,
                "crpc": details["crpc"],
                "title": details["title"],
                "procedure": details.get("procedure", [])
            }

    for bsa_section, details in BSA_IEA_MAPPING.items():
        if bsa_section.upper() == section_upper or details["iea"].upper() == section_upper:
            return {
                "bsa": bsa_section,
                "iea": details["iea"],
                "title": details["title"],
                "scope": details.get("scope", "")
            }

    return None
