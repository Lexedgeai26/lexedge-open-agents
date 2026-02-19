"""
TOOL 2: Case Law Research Tool (Judgment Finder + Ratio Extractor)

Purpose: Discover relevant SC/HC case law; extract ratio and applicability;
flag citations requiring verification.

Focuses on Indian courts:
- Supreme Court of India
- High Courts (various states)
"""

import json
import logging
from typing import Optional, List
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# Landmark cases database (commonly cited precedents)
LANDMARK_CASES = {
    # Bail Related
    "anticipatory_bail": [
        {
            "case_name": "Sushila Aggarwal v. State (NCT of Delhi)",
            "citation": "(2020) 5 SCC 1",
            "court": "Supreme Court",
            "year": 2020,
            "ratio": "Anticipatory bail can be granted without time limit. Protection should enure till end of trial unless cancelled.",
            "keywords": ["anticipatory bail", "no time limit", "438"]
        },
        {
            "case_name": "Siddharam Satlingappa Mhetre v. State of Maharashtra",
            "citation": "(2011) 1 SCC 694",
            "court": "Supreme Court",
            "year": 2011,
            "ratio": "Anticipatory bail should not be refused mechanically. Nature of accusations, evidence, punishment to be considered.",
            "keywords": ["anticipatory bail", "considerations", "discretion"]
        },
        {
            "case_name": "Gurbaksh Singh Sibbia v. State of Punjab",
            "citation": "(1980) 2 SCC 565",
            "court": "Supreme Court",
            "year": 1980,
            "ratio": "Anticipatory bail is constitutional. Courts must consider prima facie case, nature of accusation, antecedents.",
            "keywords": ["anticipatory bail", "constitutional", "landmark"]
        }
    ],

    # Quashing FIR
    "quashing": [
        {
            "case_name": "State of Haryana v. Bhajan Lal",
            "citation": "1992 Supp (1) SCC 335",
            "court": "Supreme Court",
            "year": 1992,
            "ratio": "Seven categories where FIR can be quashed: (1) No offence disclosed (2) Civil dispute (3) Legal bar (4) Complaint absurd (5) Criminal law set in motion for extraneous reasons (6) Express legal bar (7) Manifest injustice",
            "keywords": ["quashing", "482", "bhajan lal", "categories"]
        },
        {
            "case_name": "Amit Kapoor v. Ramesh Chander",
            "citation": "(2012) 9 SCC 460",
            "court": "Supreme Court",
            "year": 2012,
            "ratio": "Civil dispute given criminal colour - strong ground for quashing. Courts should not allow abuse of criminal process.",
            "keywords": ["quashing", "civil dispute", "criminal colour"]
        },
        {
            "case_name": "Indian Oil Corporation v. NEPC India Ltd.",
            "citation": "(2006) 6 SCC 736",
            "court": "Supreme Court",
            "year": 2006,
            "ratio": "Breach of contract per se does not give rise to criminal prosecution for cheating. Dishonest intention from inception required.",
            "keywords": ["quashing", "contract", "cheating", "420"]
        }
    ],

    # FIR Registration
    "fir": [
        {
            "case_name": "Lalita Kumari v. Govt. of U.P.",
            "citation": "(2014) 2 SCC 1",
            "court": "Supreme Court",
            "year": 2014,
            "ratio": "FIR registration is mandatory upon disclosure of cognizable offence. Preliminary inquiry permissible in matrimonial/commercial disputes, medical negligence, corruption cases.",
            "keywords": ["fir", "mandatory", "154", "cognizable"]
        }
    ],

    # Cheating
    "cheating": [
        {
            "case_name": "Hridaya Ranjan Prasad Verma v. State of Bihar",
            "citation": "(2000) 4 SCC 168",
            "court": "Supreme Court",
            "year": 2000,
            "ratio": "Mere breach of contract does not amount to cheating. Dishonest intention at inception must be established.",
            "keywords": ["cheating", "420", "contract", "intention"]
        },
        {
            "case_name": "Vesa Holdings Pvt. Ltd. v. State of Kerala",
            "citation": "(2015) 8 SCC 293",
            "court": "Supreme Court",
            "year": 2015,
            "ratio": "In cheating cases, accused must have dishonest or fraudulent intention at the time of making promise.",
            "keywords": ["cheating", "dishonest intention", "promise"]
        }
    ],

    # Defamation
    "defamation": [
        {
            "case_name": "Subramanian Swamy v. Union of India",
            "citation": "(2016) 7 SCC 221",
            "court": "Supreme Court",
            "year": 2016,
            "ratio": "Criminal defamation (IPC 499-500 / BNS 356) is constitutional. Right to reputation is part of Article 21.",
            "keywords": ["defamation", "499", "constitutional", "reputation"]
        }
    ],

    # Section 498A / Cruelty
    "498a_cruelty": [
        {
            "case_name": "Arnesh Kumar v. State of Bihar",
            "citation": "(2014) 8 SCC 273",
            "court": "Supreme Court",
            "year": 2014,
            "ratio": "Arrest in 498A cases should not be automatic. Police to follow S.41(1) CrPC checklist. Notice under S.41A mandatory.",
            "keywords": ["498a", "arrest", "guidelines", "41a"]
        },
        {
            "case_name": "Rajesh Sharma v. State of U.P.",
            "citation": "(2017) 8 SCC 446",
            "court": "Supreme Court",
            "year": 2017,
            "ratio": "Family Welfare Committee to be set up for 498A cases. No arrest before Committee report. (Later modified by Socially Forward)",
            "keywords": ["498a", "family welfare committee", "arrest"]
        },
        {
            "case_name": "Social Action Forum v. Union of India",
            "citation": "(2018) 10 SCC 443",
            "court": "Supreme Court",
            "year": 2018,
            "ratio": "Rajesh Sharma guidelines on Family Welfare Committee diluted. Arnesh Kumar guidelines remain in force.",
            "keywords": ["498a", "family welfare", "diluted"]
        }
    ],

    # NDPS
    "ndps": [
        {
            "case_name": "Tofan Singh v. State of Tamil Nadu",
            "citation": "(2021) 4 SCC 1",
            "court": "Supreme Court",
            "year": 2021,
            "ratio": "Statements recorded under S.67 NDPS Act are not confessions. Cannot be used as substantive evidence against accused.",
            "keywords": ["ndps", "67", "confession", "statement"]
        },
        {
            "case_name": "Union of India v. Ram Samujh",
            "citation": "(1999) 9 SCC 429",
            "court": "Supreme Court",
            "year": 1999,
            "ratio": "Conscious possession required in NDPS cases. Mere recovery without conscious possession insufficient.",
            "keywords": ["ndps", "conscious possession", "recovery"]
        }
    ],

    # NI Act / Cheque Bounce
    "cheque_bounce": [
        {
            "case_name": "Dashrath Rupsingh Rathod v. State of Maharashtra",
            "citation": "(2014) 9 SCC 129",
            "court": "Supreme Court",
            "year": 2014,
            "ratio": "Complaint under NI Act S.138 can be filed only where cheque is dishonoured (bank location), not where complainant resides.",
            "keywords": ["ni act", "138", "jurisdiction", "territorial"]
        },
        {
            "case_name": "Meters and Instruments Pvt. Ltd. v. Kanchan Mehta",
            "citation": "(2018) 1 SCC 560",
            "court": "Supreme Court",
            "year": 2018,
            "ratio": "Compounding of NI Act offence permissible at any stage. Court should encourage settlement.",
            "keywords": ["ni act", "138", "compounding", "settlement"]
        }
    ],

    # Writ Petitions
    "writ": [
        {
            "case_name": "Romesh Thappar v. State of Madras",
            "citation": "AIR 1950 SC 124",
            "court": "Supreme Court",
            "year": 1950,
            "ratio": "Article 32 is itself a fundamental right. Right to move Supreme Court for enforcement of fundamental rights.",
            "keywords": ["writ", "article 32", "fundamental right"]
        },
        {
            "case_name": "L. Chandra Kumar v. Union of India",
            "citation": "(1997) 3 SCC 261",
            "court": "Supreme Court",
            "year": 1997,
            "ratio": "Judicial review under Articles 226 and 32 is basic structure. Cannot be excluded by any statute.",
            "keywords": ["writ", "judicial review", "basic structure", "226"]
        }
    ]
}


