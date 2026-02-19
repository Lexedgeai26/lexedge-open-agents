"""
TOOL 6: Argument Builder Tool (Written + Oral + Rebuttal)

Purpose: Produce written submissions, oral outline, anticipated counter-arguments
and rebuttals.
"""

import json
import logging
from typing import List, Optional
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


def build_arguments(
    side: str,
    facts: List[str],
    issues: List[str],
    sections: List[str],
    cases: List[str] = None,
    argument_type: str = "written",
    tool_context: ToolContext = None
) -> str:
    """
    Construct legal arguments.

    Args:
        side: Party side (Petitioner/Respondent/Accused/Complainant/Plaintiff/Defendant)
        facts: List of relevant facts
        issues: Legal issues to address
        sections: Applicable statutory provisions
        cases: Supporting case laws (optional)
        argument_type: Type of arguments (written/oral/rebuttal/all)
        tool_context: ADK ToolContext

    Returns:
        JSON with written arguments, oral outline, counter-arguments, rebuttals
    """
    logger.info(f"[ARGUMENT_BUILDER] Building arguments for: {side}")

    result = {
        "response_type": "legal_arguments",
        "side": side,
        "issues_addressed": issues,
        "sections_relied": sections,
        "cases_relied": cases or [],
        "written_arguments": [],
        "oral_submissions_outline": [],
        "anticipated_counter_arguments": [],
        "rebuttals": [],
        "disclaimer": "These arguments are AI-assisted drafts for professional review and customization."
    }

    # Determine perspective based on side
    is_petitioner_side = side.lower() in ["petitioner", "applicant", "plaintiff", "accused", "appellant"]

    # Build written arguments
    if argument_type in ["written", "all"]:
        result["written_arguments"] = build_written_arguments(
            side=side,
            facts=facts,
            issues=issues,
            sections=sections,
            cases=cases or [],
            is_petitioner_side=is_petitioner_side
        )

    # Build oral submissions outline
    if argument_type in ["oral", "all"]:
        result["oral_submissions_outline"] = build_oral_outline(
            side=side,
            facts=facts,
            issues=issues,
            sections=sections,
            cases=cases or [],
            is_petitioner_side=is_petitioner_side
        )

    # Anticipate counter-arguments
    if argument_type in ["rebuttal", "all"]:
        result["anticipated_counter_arguments"] = anticipate_counter_arguments(
            side=side,
            facts=facts,
            issues=issues,
            is_petitioner_side=is_petitioner_side
        )

        result["rebuttals"] = build_rebuttals(
            counter_arguments=result["anticipated_counter_arguments"],
            sections=sections,
            cases=cases or []
        )

    return json.dumps(result, indent=2, ensure_ascii=False)


def build_written_arguments(
    side: str,
    facts: List[str],
    issues: List[str],
    sections: List[str],
    cases: List[str],
    is_petitioner_side: bool
) -> List[dict]:
    """Build structured written arguments."""
    arguments = []

    # Opening/Preliminary Submissions
    arguments.append({
        "heading": "PRELIMINARY SUBMISSIONS",
        "content": f"""
1. The present {side} respectfully submits the following arguments in support of the case.

2. The {side} seeks to establish that {"the case is made out for grant of relief" if is_petitioner_side else "the case of the opposite party is without merit"}.

3. Brief Facts:
{chr(10).join([f"   {chr(97+i)}) {fact}" for i, fact in enumerate(facts[:5])])}
"""
    })

    # Legal Framework
    arguments.append({
        "heading": "LEGAL FRAMEWORK",
        "content": f"""
4. The relevant statutory provisions are:
{chr(10).join([f"   - {section}" for section in sections])}

5. The applicable legal principles from decided cases are:
{chr(10).join([f"   - {case}" for case in cases[:5]]) if cases else "   [To be supplemented with specific case laws]"}
"""
    })

    # Issue-wise Arguments
    for i, issue in enumerate(issues):
        if is_petitioner_side:
            argument_content = f"""
{6+i}. ISSUE: {issue}

   SUBMISSION: It is submitted that the {side} has established/is entitled to relief on this issue because:

   a) The factual matrix clearly supports the {side}'s case.

   b) The legal provisions under {sections[0] if sections else '[applicable section]'} are squarely applicable.

   c) The settled legal position supports the {side}'s contention.

   d) The principles laid down in {cases[0] if cases else 'relevant precedents'} are directly applicable.
"""
        else:
            argument_content = f"""
{6+i}. ISSUE: {issue}

   SUBMISSION: It is submitted that the case of the opposite party fails on this issue because:

   a) The factual allegations are not supported by evidence.

   b) The legal provisions relied upon are not applicable to the facts.

   c) The opposite party has failed to satisfy the essential ingredients.

   d) The case laws relied upon are distinguishable on facts.
"""
        arguments.append({
            "heading": f"ISSUE {i+1}",
            "issue": issue,
            "content": argument_content
        })

    # Conclusion
    arguments.append({
        "heading": "CONCLUSION",
        "content": f"""
{6+len(issues)}. In view of the above submissions, it is respectfully prayed that this Hon'ble Court may be pleased to {"allow the case of the {side}" if is_petitioner_side else "dismiss the case of the opposite party"} and pass orders accordingly.

   The {side} relies upon the documents filed on record and reserves the right to make further submissions.
"""
    })

    return arguments


