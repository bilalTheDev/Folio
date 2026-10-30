# Folio

Document question-answering SaaS: upload a PDF, DOCX, or TXT and ask questions grounded in that document.

## Stack

| Area | Choice |
| --- | --- |
| Frontend | Next.js 15 (App Router), JavaScript, Tailwind CSS, Framer Motion |
| Backend | FastAPI on Python 3.12 |
| Hosting | Vercel (frontend + Python functions under `/api`) |
| Database (later) | Neon Postgres with pgvector |
| Auth (later) | Clerk |
| RAG (later) | LlamaIndex + fastembed (`BAAI/bge-small-en-v1.5`) |

## Folder structure

```
folio/
  frontend/          # Next.js app
  backend/           # FastAPI application and tests
  api/               # Vercel Python entry (wraps FastAPI)
  db/migrations/     # Database migrations (later)
  eval/              # RAG evaluation (later)
  .github/workflows/ # CI
```

## Local setup

### Prerequisites

- Node.js 20+
- Python 3.12+ (3.11 works for local skeleton checks)
- A virtualenv for the backend

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest
ruff check .
uvicorn backend.app.main:app --reload --app-dir ..
```

Health check (with the app running): `GET /api/health`.

### Database migrations

With `DATABASE_URL` set to your Neon connection string:

```bash
python db/migrate.py
```

This applies SQL files in `db/migrations/` (pgvector extension, users, documents, chunks, and related tables).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The placeholder landing page shows the Folio wordmark.

### Environment variables

Copy [`.env.example`](.env.example) to `.env` (and optionally `frontend/.env.local` for Next.js public keys). Never commit secrets.

## Deployment

Deploy the repository root to Vercel. `vercel.json` builds the Next.js app in `frontend/` and routes `/api/*` to `api/index.py` (Python 3.12, `maxDuration` 60). Configure the variables from `.env.example` in the Vercel project settings.

## Status

**Phase 1: ingestion (in progress on `develop`)**

Document upload pipeline is implemented on the backend: validate → extract → chunk → embed → store, plus Clerk JWT auth for protected document routes. Retrieval, chat UI, and provider keys come next.