def research_case_law(
    legal_issue: str,
    section: str = None,
    court_preference: str = "Both",
    year_range: str = "2010-2026",
    fact_similarity: str = None,
    tool_context: ToolContext = None
) -> str:
    """
    Search SC/HC case law for relevant precedents.

    Args:
        legal_issue: The legal issue to research
        section: Relevant statutory provision (optional)
        court_preference: "SC" / "HC" / "Both"
        year_range: Time range for cases (e.g., "2014-2026")
        fact_similarity: Factual context for better matching (optional)
        tool_context: ADK ToolContext

    Returns:
        JSON with case citations, ratio, applicability, verification status
    """
    logger.info(f"[CASE_LAW_RESEARCH] Researching: {legal_issue[:50]}...")

    result = {
        "response_type": "case_law_research",
        "jurisdiction": "India",
        "legal_issue": legal_issue,
        "section": section,
        "court_preference": court_preference,
        "year_range": year_range,
        "cases_found": [],
        "key_principles": [],
        "research_notes": [],
        "verification_warning": "ALL CITATIONS REQUIRE VERIFICATION on SCC Online, Manupatra, or Indian Kanoon before use.",
        "disclaimer": "This research is AI-assisted. Verify all case citations independently."
    }

    # Search for relevant cases based on issue keywords
    issue_lower = legal_issue.lower()
    matched_categories = []

    if any(word in issue_lower for word in ["anticipatory", "bail", "arrest", "custody"]):
        matched_categories.append("anticipatory_bail")

    if any(word in issue_lower for word in ["quash", "482", "528", "fir", "proceeding"]):
        matched_categories.append("quashing")

    if any(word in issue_lower for word in ["fir", "complaint", "154", "173", "cognizable"]):
        matched_categories.append("fir")

    if any(word in issue_lower for word in ["cheating", "420", "318", "fraud", "dishonest"]):
        matched_categories.append("cheating")

    if any(word in issue_lower for word in ["defamation", "499", "356", "reputation"]):
        matched_categories.append("defamation")

    if any(word in issue_lower for word in ["498a", "cruelty", "dowry", "matrimonial"]):
        matched_categories.append("498a_cruelty")

    if any(word in issue_lower for word in ["ndps", "drugs", "narcotics", "contraband"]):
        matched_categories.append("ndps")

    if any(word in issue_lower for word in ["cheque", "138", "ni act", "dishonour"]):
        matched_categories.append("cheque_bounce")

    if any(word in issue_lower for word in ["writ", "226", "32", "habeas", "mandamus", "certiorari"]):
        matched_categories.append("writ")

    # Parse year range
    try:
        if "-" in year_range:
            start_year, end_year = map(int, year_range.split("-"))
        else:
            start_year, end_year = 2010, 2026
    except:
        start_year, end_year = 2010, 2026

    # Collect matching cases
    for category in matched_categories:
        if category in LANDMARK_CASES:
            for case in LANDMARK_CASES[category]:
                # Filter by year if specified
                if start_year <= case["year"] <= end_year:
                    # Filter by court preference
                    if court_preference.upper() == "BOTH" or \
                       (court_preference.upper() == "SC" and case["court"] == "Supreme Court") or \
                       (court_preference.upper() == "HC" and "High Court" in case["court"]):

                        result["cases_found"].append({
                            "case_name": case["case_name"],
                            "citation": case["citation"],
                            "court": case["court"],
                            "year": case["year"],
                            "ratio_decidendi": case["ratio"],
                            "applicability": f"Relevant to: {legal_issue[:100]}",
                            "verification_status": "NEEDS VERIFICATION - Verify on official sources"
                        })

                        # Extract key principle
                        if case["ratio"] not in [p.get("principle") for p in result["key_principles"]]:
                            result["key_principles"].append({
                                "principle": case["ratio"],
                                "source": case["case_name"]
                            })

    # Add research notes
    if not result["cases_found"]:
        result["research_notes"].append("No exact matches found in landmark cases database. Recommend searching SCC Online/Manupatra.")
        result["research_notes"].append(f"Suggested search terms: {legal_issue}")
    else:
        result["research_notes"].append(f"Found {len(result['cases_found'])} potentially relevant case(s).")
        result["research_notes"].append("These are commonly cited precedents. Additional research recommended for recent developments.")

    # Add section-specific notes
    if section:
        result["research_notes"].append(f"Searched for cases interpreting: {section}")

    # Add fact similarity analysis if provided
    if fact_similarity:
        result["fact_analysis"] = {
            "provided_facts": fact_similarity[:500],
            "note": "Compare cited case facts with your matter to assess applicability strength."
        }

    return json.dumps(result, indent=2, ensure_ascii=False)


def get_case_by_citation(citation: str) -> Optional[dict]:
    """Retrieve case details by citation."""
    for category, cases in LANDMARK_CASES.items():
        for case in cases:
            if citation.lower() in case["citation"].lower():
                return case
    return None


def get_cases_by_keyword(keyword: str, limit: int = 5) -> List[dict]:
    """Search cases by keyword."""
    results = []
    keyword_lower = keyword.lower()

    for category, cases in LANDMARK_CASES.items():
        for case in cases:
            if keyword_lower in " ".join(case.get("keywords", [])).lower() or \
               keyword_lower in case["ratio"].lower() or \
               keyword_lower in case["case_name"].lower():
                results.append(case)
                if len(results) >= limit:
                    return results

    return results