def build_oral_outline(
    side: str,
    facts: List[str],
    issues: List[str],
    sections: List[str],
    cases: List[str],
    is_petitioner_side: bool
) -> List[dict]:
    """Build oral submissions outline."""
    outline = []

    # Opening
    outline.append({
        "phase": "OPENING (2-3 minutes)",
        "points": [
            f"My Lord, I appear for the {side}.",
            f"This is a matter concerning {issues[0] if issues else '[brief description]'}.",
            "The core question before this Hon'ble Court is...",
            "I will address the factual matrix briefly and then deal with the legal submissions."
        ]
    })

    # Facts Summary
    outline.append({
        "phase": "FACTS SUMMARY (3-5 minutes)",
        "points": [
            "The brief facts are as follows:",
            *[f"• {fact[:100]}..." for fact in facts[:4]],
            "These facts are supported by documents at Annexure..."
        ]
    })

    # Legal Submissions
    case_points = [f"• {case}" for case in cases[:3]] if cases else ["• [Cite relevant case laws]"]
    outline.append({
        "phase": "LEGAL SUBMISSIONS (Main Arguments)",
        "points": [
            f"The applicable provisions are {', '.join(sections[:3])}",
            "I rely on the following precedents:",
            *case_points,
            "The ratio of these cases squarely applies to the present facts."
        ]
    })

    # Issue-wise Points
    for i, issue in enumerate(issues[:3]):
        outline.append({
            "phase": f"ISSUE {i+1}: {issue[:50]}...",
            "points": [
                f"On this issue, my submission is that...",
                f"This is established by the documents at...",
                f"The legal position is clear from...",
                f"Therefore, this issue must be decided in favour of the {side}."
            ]
        })

    # Closing
    outline.append({
        "phase": "CLOSING",
        "points": [
            "In summary, the case of the opposite party is...",
            f"The {side} has made out a clear case for relief.",
            "I pray that this Hon'ble Court may be pleased to...",
            "I rest my submissions, subject to reply."
        ]
    })

    return outline


