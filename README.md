# Folio

Bring-your-own-key RAG app: upload your documents, connect your own Groq, Cerebras, or
Hugging Face key, and chat with answers cited from your files.

| Part | Stack | Folder |
|---|---|---|
| Frontend | Next.js 16 (App Router, JavaScript), Tailwind CSS | `frontend/` |
| Backend | FastAPI, MongoDB (Motor), LlamaIndex, LangChain, local FastEmbed | `backend/` |

Architecture notes: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Production checklist: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

**Never commit `.env` or `.env.local`.** Those files hold secrets. The repo only ships empty templates (`.env.example`).

---

## Prerequisites

Install these before you clone:

- **Git**
- **Node.js 20+** ([download](https://nodejs.org/))
- **Python 3.11+** ([download](https://www.python.org/downloads/))
- **MongoDB Community Server** listening on port `27017`
  ([download](https://www.mongodb.com/try/download/community))
- Optional: [MongoDB Compass](https://www.mongodb.com/try/download/compass) to inspect data

On Windows, MongoDB usually runs as the `MongoDB` service after install. Confirm Compass can
connect to `mongodb://localhost:27017`. The `folio` database is created automatically on first API start.

You also need **your own LLM API key** later in the app (not in `.env`):

- Groq native key starting with `gsk_` ([console.groq.com/keys](https://console.groq.com/keys)), or
- Cerebras native key starting with `csk_` ([cloud.cerebras.ai](https://cloud.cerebras.ai)), or
- Hugging Face token starting with `hf_` with Inference Provider credits ([huggingface.co/settings/tokens](https://huggingface.co/settings/tokens))

---

## 1. Clone

```bash
git clone https://github.com/bilalTheDev/Folio.git
cd Folio
```

---

## 2. Backend

From the repo root:

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

macOS / Linux:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Fill in `backend/.env`

Copy the block below into `backend/.env`, then **replace the three secret lines** with values you generate on your machine.

```env
APP_ENV=development

MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=folio

JWT_SECRET=replace-me
JWT_REFRESH_SECRET=replace-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
REFRESH_COOKIE_NAME=folio_refresh
COOKIE_SECURE=false
COOKIE_SAMESITE=lax

ENCRYPTION_KEY=replace-me

CORS_ORIGIN=http://localhost:3000

STORAGE_DIR=storage
MAX_UPLOAD_BYTES=10485760

EMBED_MODEL=BAAI/bge-small-en-v1.5
CHUNK_SIZE=512
CHUNK_OVERLAP=50
CHUNK_LEAF_PROSE=512
CHUNK_PARENT_PROSE=2048
CHUNK_LEAF_STRUCTURED=256
CHUNK_PARENT_STRUCTURED=1024
RETRIEVAL_TOP_K=5
RETRIEVAL_CANDIDATE_K=20
RERANK_ENABLED=true

HF_ROUTER_BASE_URL=https://router.huggingface.co/v1
LLM_TIMEOUT_SECONDS=60

RATE_LIMIT_AUTH=10/minute
RATE_LIMIT_UPLOAD=20/minute
RATE_LIMIT_CHAT=30/minute
```

Generate the secrets (run the JWT command twice so access and refresh secrets are different):

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste the first two outputs into `JWT_SECRET` and `JWT_REFRESH_SECRET`. Paste the Fernet output into `ENCRYPTION_KEY`. Do not reuse sample values from docs or screenshots.

### Start the API

Keep the venv activated:

```powershell
uvicorn app.main:app --reload --port 8000
```

- API: <http://localhost:8000/> → `{"message": "Hello Folio"}`
- Health: <http://localhost:8000/health> → `{"status": "ok"}`
- Docs: <http://localhost:8000/docs>

The first start downloads the local embedding model (`BAAI/bge-small-en-v1.5`, roughly 70 MB) into `backend/.cache/fastembed`. That cache is gitignored. Later starts reuse it. No LLM key is required for this download.

Leave this terminal running.

---

## 3. Frontend

Open a **second** terminal from the repo root:

```powershell
cd frontend
npm install
copy .env.example .env.local
```

macOS / Linux: `cp .env.example .env.local`

`frontend/.env.local` only needs public URLs (not secrets):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MAX_UPLOAD_BYTES=10485760
```

Start the app:

```powershell
npm run dev
```

Open <http://localhost:3000>.

---

## 4. First run in the browser

1. Sign up at `/signup` (email + password).
2. Upload a PDF, Word (`.docx`), `.txt`, or Markdown file (10 MB max).
3. Choose a provider and paste **your** API key in the app (Groq / Cerebras / Hugging Face). Folio encrypts it with `ENCRYPTION_KEY` and never stores it in `.env`.
4. Open a chat and ask a question about the uploaded file. Citations open the exact passage.

If the UI says it cannot reach the Folio server, the API on port 8000 is not running.

---

## 5. Tests

```powershell
cd backend
venv\Scripts\activate
pytest
```

Tests use a disposable `folio_test` MongoDB database and a temp storage folder, then clean both up. They do not read your real LLM keys.

Optional retrieval eval (no live LLM):

```powershell
python scripts/eval_retrieval.py
```

---

## Environment variable reference

### Backend (`backend/.env`)

| Variable | Local value | Notes |
|---|---|---|
| `APP_ENV` | `development` | Use `production` only when deploying. |
| `MONGODB_URI` | `mongodb://localhost:27017` | Local Compass connection string. |
| `MONGODB_DB_NAME` | `folio` | Created on first use. |
| `JWT_SECRET` | generated | Min 32 characters. Secret. |
| `JWT_REFRESH_SECRET` | generated | Different from `JWT_SECRET`. Secret. |
| `JWT_ALGORITHM` | `HS256` | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | |
| `REFRESH_COOKIE_NAME` | `folio_refresh` | httpOnly cookie path `/auth`. |
| `COOKIE_SECURE` | `false` | `true` in production (HTTPS). |
| `COOKIE_SAMESITE` | `lax` | |
| `ENCRYPTION_KEY` | generated Fernet key | Encrypts provider tokens at rest. Losing it makes saved keys unreadable. |
| `CORS_ORIGIN` | `http://localhost:3000` | Must match the Next.js origin exactly. |
| `STORAGE_DIR` | `storage` | Uploads + per-user Chroma indexes. Gitignored. |
| `MAX_UPLOAD_BYTES` | `10485760` | 10 MB cap; cannot be raised above this. |
| `EMBED_MODEL` | `BAAI/bge-small-en-v1.5` | Local FastEmbed. Changing it requires reindexing. |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `512` / `50` | |
| `RETRIEVAL_TOP_K` | `5` | Passages sent to the LLM. |
| `RETRIEVAL_CANDIDATE_K` | `20` | Hybrid retrieve pool before rerank. |
| `RERANK_ENABLED` | `true` | Reranks with the same local embed model (no extra download). |
| `HF_ROUTER_BASE_URL` | `https://router.huggingface.co/v1` | Used only for Hugging Face Inference Providers. |
| `LLM_TIMEOUT_SECONDS` | `60` | |
| `RATE_LIMIT_*` | see example | Auth / upload / chat. |

Provider API keys (`gsk_…`, `csk_…`, `hf_…`) go in **Settings in the app**, not in `.env`.

### Frontend (`frontend/.env.local`)

| Variable | Local value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` |
| `NEXT_PUBLIC_MAX_UPLOAD_BYTES` | `10485760` |

---

## Git workflow

`main` is the default clone target. Feature work lands on `phase-…` branches and merges through `develop`.

Do not commit:

- `backend/.env`, `frontend/.env.local`
- `backend/venv/`, `frontend/node_modules/`
- `backend/storage/`, `backend/.cache/`
- `.next/`
