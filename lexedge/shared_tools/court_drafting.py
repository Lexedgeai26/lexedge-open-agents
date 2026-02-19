"""
TOOL 4: Court-Ready Drafting Tool (Drafting & Formatting)

Purpose: Generate court-style documents with correct headings, prayers,
verification, annexures placeholders.

Supports Indian court formats for:
- Anticipatory Bail Application
- Regular Bail Application
- Quashing Petition (S.482/528)
- Writ Petition (Art. 226/32)
- Plaint / Written Statement
- Injunction Application
- Legal Notice
- Reply to Notice
- Appeal Memo
- SLP Synopsis
"""

import json
import logging
from typing import List, Optional
from datetime import datetime
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)


# Document templates with Indian court formatting
DOCUMENT_TEMPLATES = {
    "anticipatory_bail": {
        "title": "APPLICATION FOR ANTICIPATORY BAIL",
        "under_section": "Section 482 of Bharatiya Nagarik Suraksha Sanhita, 2023 (formerly Section 438 Cr.P.C.)",
        "structure": [
            "cause_title",
            "index",
            "synopsis_list_of_dates",
            "application",
            "grounds",
            "prayer",
            "verification",
            "annexures"
        ]
    },
    "regular_bail": {
        "title": "APPLICATION FOR BAIL",
        "under_section": "Section 483 of Bharatiya Nagarik Suraksha Sanhita, 2023 (formerly Section 439 Cr.P.C.)",
        "structure": [
            "cause_title",
            "index",
            "application",
            "brief_facts",
            "grounds",
            "prayer",
            "verification"
        ]
    },
    "quashing_petition": {
        "title": "PETITION UNDER SECTION 528 BNSS",
        "under_section": "Section 528 of Bharatiya Nagarik Suraksha Sanhita, 2023 (formerly Section 482 Cr.P.C.)",
        "structure": [
            "cause_title",
            "index",
            "synopsis_list_of_dates",
            "petition",
            "grounds",
            "prayer",
            "verification",
            "annexures"
        ]
    },
    "writ_petition": {
        "title": "WRIT PETITION (CIVIL/CRIMINAL)",
        "under_section": "Article 226 of the Constitution of India",
        "structure": [
            "cause_title",
            "index",
            "synopsis_list_of_dates",
            "petition",
            "questions_of_law",
            "grounds",
            "prayer",
            "verification",
            "annexures"
        ]
    },
    "plaint": {
        "title": "PLAINT",
        "under_section": "Order VII of the Code of Civil Procedure, 1908",
        "structure": [
            "cause_title",
            "jurisdiction",
            "parties",
            "facts",
            "cause_of_action",
            "limitation",
            "relief",
            "verification"
        ]
    },
    "written_statement": {
        "title": "WRITTEN STATEMENT",
        "under_section": "Order VIII of the Code of Civil Procedure, 1908",
        "structure": [
            "cause_title",
            "preliminary_objections",
            "para_wise_reply",
            "additional_pleas",
            "prayer",
            "verification"
        ]
    },
    "injunction_application": {
        "title": "APPLICATION FOR TEMPORARY INJUNCTION",
        "under_section": "Order XXXIX Rules 1 & 2 of CPC read with Section 151 CPC",
        "structure": [
            "cause_title",
            "application",
            "facts",
            "prima_facie_case",
            "balance_of_convenience",
            "irreparable_injury",
            "prayer",
            "verification"
        ]
    },
    "legal_notice": {
        "title": "LEGAL NOTICE",
        "under_section": "Section 80 CPC / General",
        "structure": [
            "header",
            "addressee",
            "subject",
            "facts",
            "legal_position",
            "demand",
            "consequences",
            "signature"
        ]
    },
    "criminal_appeal": {
        "title": "CRIMINAL APPEAL",
        "under_section": "Section 419 BNSS (formerly Section 374 Cr.P.C.)",
        "structure": [
            "cause_title",
            "index",
            "memo_of_appeal",
            "grounds",
            "prayer",
            "verification"
        ]
    }
}