def anticipate_counter_arguments(
    side: str,
    facts: List[str],
    issues: List[str],
    is_petitioner_side: bool
) -> List[dict]:
    """Anticipate possible counter-arguments."""
    counter_arguments = []

    if is_petitioner_side:
        # Common counter-arguments against petitioner
        counter_arguments = [
            {
                "point": "MAINTAINABILITY",
                "argument": "The petition/application is not maintainable due to availability of alternative remedy.",
                "strength": "Medium"
            },
            {
                "point": "DELAY/LACHES",
                "argument": "There is unexplained delay in approaching the court.",
                "strength": "Medium"
            },
            {
                "point": "SUPPRESSION",
                "argument": "Material facts have been suppressed by the petitioner.",
                "strength": "High"
            },
            {
                "point": "DISPUTED FACTS",
                "argument": "Disputed questions of fact cannot be decided in summary proceedings.",
                "strength": "Medium"
            },
            {
                "point": "CLEAN HANDS",
                "argument": "The petitioner does not come with clean hands.",
                "strength": "Low"
            }
        ]

        # Add issue-specific counters
        for issue in issues[:2]:
            issue_lower = issue.lower()
            if "bail" in issue_lower:
                counter_arguments.append({
                    "point": "FLIGHT RISK",
                    "argument": "The accused is a flight risk and may abscond if released on bail.",
                    "strength": "High"
                })
                counter_arguments.append({
                    "point": "TAMPERING",
                    "argument": "The accused may tamper with evidence or influence witnesses.",
                    "strength": "High"
                })
            if "quash" in issue_lower:
                counter_arguments.append({
                    "point": "PRIMA FACIE CASE",
                    "argument": "Prima facie case is made out against the accused.",
                    "strength": "High"
                })
    else:
        # Counter-arguments against respondent/complainant
        counter_arguments = [
            {
                "point": "LACK OF EVIDENCE",
                "argument": "The allegations are not supported by any credible evidence.",
                "strength": "High"
            },
            {
                "point": "MOTIVE",
                "argument": "The complaint is motivated by malice/personal vendetta.",
                "strength": "Medium"
            },
            {
                "point": "CIVIL NATURE",
                "argument": "The dispute is essentially civil in nature given criminal colour.",
                "strength": "High"
            },
            {
                "point": "DELAY IN FIR",
                "argument": "There is inordinate delay in lodging the FIR which is not explained.",
                "strength": "Medium"
            }
        ]

    return counter_arguments


def build_rebuttals(
    counter_arguments: List[dict],
    sections: List[str],
    cases: List[str]
) -> List[dict]:
    """Build rebuttals to anticipated counter-arguments."""
    rebuttals = []

    rebuttal_templates = {
        "MAINTAINABILITY": "The present remedy is the most appropriate and efficacious remedy. Alternative remedy is not a bar in cases of violation of fundamental rights or where irreparable injury would be caused.",
        "DELAY/LACHES": "The delay, if any, is satisfactorily explained. The cause of action is continuing in nature. In any event, delay alone cannot be a ground to deny relief on merits.",
        "SUPPRESSION": "There is no suppression of material facts. All relevant facts have been placed before this Hon'ble Court. The allegations of suppression are vague and without particulars.",
        "DISPUTED FACTS": "The facts are not in dispute. Even on disputed facts, this Hon'ble Court can decide the matter based on admitted facts and documents.",
        "CLEAN HANDS": "The petitioner comes with absolutely clean hands. The allegations of unclean hands are afterthoughts without any basis.",
        "FLIGHT RISK": "The accused has deep roots in society and has no intention to abscond. The accused is ready to furnish surety and comply with conditions.",
        "TAMPERING": "Investigation is complete. There is no possibility of tampering with evidence. Custodial interrogation is not required.",
        "PRIMA FACIE CASE": "Even on prima facie reading of the FIR, no offence is made out. The allegations do not satisfy essential ingredients of the alleged offence.",
        "LACK OF EVIDENCE": "The evidence on record clearly establishes the case. The oral and documentary evidence is consistent and corroborates the allegations.",
        "MOTIVE": "The complaint is not motivated. It is based on genuine grievance. The opposite party is trying to deflect from the real issues.",
        "CIVIL NATURE": "The matter involves criminal liability. The ingredients of the offence are clearly made out. Civil remedy does not bar criminal prosecution.",
        "DELAY IN FIR": "The delay in lodging FIR is satisfactorily explained. The complainant was under threat/exploring settlement/was not aware of legal remedies."
    }

    for counter in counter_arguments:
        point = counter.get("point", "")
        rebuttal_text = rebuttal_templates.get(point, "This contention is misconceived and without merit. The facts and law are clearly in favour of the petitioner.")

        if cases:
            rebuttal_text += f" Reliance is placed on {cases[0]}."

        rebuttals.append({
            "counter_argument": counter.get("argument", ""),
            "rebuttal": rebuttal_text,
            "supporting_section": sections[0] if sections else None
        })

    return rebuttals
