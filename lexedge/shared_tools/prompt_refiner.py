"""
TOOL 7: Prompt Refinement Tool (Prompt Coach / Clarifier)

Purpose: Convert vague user prompts into structured "facts + context + request + format".
"""

import json
import logging
from typing import List, Optional
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# Common legal matter types
MATTER_TYPES = [
    "Anticipatory Bail Application",
    "Regular Bail Application",
    "Analysis of Quashing Petition (S.482/528)",
    "Analysis of Writ Petition (Art. 226/32)",
    "Analysis of Plaint",
    "Analysis of Written Statement",
    "Analysis of Temporary Injunction Application",
    "Analysis of Legal Notice",
    "Strategy for Reply to Legal Notice",
    "Criminal Appeal",
    "Civil Appeal",
    "Analysis of Special Leave Petition (SLP)",
    "Review Petition",
    "Revision Application",
    "Discharge Application",
    "Complaint under S.200",
    "Private Complaint",
    "Execution Application"
]

# Practice areas
PRACTICE_AREAS = [
    "Criminal Law",
    "Civil Litigation",
    "Property Disputes",
    "Family & Matrimonial",
    "Corporate & Commercial",
    "Constitutional & Writs",
    "Taxation",
    "Intellectual Property"
]

# Courts/Forums
FORUMS = [
    "Supreme Court of India",
    "High Court",
    "Sessions Court",
    "District Court",
    "Magistrate Court",
    "Family Court",
    "Consumer Forum",
    "NCLT",
    "ITAT",
    "Labour Court",
    "Rent Tribunal"
]


def refine_prompt(
    raw_prompt: str,
    tool_context: ToolContext = None
) -> str:
    """
    Convert vague user prompts into structured legal requests.

    Args:
        raw_prompt: The raw, potentially vague user input
        tool_context: ADK ToolContext

    Returns:
        JSON with improved prompt, missing information checklist, follow-up questions
    """
    logger.info(f"[PROMPT_REFINER] Refining: {raw_prompt[:50]}...")

    result = {
        "response_type": "refined_prompt",
        "original_prompt": raw_prompt,
        "analysis": {
            "detected_intent": "",
            "detected_practice_area": "",
            "detected_matter_type": "",
            "detected_forum": "",
            "clarity_score": 0,  # 1-10
        },
        "improved_prompt": "",
        "missing_information": [],
        "follow_up_questions": [],
        "prompt_formula": {
            "facts": "",
            "jurisdiction_forum": "",
            "relief_sought": "",
            "output_format": "",
            "constraints": ""
        }
    }

    prompt_lower = raw_prompt.lower()

    # Detect intent
    result["analysis"]["detected_intent"] = detect_intent(prompt_lower)

    # Detect practice area
    result["analysis"]["detected_practice_area"] = detect_practice_area(prompt_lower)

    # Detect matter type
    result["analysis"]["detected_matter_type"] = detect_matter_type(prompt_lower)

    # Detect forum
    result["analysis"]["detected_forum"] = detect_forum(prompt_lower)

    # Calculate clarity score
    result["analysis"]["clarity_score"] = calculate_clarity_score(raw_prompt)

    # Identify missing information
    result["missing_information"] = identify_missing_info(raw_prompt, result["analysis"])

    # Generate follow-up questions
    result["follow_up_questions"] = generate_follow_up_questions(raw_prompt, result["analysis"], result["missing_information"])

    # Build improved prompt
    result["improved_prompt"] = build_improved_prompt(raw_prompt, result["analysis"])

    # Build prompt formula
    result["prompt_formula"] = build_prompt_formula(raw_prompt, result["analysis"])

    return json.dumps(result, indent=2, ensure_ascii=False)


def detect_intent(prompt: str) -> str:
    """Detect the primary intent from the prompt."""
    if any(word in prompt for word in ["draft", "prepare", "write", "create"]):
        return "Strategic Strategy Development"
    elif any(word in prompt for word in ["research", "find", "search", "case law", "precedent"]):
        return "Legal Research"
    elif any(word in prompt for word in ["analyze", "review", "examine", "check"]):
        return "Document Analysis"
    elif any(word in prompt for word in ["advise", "advice", "opinion", "suggest"]):
        return "Legal Advisory"
    elif any(word in prompt for word in ["argue", "argument", "submission"]):
        return "Argument Construction"
    else:
        return "General Legal Query"


