"""
Civil Litigation Lead Agent

Specialized agent for civil litigation matters in India.

Scope:
- Plaint / Written Statement (O.VII / O.VIII CPC)
- Temporary Injunctions (O.XXXIX R.1 & 2)
- Permanent Injunctions
- Civil Appeals
- Execution Applications
- Limitation Analysis
- Arbitration (S.8/9/11/34/36 A&C Act)
"""

from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext

try:
    from lexedge.config import LlmModel
except ImportError:
    from ...config import LlmModel

from lexedge.prompts.agent_prompts import get_civil_lead_prompt
from lexedge.shared_tools import (
    map_statute_sections,
    research_case_law,
    verify_citation,
    analyze_document,
    build_arguments,
    validate_output
)


def civil_instruction_provider(context: ReadonlyContext) -> str:
    """Dynamic instruction provider for civil litigation lead agent."""
    return get_civil_lead_prompt()





def check_limitation(
    cause_of_action: str,
    date_of_cause: str,
    suit_type: str
) -> str:
    """
    Check limitation period for civil matters.

    Args:
        cause_of_action: Description of cause of action
        date_of_cause: Date when cause of action arose (DD/MM/YYYY)
        suit_type: Type of suit (recovery, specific performance, injunction, etc.)

    Returns:
        JSON with limitation analysis
    """
    import json
    from datetime import datetime, timedelta

    # Limitation periods under Limitation Act, 1963
    LIMITATION_PERIODS = {
        "recovery_of_money": {"years": 3, "article": "Article 113"},
        "specific_performance": {"years": 3, "article": "Article 54"},
        "declaration": {"years": 3, "article": "Article 58"},
        "possession_of_immovable": {"years": 12, "article": "Article 64"},
        "injunction": {"years": 3, "article": "Article 113"},
        "contract": {"years": 3, "article": "Article 55"},
        "tort": {"years": 1, "article": "Article 72/73"},
        "appeal": {"years": 0, "days": 90, "article": "Article 116"},
        "review": {"years": 0, "days": 30, "article": "Article 124"}
    }

    suit_type_lower = suit_type.lower()
    limitation_info = None

    for key, info in LIMITATION_PERIODS.items():
        if key in suit_type_lower:
            limitation_info = info
            break

    if not limitation_info:
        limitation_info = {"years": 3, "article": "Article 113 (residuary)"}

    # Parse date
    try:
        cause_date = datetime.strptime(date_of_cause, "%d/%m/%Y")
    except:
        try:
            cause_date = datetime.strptime(date_of_cause, "%d-%m-%Y")
        except:
            cause_date = None

    result = {
        "response_type": "limitation_analysis",
        "cause_of_action": cause_of_action,
        "date_of_cause": date_of_cause,
        "suit_type": suit_type,
        "limitation_period": f"{limitation_info.get('years', 0)} years" + (f" {limitation_info.get('days', 0)} days" if limitation_info.get('days') else ""),
        "applicable_article": limitation_info["article"],
        "status": "Unknown"
    }

    if cause_date:
        years = limitation_info.get("years", 0)
        days = limitation_info.get("days", 0)
        expiry_date = cause_date + timedelta(days=years*365 + days)

        result["limitation_expires"] = expiry_date.strftime("%d/%m/%Y")

        if datetime.now() < expiry_date:
            result["status"] = "WITHIN LIMITATION"
            remaining = (expiry_date - datetime.now()).days
            result["days_remaining"] = remaining
            result["recommendation"] = f"File suit before {expiry_date.strftime('%d/%m/%Y')}. {remaining} days remaining."
        else:
            result["status"] = "POSSIBLY BARRED"
            exceeded = (datetime.now() - expiry_date).days
            result["days_exceeded"] = exceeded
            result["recommendation"] = "Limitation may have expired. Consider grounds for condonation of delay under Section 5 of Limitation Act."

    result["important_notes"] = [
        "Limitation starts from date cause of action accrues",
        "Acknowledgment in writing extends limitation (S.18)",
        "Part payment extends limitation for balance (S.19)",
        "Minority, insanity, etc. excluded under S.6",
        "Delay can be condoned for sufficient cause (S.5)"
    ]

    return json.dumps(result, indent=2, ensure_ascii=False)


CivilLitigationLeadAgent = LlmAgent(
    name="CivilLitigationLeadAgent",
    model=LlmModel,
    description=(
        "Civil Litigation Lead Agent for India. Handles suits, plaints, written statements, "
        "injunction applications, appeals, execution, and arbitration matters. "
        "Specializes in CPC procedures and limitation analysis."
    ),
    instruction=civil_instruction_provider,
    tools=[
        check_limitation,
        # Shared tools
        map_statute_sections,
        research_case_law,
        verify_citation,
        analyze_document,
        build_arguments,
        validate_output
    ]
)
