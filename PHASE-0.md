# Phase 0 — Project Foundation

## Goal

Create a clean local foundation for the Livestock Intelligence & Early-Warning System.

## Included

- Git-ready repository structure
- FastAPI backend
- Next.js frontend
- English UI
- White/navy visual foundation
- `.env.example`
- Basic backend health endpoint
- Basic backend test
- Local development only

## Explicitly NOT included

- Docker
- CI/CD
- PostgreSQL
- pgvector
- LLM integration
- Web scraping
- RSS/API collectors
- Authentication
- Microsoft Teams
- Power BI
- Production deployment

These are intentionally deferred.

## Run backend

```bash
cd backend

python -m venv .venv
.venv\Scripts\activate

pip install -e ".[dev]"

uvicorn app.main:app --reload --port 8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

Run tests:

```bash
pytest
```

## Run frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## Phase 0 acceptance criteria

- Backend starts successfully.
- `/health` returns HTTP 200.
- Backend test passes.
- Frontend starts successfully.
- Frontend renders the Livestock Intelligence landing page.
- UI uses the agreed white/navy visual direction.
- No secrets are committed.
- No database or external AI service is required.

## Approval gate

Do not start Phase 1 until Phase 0 has been tested and explicitly approved.
