# Business Adaptive EDI & API Integration Portal

Light-weight prototype for EDI parsing, transformation and audit/replay (thesis MVP).

## Overview
- FastAPI backend exposing endpoints to ingest EDI-like XML for `850` (PO) and `856` (ASN).
- Transforms raw XML into a canonical model and a Netsuite-style payload.
- Persists runs in `runs.db` for audit and replay via `/replay/{run_id}`.
- Simple frontend UI is served at `/ui` for non-technical testing.

## Prerequisites
- Python 3.10+ installed on Windows

## Quick start (PowerShell)
1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install required packages:

```powershell
pip install fastapi uvicorn lxml
```

3. Run the application (from the project root):

```powershell
python -m uvicorn app:app --reload --port 8000
```

4. Open the UI in your browser:

http://localhost:8000/ui/

API docs (interactive):

http://localhost:8000/docs

## Mapping Assistant (AI chatbot)
This project includes a simple mapping assistant endpoint that uses an OpenAI-compatible model to provide EDI -> API mapping help.

1. Set your OpenAI API key in the environment (PowerShell):

```powershell
$env:OPENAI_API_KEY = "sk-..."
```

2. (Optional) select model via `OPENAI_MODEL` env var (default `gpt-3.5-turbo`):

```powershell
$env:OPENAI_MODEL = "gpt-3.5-turbo"
```

3. The frontend includes a "Mapping Assistant (AI)" panel at `/ui` where non-technical users can ask mapping questions. The frontend calls `POST /chat/map` with `{ "message": "..." }` and the backend relays to the configured model with a system prompt that restricts answers to mapping help only.

Security & notes:
- Do not commit your API key. The server reads `OPENAI_API_KEY` from the environment.
- Install the `openai` Python package to enable the feature:

```powershell
pip install openai
```

## Notes

```powershell
pip freeze > requirements.txt
```

## Example curl (Linux/macOS) / PowerShell equivalent
- Ingest an 850 (example):

```bash
curl -X POST "http://localhost:8000/ingest/850" -H "Content-Type: application/json" -d '{"raw_xml":"<?xml version=\"1.0\"?><order><poNumber>PO-12345</poNumber></order>"}'
```

## Where to look in the code
- `app.py` — API routes, mounts `frontend/` at `/ui` and runs DB initialization.
- `transform.py` — XML -> canonical -> Netsuite payload functions for 850 and 856.
- `db.py` — SQLite helpers and `insert_run()` for audit storage.
- `frontend/` — `index.html`, `app.js`, `styles.css` (user-friendly portal).

If you'd like, I can also add a `requirements.txt`, a small test script that posts sample payloads, or a packaged run script for Windows.
## Scope of Implementation

Implemented:
- Inbound 850 parsing
- Inbound 856 parsing
- Canonical transformation
- Netsuite-style payload generation
- Audit logging and replay
- AI-assisted mapping helper

Not implemented:
- Real Netsuite connection
- Real EDI X12 parsing
- Authentication and role management
- Production-grade error handling