def detect_practice_area(prompt: str) -> str:
    """Detect the practice area from the prompt."""
    if any(word in prompt for word in ["bail", "fir", "arrest", "criminal", "accused", "quash", "482", "murder", "theft", "cheating"]):
        return "Criminal Law"
    elif any(word in prompt for word in ["divorce", "maintenance", "custody", "marriage", "498a", "domestic violence", "alimony"]):
        return "Family & Matrimonial"
    elif any(word in prompt for word in ["property", "land", "title", "possession", "partition", "eviction", "tenancy"]):
        return "Property Disputes"
    elif any(word in prompt for word in ["contract", "agreement", "nda", "corporate", "company", "shareholder", "director"]):
        return "Corporate & Commercial"
    elif any(word in prompt for word in ["tax", "income tax", "gst", "148", "assessment", "itat"]):
        return "Taxation"
    elif any(word in prompt for word in ["trademark", "patent", "copyright", "ip", "infringement"]):
        return "Intellectual Property"
    elif any(word in prompt for word in ["writ", "habeas", "mandamus", "226", "32", "fundamental right", "constitutional"]):
        return "Constitutional & Writs"
    elif any(word in prompt for word in ["suit", "injunction", "plaint", "civil", "recovery", "money"]):
        return "Civil Litigation"
    else:
        return "General"


def detect_matter_type(prompt: str) -> str:
    """Detect the type of matter requested."""
    for matter in MATTER_TYPES:
        if matter.lower() in prompt or matter.replace(" ", "").lower() in prompt.replace(" ", ""):
            return matter

    # Check for common variations
    if "bail" in prompt:
        if "anticipatory" in prompt or "pre-arrest" in prompt:
            return "Anticipatory Bail Application"
        else:
            return "Regular Bail Application"
    elif "quash" in prompt:
        return "Quashing Petition (S.482/528)"
    elif "writ" in prompt:
        return "Writ Petition (Art. 226/32)"
    elif "notice" in prompt:
        if "reply" in prompt or "response" in prompt:
            return "Reply to Legal Notice"
        else:
            return "Legal Notice"
    elif "injunction" in prompt:
        return "Temporary Injunction Application"
    elif "appeal" in prompt:
        if "criminal" in prompt:
            return "Criminal Appeal"
        else:
            return "Civil Appeal"

    return "Not specified"


def detect_forum(prompt: str) -> str:
    """Detect the forum/court from the prompt."""
    for forum in FORUMS:
        if forum.lower() in prompt:
            return forum

    # Check for abbreviations
    if "sc" in prompt.split() or "supreme" in prompt:
        return "Supreme Court of India"
    elif "hc" in prompt.split() or "high court" in prompt:
        return "High Court"
    elif "sessions" in prompt:
        return "Sessions Court"
    elif "magistrate" in prompt:
        return "Magistrate Court"
    elif "nclt" in prompt:
        return "NCLT"
    elif "itat" in prompt:
        return "ITAT"

    return "Not specified"


def calculate_clarity_score(prompt: str) -> int:
    """Calculate how clear/complete the prompt is (1-10)."""
    score = 5  # Base score

    # Positive factors
    if len(prompt) > 100:
        score += 1
    if len(prompt) > 200:
        score += 1

    # Check for essential elements
    prompt_lower = prompt.lower()

    # Facts present
    if any(word in prompt_lower for word in ["fact", "incident", "occurred", "happened", "alleges"]):
        score += 1

    # Court/Forum specified
    if any(word in prompt_lower for word in ["court", "sessions", "high court", "supreme", "tribunal"]):
        score += 1

    # Relief specified
    if any(word in prompt_lower for word in ["seek", "pray", "relief", "order", "direct"]):
        score += 1

    # Dates/timeline present
    if any(word in prompt_lower for word in ["dated", "date", "on", "since", "from"]):
        score += 0.5

    # Negative factors
    if len(prompt) < 50:
        score -= 2
    if "help" in prompt_lower and len(prompt) < 30:
        score -= 2

    return max(1, min(10, int(score)))


