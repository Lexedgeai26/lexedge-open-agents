# LexEdge: Legal Response Template System

This document outlines how LexEdge transforms structured JSON responses from legal tools into premium, professional HTML templates for the frontend.

---

## 1. Overview

The formatting logic resides in `lexedge/utils/response_formatter.py`. 
The system uses a **Server-Side Rendering (SSR)** approach for chat bubbles:
1.  **Legal Agents** return a raw JSON dictionary containing legal findings.
2.  **LexEdge Backend** (Python) processes this JSON and generates an HTML string.
3.  **Frontend** (React) safely renders this HTML string inside the chat interface.

This ensures consistent legal professional styling and allows for complex logic (like risk highlighting) to be handled centrally.

---

## 2. Core Template Types

The system dispatches to different specialized templates based on the `response_type` field.

### 2.1 Legal Assessment Template (`response_type: "legal_analysis"`)
Used for case evaluations and strategic summaries.
- **Header**: Case name & Jurisdiction.
- **Findings**: Structured analysis of facts.
- **Risk Level**: Color-coded (Red for High Risk, Green for Low Risk).
- **Next Steps**: Actionable checklist for the user.

### 2.2 Document Analysis Template (`response_type: "document_analysis"`)
Used when a document (FIR, Contract, Order) is analyzed.
- **Summary**: Brief overview of the document nature.
- **Key Provisions**: Bulleted list of important clauses/sections.
- **Identified Risks**: Specific legal red flags in the document.

### 2.3 Specialist Opinion Template (`response_type: "specialist_opinion"`)
Used for niche area queries (IP, Tax, Immigration).
- **Specialty Badge**: Identifies the area of expertise.
- **Key Considerations**: Domain-specific legal factors.

---

## 3. Dynamic Styling

The theme engine assigns colors based on the **Risk Level** or **Urgency**:

| Risk level | Color Code | Visual Representation |
|------------|------------|-----------------------|
| `Critical` | `#ef4444`  | 🔴 RED (Emergencies/Deadlines)|
| `High`     | `#f97316`  | 🟠 ORANGE (Major Risks)      |
| `Moderate` | `#eab308`  | 🟡 YELLOW (Standard Risks)   |
| `Low`      | `#22c55e`  | 🟢 GREEN (Safe/Routine)      |

---

## 4. Usage in Code

To send a formatted response from a tool:

```python
from lexedge.utils.response_formatter import format_premium_template
from lexedge.utils.tool_response_handler import create_tool_handler

# ... inside your tool function ...
tool_handler = create_tool_handler("LegalDocsTool")
response_data = {
    "response_type": "document_analysis",
    "document_type": "FIR",
    # ... other data ...
}
formatted_html = format_premium_template(response_data)

# Push to UI immediately
tool_handler.send_websocket_notification(formatted_html, cancel_llm_processing=True)
```

---
**Maintained by LexEdge Legal Engineering Team**
