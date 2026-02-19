# Repository Guidelines

## Project Structure & Module Organization
- `lexedge/`: Python agent server and core logic (FastAPI app in `lexedge/api/app.py`, agents in `lexedge/sub_agents`, tools in `lexedge/tools`, utilities in `lexedge/utils`).
- `lexedge/tests/`: Python test suite and runner scripts.
- `frontend/`: Vite + React UI (`frontend/src` for source, `frontend/public` for static assets).
- `docs/`: setup and architecture notes (see `docs/start.md`).
- Root config: `requirements.txt`, `.env` (local secrets), `README.md`.

## Build, Test, and Development Commands
- Install backend deps: `pip install -r requirements.txt`.
- Run the agent server (port 3333): `PYTHONPATH=. ./.venv/bin/python3 lexedge/api/app.py` or `python -m lexedge.api.app`.
- Run the frontend (port 5173): `npm --prefix frontend run dev`.
- Build the frontend: `npm --prefix frontend run build`.
- Lint the frontend: `npm --prefix frontend run lint`.
- Run all tests: `python lexedge/tests/run_all_tests.py` (or run a single file like `python lexedge/tests/test_websocket_integration.py`).

## Coding Style & Naming Conventions
- Python: follow existing module structure and PEP 8 style (4-space indentation, `snake_case` functions, `CapWords` classes).
- React: components in `PascalCase`, hooks in `useX` form; keep JSX in `frontend/src`.
- Formatting is not centrally enforced; keep changes consistent with nearby code and run ESLint for frontend edits.

## Testing Guidelines
- Tests live under `lexedge/tests/` and follow `test_*.py` naming.
- Many tests require an active WebSocket session; start the app and connect via the UI before running the suite.

## Commit & Pull Request Guidelines
- Commit messages follow a short, typed prefix pattern (e.g., `feat: add image upload`, `Fix: stabilize chat`, `docs: add start.md`). Keep them imperative and concise.
- PRs should include a brief summary, key testing commands executed, and screenshots/GIFs for UI changes. Link related issues when applicable.

## Security & Configuration Tips
- Never commit `.env` or API keys. Required values include `GOOGLE_API_KEY`, `LLM_BASE_URL`, and `BACKEND_URL`.
- Default ports: agent server `3333`, frontend `5173`.
