"""
Legal Prompt Coach Agent

Orchestrator that converts vague user prompts into structured,
court-usable legal requests using the prompt formula.
"""

from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext

try:
    from lexedge.config import LlmModel
except ImportError:
    from ..config import LlmModel

from lexedge.prompts.agent_prompts import get_prompt_coach_prompt
from lexedge.shared_tools import refine_prompt


def prompt_coach_instruction_provider(context: ReadonlyContext) -> str:
    """Dynamic instruction provider for prompt coach agent."""
    return get_prompt_coach_prompt()


def analyze_prompt_completeness(prompt: str) -> str:
    """
    Analyze a legal prompt for completeness.

    Args:
        prompt: User's raw prompt

    Returns:
        JSON with analysis and missing elements
    """
    import json

    prompt_lower = prompt.lower()

    # Check for essential elements
    elements = {
        "facts": {
            "present": any(word in prompt_lower for word in ["fact", "happened", "incident", "alleges", "states", "case is"]),
            "description": "Chronological facts of the case"
        },
        "parties": {
            "present": any(word in prompt_lower for word in ["against", "versus", "v.", "complainant", "accused", "petitioner", "respondent", "client"]),
            "description": "Names and roles of parties involved"
        },
        "jurisdiction": {
            "present": any(word in prompt_lower for word in ["court", "sessions", "high court", "supreme", "district", "india", "state"]),
            "description": "Court/forum and geographic jurisdiction"
        },
        "relief": {
            "present": any(word in prompt_lower for word in ["seek", "pray", "want", "relief", "order", "bail", "quash", "injunction"]),
            "description": "What relief or order is sought"
        },
        "law_sections": {
            "present": any(word in prompt_lower for word in ["section", "under", "bns", "ipc", "crpc", "bnss", "act", "article"]),
            "description": "Applicable laws and sections"
        },
        "strategy_type": {
            "present": any(word in prompt_lower for word in ["analyze", "strategy", "opinion", "assessment", "research", "steps", "roadmap"]),
            "description": "Type of legal analysis or strategy needed"
        },
        "timeline": {
            "present": any(word in prompt_lower for word in ["dated", "date", "on", "since", "when", "year", "month"]),
            "description": "Key dates and timeline"
        }
    }

    # Calculate completeness score
    present_count = sum(1 for e in elements.values() if e["present"])
    total_elements = len(elements)
    completeness_score = round((present_count / total_elements) * 10)

    # Generate missing items list
    missing = [
        {"element": key, "description": val["description"]}
        for key, val in elements.items()
        if not val["present"]
    ]

    # Generate follow-up questions
    follow_up_questions = []
    if not elements["facts"]["present"]:
        follow_up_questions.append("What are the key facts of your case? Please describe chronologically.")
    if not elements["parties"]["present"]:
        follow_up_questions.append("Who are the parties involved? (Names and their roles)")
    if not elements["jurisdiction"]["present"]:
        follow_up_questions.append("Which court/forum will this be filed in? Which state?")
    if not elements["relief"]["present"]:
        follow_up_questions.append("What relief or order are you seeking?")
    if not elements["law_sections"]["present"]:
        follow_up_questions.append("Are there specific sections or laws involved?")
    if not elements["strategy_type"]["present"]:
        follow_up_questions.append("What type of legal analysis do you need? (Strategic assessment, procedural roadmap, etc.)")

    result = {
        "response_type": "prompt_analysis",
        "original_prompt": prompt,
        "completeness_score": completeness_score,
        "elements_present": present_count,
        "elements_total": total_elements,
        "status": "COMPLETE" if completeness_score >= 7 else "NEEDS INFO" if completeness_score >= 4 else "INCOMPLETE",
        "elements": {key: val["present"] for key, val in elements.items()},
        "missing_elements": missing,
        "follow_up_questions": follow_up_questions[:5]  # Max 5 questions
    }

    return json.dumps(result, indent=2)


def generate_improved_prompt(
    original_prompt: str,
    facts: str = None,
    parties: str = None,
    forum: str = None,
    relief: str = None,
    strategy_type: str = None
) -> str:
    """
    Generate an improved, structured prompt from fragments.

    Args:
        original_prompt: Original user prompt
        facts: Facts if provided separately
        parties: Parties if provided separately
        forum: Court/forum if provided separately
        relief: Relief sought if provided separately
        strategy_type: Strategy type if provided separately

    Returns:
        JSON with improved prompt following the prompt formula
    """
    import json

    # Start building improved prompt
    improved_parts = []

    # Strategy type
    if strategy_type:
        improved_parts.append(f"Provide a {strategy_type}")
    else:
        improved_parts.append("Provide a strategic assessment")

    # Forum
    if forum:
        improved_parts.append(f"for filing before {forum}")

    improved_parts.append("with the following details:")

    # Facts
    if facts:
        improved_parts.append(f"\n\nFACTS:\n{facts}")
    else:
        improved_parts.append("\n\nFACTS:\n[Please provide chronological facts of the case]")

    # Parties
    if parties:
        improved_parts.append(f"\n\nPARTIES:\n{parties}")
    else:
        improved_parts.append("\n\nPARTIES:\n[Petitioner/Applicant: ____]\n[Respondent/Opposite Party: ____]")

    # Relief
    if relief:
        improved_parts.append(f"\n\nRELIEF SOUGHT:\n{relief}")
    else:
        improved_parts.append("\n\nRELIEF SOUGHT:\n[Specify the relief/order being sought]")

    # Standard requirements
    improved_parts.append("\n\nREQUIREMENTS:")
    improved_parts.append("- Expert technical legal analysis")
    improved_parts.append("- Use BNS/BNSS/BSA (new codes) where applicable")
    improved_parts.append("- Identify strategic grounds and procedural steps")
    improved_parts.append("- Flag any citations that need verification")

    improved_prompt = " ".join(improved_parts[:3]) + "".join(improved_parts[3:])

    result = {
        "response_type": "improved_prompt",
        "original_prompt": original_prompt,
        "improved_prompt": improved_prompt,
        "prompt_formula": {
            "facts": facts or "[To be provided]",
            "jurisdiction_forum": forum or "[To be specified]",
            "relief_sought": relief or "[To be specified]",
            "output_format": strategy_type or "[Strategic Assessment]",
            "constraints": "Technical analysis, BNS/BNSS/BSA"
        }
    }

    return json.dumps(result, indent=2, ensure_ascii=False)


PromptCoachAgent = LlmAgent(
    name="PromptCoachAgent",
    model=LlmModel,
    description=(
        "Legal Prompt Coach Agent. Converts vague legal requests into precise, "
        "court-usable prompts. Use this agent when the user's request needs "
        "clarification or restructuring for better results."
    ),
    instruction=prompt_coach_instruction_provider,
    tools=[
        analyze_prompt_completeness,
        generate_improved_prompt,
        refine_prompt
    ]
)