def identify_missing_info(prompt: str, analysis: dict) -> List[str]:
    """Identify missing essential information."""
    missing = []
    prompt_lower = prompt.lower()

    # Check for essential elements
    if analysis["detected_practice_area"] == "General":
        missing.append("Practice Area: Criminal/Civil/Family/Property/Corporate/Tax/IP/Constitutional")

    if analysis["detected_matter_type"] == "Not specified":
        missing.append("Matter Type: What is the primary legal issue? (Bail, Writ petition, Property dispute, etc.)")

    if analysis["detected_forum"] == "Not specified":
        missing.append("Court/Forum: Which court will this be filed in?")

    # Check for facts
    if not any(word in prompt_lower for word in ["fact", "happened", "incident", "alleges", "states", "background"]):
        missing.append("Facts: What are the key facts of the case?")

    # Check for parties
    if not any(word in prompt_lower for word in ["against", "versus", "v.", "complainant", "accused", "petitioner", "respondent"]):
        missing.append("Parties: Who are the parties involved?")

    # Check for dates
    if not any(word in prompt_lower for word in ["dated", "date", "on", "since", "when"]):
        missing.append("Timeline: Key dates and chronology")

    # Check for sections/law
    if not any(word in prompt_lower for word in ["section", "under", "bns", "ipc", "crpc", "bnss", "cpc", "act"]):
        missing.append("Applicable Law: What sections/laws are involved?")

    # Check for relief
    if not any(word in prompt_lower for word in ["seek", "pray", "want", "relief", "order", "direct"]):
        missing.append("Relief Sought: What relief/order are you seeking?")

    return missing


def generate_follow_up_questions(prompt: str, analysis: dict, missing: List[str]) -> List[str]:
    """Generate follow-up questions based on analysis."""
    questions = []
    prompt_lower = prompt.lower()

    # Priority questions based on practice area
    if analysis["detected_practice_area"] == "Criminal Law":
        if "fir" not in prompt_lower:
            questions.append("Is there an FIR registered? If yes, what is the FIR number and police station?")
        if "section" not in prompt_lower:
            questions.append("Under what sections (BNS/IPC) is the case registered?")
        if "bail" in prompt_lower and "custody" not in prompt_lower:
            questions.append("Is the person currently in custody or apprehending arrest?")

    elif analysis["detected_practice_area"] == "Family & Matrimonial":
        questions.append("What is the date of marriage and separation (if any)?")
        questions.append("Are there any children? What are their ages?")
        questions.append("What is the income and asset profile of both parties?")

    elif analysis["detected_practice_area"] == "Property Disputes":
        questions.append("What is the nature of the property (ancestral/self-acquired/joint)?")
        questions.append("Who is currently in possession of the property?")
        questions.append("What documents do you have to establish title?")

    elif analysis["detected_practice_area"] == "Corporate & Commercial":
        questions.append("Who are the parties to the agreement/transaction?")
        questions.append("What is the governing law and dispute resolution clause?")
        questions.append("What is the key commercial issue or breach?")

    # General questions based on missing info
    if "Facts" in str(missing):
        questions.append("Can you provide a chronological summary of the key facts?")

    if "Timeline" in str(missing):
        questions.append("What are the key dates involved (incident date, FIR date, notice date, etc.)?")

    if "Parties" in str(missing):
        questions.append("Who are the parties involved? (Names and roles)")

    # Limit to 5 most important questions
    return questions[:5]


def build_improved_prompt(prompt: str, analysis: dict) -> str:
    """Build an improved version of the prompt focus on strategy."""
    improved = f"""
Provide a Strategic Assessment for a {analysis['detected_matter_type'] if analysis['detected_matter_type'] != 'Not specified' else '[MATTER TYPE]'} for adjudication before {analysis['detected_forum'] if analysis['detected_forum'] != 'Not specified' else '[COURT/FORUM]'}.

PRACTICE AREA: {analysis['detected_practice_area']}

FACTS:
[Provide chronological facts here]
- Fact 1
- Fact 2
- Fact 3

PARTIES:
- Petitioner/Applicant: [NAME]
- Respondent/Opposite Party: [NAME]

APPLICABLE LAW:
- [Relevant sections under BNS/BNSS/BSA or other applicable acts]

RELIEF SOUGHT:
[Specific relief/order being sought]

OUTPUT FORMAT:
- Expert technical legal analysis and strategic roadmap
- Include key issues, procedural steps, and risk assessment
- Use formal legal language
"""
    return improved.strip()


def build_prompt_formula(prompt: str, analysis: dict) -> dict:
    """Build the prompt formula components."""
    return {
        "facts": "[Chronological facts of the case with dates]",
        "jurisdiction_forum": analysis["detected_forum"] if analysis["detected_forum"] != "Not specified" else "[Specify court/tribunal]",
        "relief_sought": "[Specific relief being sought - bail, quashing, injunction, etc.]",
        "output_format": f"Strategic Analysis and Roadmap for {analysis['detected_matter_type']}",
        "constraints": "Use BNS/BNSS/BSA (new criminal laws). Technical analysis. Flag uncertain citations."
    }