def draft_legal_document(
    document_type: str,
    court: str,
    parties: List[str],
    facts: List[str],
    relief: str,
    sections: List[str],
    cases: List[str] = None,
    tool_context: ToolContext = None
) -> str:
    """
    Generate court-ready legal documents.

    Args:
        document_type: Type of document (anticipatory_bail, quashing_petition, etc.)
        court: Court/Forum name (e.g., "Sessions Court, Pune", "High Court of Bombay")
        parties: List of parties [petitioner/applicant, respondent/opposite party]
        facts: Chronological list of facts
        relief: Relief sought
        sections: List of applicable sections (e.g., ["BNS 318", "BNSS 482"])
        cases: List of supporting case laws (optional)
        tool_context: ADK ToolContext

    Returns:
        JSON with fully formatted legal draft and placeholders
    """
    logger.info(f"[COURT_DRAFTING] Drafting: {document_type} for {court}")

    doc_type_key = document_type.lower().replace(" ", "_").replace("-", "_")

    if doc_type_key not in DOCUMENT_TEMPLATES:
        # Try to find closest match
        for key in DOCUMENT_TEMPLATES.keys():
            if key in doc_type_key or doc_type_key in key:
                doc_type_key = key
                break
        else:
            doc_type_key = "anticipatory_bail"  # Default

    template = DOCUMENT_TEMPLATES[doc_type_key]
    current_date = datetime.now().strftime("%d.%m.%Y")

    # Build the document
    draft_content = generate_document_content(
        template=template,
        doc_type=doc_type_key,
        court=court,
        parties=parties,
        facts=facts,
        relief=relief,
        sections=sections,
        cases=cases or [],
        current_date=current_date
    )

    result = {
        "response_type": "legal_draft",
        "document_type": template["title"],
        "under_section": template["under_section"],
        "court": court,
        "date_generated": current_date,
        "draft": draft_content,
        "placeholders_used": [
            "[PETITIONER NAME]",
            "[RESPONDENT NAME]",
            "[FIR NUMBER]",
            "[POLICE STATION]",
            "[DATE]",
            "[PLACE]",
            "[ADVOCATE NAME]",
            "[ENROLLMENT NUMBER]"
        ],
        "filing_checklist": generate_filing_checklist(doc_type_key),
        "disclaimer": "This is an AI-generated draft for professional review. Verify all facts, sections, and citations before filing."
    }

    return json.dumps(result, indent=2, ensure_ascii=False)


