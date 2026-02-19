# LexEdge: Backend API Documentation

This document lists the available backend API endpoints for the LexEdge Legal AI application.

---

## 1. Core Backend (FastAPI)

**Base URL**: `http://localhost:8000` (Default)  
**Authentication**: Token-based authentication for legal professional sessions.

### Authentication & Sessions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/token-login` | Authenticate with a pre-validated token; returns `session_id`. |
| POST | `/sessions` | Create a new legal session. |
| GET | `/sessions/{id}` | Retrieve session state and context. |
| DELETE | `/sessions/{id}` | Invalidate and delete a legal session. |
| POST | `/logout` | Log out and clear all session data/history. |

### AI Interaction
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agent/query` | Synchronous agent query (Standard ADK turn). |
| POST | `/agent/stream` | Streaming agent response via SSE (Server-Sent Events). |
| WS | `/ws/{session_id}`| Real-time bi-directional communication. |

### Case History & Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/chat-history/{id}` | Get full conversation history for a specific session. |
| GET | `/user-chat-history`| Get all sessions and history for a specific user ID. |
| POST | `/audio/transcribe` | Proxy for transcribing legal dictations/voice notes. |

---

## 2. WebSocket Protocol

LexEdge uses WebSockets for real-time tool notifications and premium template delivery.

- **Endpoint**: `ws://localhost:8000/ws/{session_id}`
- **Message Types**:
  - `response`: Standard agent text or HTML template.
  - `processing_cancelled`: Signal that an LLM turn was interrupted by a tool.
  - `action_suggestions`: Contextual buttons for the next legal steps.

---

## 3. Running the Server

To start the LexEdge backend:

```bash
# From the project root
python -m lexedge.api.app
```

The server will be accessible at `http://localhost:8000`, with automated Swagger documentation at `/docs`.

---
**Maintained by LexEdge Advanced Engineering Team**