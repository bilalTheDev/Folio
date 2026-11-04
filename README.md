# Folio

Bring-your-own-key RAG app: upload your documents, connect your own Hugging Face token,
pick an inference provider, and chat with answers cited from your own sources.

| Part | Stack | Folder |
|---|---|---|
| Frontend | Next.js (App Router, JavaScript), Tailwind CSS | `frontend/` |
| Backend | FastAPI, MongoDB (Motor), LlamaIndex, LangChain | `backend/` |

Architecture, API surface, and env vars: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Prerequisites

- Node.js 20+
- Python 3.11+
- MongoDB Community Server running locally on port 27017
  ([download](https://www.mongodb.com/try/download/community)), plus
  [MongoDB Compass](https://www.mongodb.com/try/download/compass) to inspect data.
  Compass is only a client; the server must be running.

## 1. MongoDB

Start MongoDB (on Windows it usually runs as the `MongoDB` service after install), then in
Compass connect to:

```
mongodb://localhost:27017
```

The `folio` database and its collections are created by the backend on first use.

## 2. Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate              # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env             # macOS/Linux: cp .env.example .env
uvicorn app.main:app --reload
```

Fill in `backend/.env`. Local values that work:

```env
APP_ENV=development
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=folio
CORS_ORIGIN=http://localhost:3000
```

Generate secrets:

```powershell
# JWT_SECRET and JWT_REFRESH_SECRET (run twice, use different values)
python -c "import secrets; print(secrets.token_urlsafe(64))"
# ENCRYPTION_KEY (Fernet)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Check it: <http://localhost:8000/> returns `{"message": "Hello Folio"}`; API docs at
<http://localhost:8000/docs>.

## 3. Frontend

```powershell
cd frontend
npm install
copy .env.example .env.local       # macOS/Linux: cp .env.example .env.local
npm run dev
```

In `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MAX_UPLOAD_BYTES=10485760
```

Open <http://localhost:3000>.

## Git workflow

`main` holds releases, `develop` is the integration branch, and each phase is built on its
own `phase-N/<slug>` branch merged into `develop` by pull request.

Backend tests (uses a disposable `folio_test` database, then drops it):

```powershell
cd backend
venv\Scripts\activate
pytest
```

## Status

**Backend (Phases 3–10):** implemented. Auth, onboarding APIs, upload (10 MB cap), HF token encryption, provider selection, per-user LlamaIndex/Chroma indexing, grounded chat with source excerpts, session history, rate limits, and a deployment checklist in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

**Frontend:** Phase 2 placeholder still boots at `/` with “Hello Folio”. App screens (`/signup`, `/onboarding/*`, `/app/*`) are not part of this backend pass.

To run the API: `cd backend` → `venv\Scripts\activate` → `uvicorn app.main:app --reload` → http://localhost:8000/docs.
