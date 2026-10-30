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

### Neon Postgres

This repo is linked to a Neon project via `.neon` + `neon.ts`. `neon deploy` / `neon env pull` write `DATABASE_URL` (pooled), `DATABASE_URL_UNPOOLED` (direct), and `NEON_BRANCH` into `.env.local`.

```bash
neon deploy
npm run migrate   # uses DATABASE_URL_UNPOOLED when present
```

The FastAPI app reads those vars (SQLAlchemy + asyncpg, SSL on). Prefer the pooled URL for app traffic and the unpooled URL for migrations.

### Database migrations

With `DATABASE_URL` / `DATABASE_URL_UNPOOLED` set (from Neon):

```bash
python db/migrate.py
# or: npm run migrate
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

**Product features on `develop` (auth/DB optional for demo paths)**

Backend:
- Document ingestion (validate → extract → chunk → embed → store)
- Clerk JWT auth dependency
- pgvector retrieval (top 6) + grounded prompt
- OpenAI-compatible provider streaming (SSE: meta / token / citations / done / error)
- Threads, messages, citations, Markdown export, regenerate flag
- Public sample trial (`GET/POST /api/sample`) with IP daily + burst limits
- Provider catalog + key test
- `/api/me` profile, theme defaults, encrypted remember-key helpers

Frontend (Quiet Light / Mineral Emerald):
- Landing, auth, workspace (citations, stop/regenerate/export), settings, admin
- Library + upload (API when signed in, demo fallback), history + export, command palette
- `/try` sample trial wired to `/api/sample`
- Typography: Newsreader, Inter, JetBrains Mono · accent `#00D59D`

Eval: `python eval/run_eval.py` (lexical retrieval baseline on the sample report).

Next: Neon migrate + Clerk env for live end-to-end; OCR and team admin remain later.