def generate_document_content(
    template: dict,
    doc_type: str,
    court: str,
    parties: List[str],
    facts: List[str],
    relief: str,
    sections: List[str],
    cases: List[str],
    current_date: str
) -> str:
    """Generate the actual document content."""

    petitioner = parties[0] if parties else "[PETITIONER NAME]"
    respondent = parties[1] if len(parties) > 1 else "State / [RESPONDENT NAME]"

    # Build document based on type
    if doc_type == "anticipatory_bail":
        return f"""
IN THE COURT OF {court.upper()}

{template['title']}
UNDER {template['under_section']}

IN THE MATTER OF:

{petitioner}
... Applicant/Accused

VERSUS

{respondent}
... Respondent/State

FIR No.: [FIR NUMBER]
Police Station: [POLICE STATION]
Under Sections: {', '.join(sections)}

INDEX

S.No. | Particulars                          | Page No.
------|--------------------------------------|----------
1.    | Application for Anticipatory Bail   |
2.    | Synopsis and List of Dates          |
3.    | Grounds                              |
4.    | Annexure A - [Document]              |

SYNOPSIS AND LIST OF DATES

Date        | Event
------------|--------------------------------------------------
{chr(10).join([f"[DATE]     | {fact}" for fact in facts[:5]])}

APPLICATION FOR ANTICIPATORY BAIL

MOST RESPECTFULLY SHOWETH:

1. That the Applicant is filing the present application seeking anticipatory bail in connection with FIR No. [FIR NUMBER] registered at Police Station [POLICE STATION] under Sections {', '.join(sections)}.

2. BRIEF FACTS:
{chr(10).join([f"   {i+1}. {fact}" for i, fact in enumerate(facts)])}

3. That the Applicant apprehends arrest in connection with the aforesaid FIR and seeks protection of anticipatory bail.

4. That no recovery is to be effected from the Applicant and the Applicant's custodial interrogation is not required.

5. That the Applicant is a respectable citizen with deep roots in society and there is no likelihood of the Applicant fleeing from justice or tampering with evidence.

GROUNDS

A. That the allegations in the FIR are false and frivolous and have been lodged with ulterior motives.

B. That the Applicant is innocent and has been falsely implicated in the present case.

C. That no useful purpose would be served by sending the Applicant to judicial custody.

D. That the Applicant is ready and willing to join investigation and cooperate with the investigating agency.

E. That the Applicant has no criminal antecedents.

F. {f"That reliance is placed on: {', '.join(cases)}" if cases else "That the Applicant relies upon the principles laid down in Sushila Aggarwal v. State (NCT of Delhi) (2020) 5 SCC 1."}

PRAYER

In view of the facts and circumstances stated above, it is most respectfully prayed that this Hon'ble Court may be pleased to:

a) Grant anticipatory bail to the Applicant in connection with FIR No. [FIR NUMBER], Police Station [POLICE STATION];

b) Direct that in the event of arrest, the Applicant be released on bail on such terms and conditions as this Hon'ble Court may deem fit and proper;

c) Pass any other order as this Hon'ble Court may deem fit in the facts and circumstances of the case.

AND FOR THIS ACT OF KINDNESS, THE APPLICANT SHALL EVER PRAY.

Place: [PLACE]
Date: {current_date}

                                        [PETITIONER NAME]
                                        Through Counsel

                                        [ADVOCATE NAME]
                                        Advocate
                                        Enrollment No.: [ENROLLMENT NUMBER]

VERIFICATION

I, {petitioner}, the Applicant above-named, do hereby verify that the contents of the above application are true and correct to the best of my knowledge and belief. No part of it is false and nothing material has been concealed therefrom.

Verified at [PLACE] on this {current_date}.

                                        [PETITIONER NAME]
                                        Applicant
"""

    elif doc_type == "quashing_petition":
        return f"""
IN THE HIGH COURT OF [STATE]
AT [CITY]

CRIMINAL MISCELLANEOUS PETITION NO. _____ OF {datetime.now().year}

{template['title']}
UNDER {template['under_section']}

IN THE MATTER OF:

{petitioner}
... Petitioner

VERSUS

{respondent}
... Respondent(s)

FIR No.: [FIR NUMBER]
Police Station: [POLICE STATION]
Under Sections: {', '.join(sections)}

INDEX

S.No. | Particulars                          | Page No.
------|--------------------------------------|----------
1.    | Petition under Section 528 BNSS     |
2.    | Synopsis and List of Dates          |
3.    | Grounds                              |
4.    | Annexure A - Copy of FIR             |
5.    | Annexure B - [Other Documents]       |

SYNOPSIS AND LIST OF DATES

Date        | Event
------------|--------------------------------------------------
{chr(10).join([f"[DATE]     | {fact}" for fact in facts[:5]])}

PETITION UNDER SECTION 528 BNSS (FORMERLY SECTION 482 Cr.P.C.)

TO,
THE HON'BLE CHIEF JUSTICE AND HIS COMPANION JUDGES OF THE HIGH COURT OF [STATE]

THE HUMBLE PETITION OF THE PETITIONER ABOVE-NAMED

MOST RESPECTFULLY SHOWETH:

1. That the Petitioner is filing the present petition seeking quashing of FIR No. [FIR NUMBER] dated [DATE] registered at Police Station [POLICE STATION] under Sections {', '.join(sections)}.

2. BRIEF FACTS:
{chr(10).join([f"   {i+1}. {fact}" for i, fact in enumerate(facts)])}

3. That the present FIR has been lodged with malafide intention and is an abuse of the process of law.

4. That the dispute between the parties is purely civil in nature and criminal law has been set in motion to harass the Petitioner.

5. That even if the entire allegations in the FIR are taken at their face value, no offence is made out against the Petitioner.

GROUNDS

A. NO OFFENCE DISCLOSED: That the FIR does not disclose commission of any cognizable offence against the Petitioner. The allegations are vague and do not satisfy the essential ingredients of the sections invoked.

B. CIVIL DISPUTE: That the dispute is essentially civil in nature and has been given a criminal colour to harass and intimidate the Petitioner. Reliance is placed on State of Haryana v. Bhajan Lal, 1992 Supp (1) SCC 335.

C. MALAFIDE AND ULTERIOR MOTIVE: That the FIR has been lodged with malafide intention and ulterior motive to settle personal scores.

D. ABUSE OF PROCESS: That continuation of the criminal proceedings would amount to abuse of the process of law and would cause grave injustice to the Petitioner.

E. {f"That reliance is placed on: {', '.join(cases)}" if cases else "That the Petitioner relies upon the principles laid down in Bhajan Lal, Amit Kapoor, and other relevant precedents."}

PRAYER

In view of the facts and circumstances stated above, it is most respectfully prayed that this Hon'ble Court may be pleased to:

a) Quash FIR No. [FIR NUMBER] dated [DATE] registered at Police Station [POLICE STATION] under Sections {', '.join(sections)};

b) Stay further investigation/proceedings in the matter during pendency of this petition;

c) Pass any other order as this Hon'ble Court may deem fit in the interests of justice.

AND FOR THIS ACT OF KINDNESS, THE PETITIONER SHALL EVER PRAY.

Place: [PLACE]
Date: {current_date}

                                        [PETITIONER NAME]
                                        Through Counsel

                                        [ADVOCATE NAME]
                                        Advocate
                                        Enrollment No.: [ENROLLMENT NUMBER]

VERIFICATION

I, {petitioner}, the Petitioner above-named, do hereby solemnly affirm and state that the contents of paras 1 to [X] are true and correct to my knowledge and the contents of paras [Y] are based on legal advice which I believe to be true. No part of it is false and nothing material has been concealed therefrom.

Verified at [PLACE] on this {current_date}.

                                        [PETITIONER NAME]
                                        Petitioner
"""

    elif doc_type == "legal_notice":
        return f"""
LEGAL NOTICE

Date: {current_date}

To,
{respondent}
[COMPLETE ADDRESS]

Subject: Legal Notice for [SUBJECT MATTER]

Under Instructions from and on behalf of my client:
{petitioner}
[CLIENT ADDRESS]

Dear Sir/Madam,

Under instructions from and on behalf of my client, {petitioner}, I hereby serve upon you the following Legal Notice:

FACTS OF THE MATTER:

{chr(10).join([f"{i+1}. {fact}" for i, fact in enumerate(facts)])}

LEGAL POSITION:

{chr(10).join([f"- Under {section}" for section in sections])}

DEMAND:

In view of the above, my client demands that you:

{relief}

CONSEQUENCES:

Please note that if you fail to comply with the above demand within 15 days from the receipt of this notice, my client shall be constrained to initiate appropriate legal proceedings against you, civil and/or criminal, at your risk, cost and consequences.

Please treat this notice as final and act accordingly.

                                        [ADVOCATE NAME]
                                        Advocate for {petitioner}
                                        [OFFICE ADDRESS]
                                        [CONTACT DETAILS]
                                        Enrollment No.: [ENROLLMENT NUMBER]
"""

    elif doc_type == "injunction_application":
        return f"""
IN THE COURT OF {court.upper()}

I.A. NO. _____ OF {datetime.now().year}
IN
SUIT NO. _____ OF {datetime.now().year}

{template['title']}
UNDER {template['under_section']}

{petitioner}
... Plaintiff/Applicant

VERSUS

{respondent}
... Defendant/Respondent

APPLICATION FOR TEMPORARY INJUNCTION

MOST RESPECTFULLY SHOWETH:

1. That the above-named Applicant/Plaintiff has filed the present suit seeking [MAIN RELIEF] against the Defendant.

2. BRIEF FACTS:
{chr(10).join([f"   {i+1}. {fact}" for i, fact in enumerate(facts)])}

3. PRIMA FACIE CASE:
   That the Applicant has a strong prima facie case in their favour. The suit property belongs to the Applicant and the Defendant has no right, title or interest in the same.

4. BALANCE OF CONVENIENCE:
   That the balance of convenience lies in favour of the Applicant. If the injunction is not granted, the Applicant will suffer irreparable loss, whereas the Defendant will not suffer any prejudice if the injunction is granted.

5. IRREPARABLE INJURY:
   That if the temporary injunction is not granted, the Applicant will suffer irreparable injury which cannot be compensated in terms of money.

6. That the Applicant has not approached any other court for similar relief.

PRAYER

In view of the facts and circumstances stated above, it is most respectfully prayed that this Hon'ble Court may be pleased to:

a) Grant temporary injunction restraining the Defendant, their agents, servants, or anyone claiming through them from [SPECIFIC RESTRAINT];

b) Grant ex-parte ad-interim injunction in terms of prayer (a) above;

c) Pass any other order as this Hon'ble Court may deem fit and proper.

Place: [PLACE]
Date: {current_date}

                                        [PLAINTIFF NAME]
                                        Through Counsel

                                        [ADVOCATE NAME]
                                        Advocate
                                        Enrollment No.: [ENROLLMENT NUMBER]
"""

    else:
        # Generic template for other document types
        return f"""
IN THE COURT OF {court.upper()}

{template['title']}
UNDER {template['under_section']}

{petitioner}
... Applicant/Petitioner/Plaintiff

VERSUS

{respondent}
... Respondent/Defendant

PETITION/APPLICATION

MOST RESPECTFULLY SHOWETH:

1. That the Applicant is filing the present application/petition for the following reliefs.

2. FACTS:
{chr(10).join([f"   {i+1}. {fact}" for i, fact in enumerate(facts)])}

3. APPLICABLE PROVISIONS:
   {', '.join(sections)}

GROUNDS:

A. [GROUND 1]
B. [GROUND 2]
C. [GROUND 3]

{f"CASE LAW RELIED UPON: {', '.join(cases)}" if cases else ""}

PRAYER

{relief}

Place: [PLACE]
Date: {current_date}

                                        [APPLICANT NAME]
                                        Through Counsel

                                        [ADVOCATE NAME]
                                        Advocate
"""


def generate_filing_checklist(doc_type: str) -> List[str]:
    """Generate filing checklist based on document type."""
    common_items = [
        "Original + required number of copies",
        "Court fee stamps",
        "Index with page numbers",
        "Vakalatnama / Memo of Appearance",
        "Identity proof of Petitioner/Applicant"
    ]

    specific_items = {
        "anticipatory_bail": [
            "Copy of FIR (if available) or complaint",
            "Proof of apprehension of arrest",
            "Previous bail orders (if any)",
            "Character certificate / service records",
            "Proof of residence"
        ],
        "quashing_petition": [
            "Certified copy of FIR",
            "Copy of chargesheet (if filed)",
            "Documents showing civil nature of dispute",
            "Settlement deed (if any)",
            "Previous orders in the matter"
        ],
        "injunction_application": [
            "Title documents",
            "Plaint (if filed separately)",
            "Site plan / property documents",
            "Photographs (if relevant)",
            "Valuation certificate"
        ],
        "legal_notice": [
            "Send by Registered Post AD",
            "Keep proof of dispatch",
            "Maintain copy with postal receipt",
            "Wait for 15-30 days for response"
        ]
    }

    return common_items + specific_items.get(doc_type, [])
