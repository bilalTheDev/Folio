# Folio — Architecture (Phase 1)

Bring-your-own-key RAG app: users upload documents, connect their own Hugging Face
token, pick an inference provider/model, and chat with answers grounded in (and cited
from) their own documents.

> Status: **Phase 1 plan, pending confirmation.** Nothing here is scaffolded yet.
> Items marked **[needs approval]** are additions beyond the fixed stack.

---

## 1. Fixed stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (App Router), JavaScript, Tailwind CSS |
| Backend | FastAPI (async), Python 3.11+ |
| Database | MongoDB via Motor; local dev `mongodb://localhost:27017` (Compass) |
| RAG orchestration | LlamaIndex (extract → chunk → embed → index → retrieve, source nodes) |
| Chain / provider calls | LangChain (prompt, chat-history glue, LLM call) |
| Vector store | Chroma (embedded, on disk), one store **per user**, behind LlamaIndex |
| Auth | JWT access (15 min) + refresh (7 days, httpOnly cookie), bcrypt |
| Token at rest | Fernet (`cryptography`) using `ENCRYPTION_KEY` |

### Proposed additions **[needs approval]**

| Package | Why | Phase |
|---|---|---|
| `email-validator` | `EmailStr` validation on signup | 3 |
| `chromadb`, `llama-index-vector-stores-chroma` | Chroma as the LlamaIndex vector store | 6 |
| `llama-index-embeddings-fastembed` (+ `fastembed`) | Local embeddings (`BAAI/bge-small-en-v1.5`, ONNX, no torch) so indexing never spends the user's HF credits | 6 |
| `pypdf`, `python-docx` | PDF / DOCX text extraction (page / section metadata) | 6 |
| `langchain-openai` | `ChatOpenAI` pointed at the HF router's OpenAI-compatible endpoint (`https://router.huggingface.co/v1`) with the user's token | 7 |
| `slowapi` | Rate limiting for `/auth/*`, `/documents/upload`, `/chat/*/messages` | 10 |
| `pytest`, `httpx` (dev only) | Backend tests | 3+ |

Frontend: no additions beyond `axios`, `zustand`, `react-hook-form`.

---

## 2. Monorepo layout

```
Folio/
├── README.md                  # How to run both apps locally
├── .gitignore
├── docs/
│   ├── ARCHITECTURE.md        # This file
│   └── DEPLOYMENT.md          # Phase 10 checklist
├── backend/                   # FastAPI
│   ├── .env.example
│   ├── requirements.txt
│   ├── app/ ...               # see §3
│   ├── storage/               # gitignored: uploads + per-user indexes
│   └── tests/
└── frontend/                  # Next.js
    ├── .env.example
    ├── package.json
    ├── app/ ...               # see §4
    ├── components/
    ├── hooks/
    └── lib/
```

---

## 3. Backend module breakdown

```
backend/
├── app/
│   ├── main.py                 # FastAPI app factory, CORS (single origin), routers, lifespan (Mongo connect + indexes)
│   ├── config.py               # pydantic-settings Settings, reads .env
│   ├── db.py                   # Motor client, get_db(), collection handles, ensure_indexes()
│   ├── deps.py                 # get_current_user, require_onboarded (reusable dependencies)
│   ├── core/
│   │   ├── security.py         # bcrypt hash/verify, create/decode access + refresh JWTs
│   │   ├── cookies.py          # set/clear refresh cookie (httpOnly, Secure, SameSite from env)
│   │   ├── errors.py           # Uniform error shape + exception handlers
│   │   ├── logging.py          # Log config + redaction filter (strips hf_* tokens, Authorization headers)
│   │   └── rate_limit.py       # Limiter (Phase 10)
│   ├── models/                 # Pydantic request/response schemas (Mongo docs are dicts)
│   │   ├── common.py           # PyObjectId, timestamps, serialize helpers
│   │   ├── user.py             # SignupIn, SigninIn, UserOut (masked token), HfTokenIn, ProviderIn
│   │   ├── document.py         # DocumentOut, DocumentStatus enum
│   │   └── chat.py             # SessionIn/Out, MessageIn/Out, SourceOut
│   ├── routers/
│   │   ├── health.py           # GET /            -> "Hello Folio" ; GET /health
│   │   ├── auth.py             # POST /auth/signup, /auth/signin, /auth/refresh, /auth/signout
│   │   ├── users.py            # GET /users/me ; PATCH /users/me/hf-token, /provider, /onboarding
│   │   ├── documents.py        # POST /documents/upload ; GET /documents ; DELETE /documents/{id} ; POST /documents/{id}/reindex
│   │   ├── providers.py        # GET /providers (allowlisted providers + models)
│   │   └── chat.py             # sessions CRUD + POST /chat/sessions/{id}/messages
│   ├── services/
│   │   ├── encryption.py       # Fernet encrypt/decrypt, mask_token() -> "hf_****1234"
│   │   ├── storage.py          # Stream upload to backend/storage/{user_id}/files/, 10MB hard cap, delete
│   │   ├── extraction.py       # PDF (per page) / DOCX (per heading section) / TXT -> LlamaIndex Documents
│   │   ├── rag.py              # Per-user index: ingest_document, delete_document_nodes, retrieve(user_id, query, k)
│   │   ├── providers.py        # Provider/model allowlist (single source of truth)
│   │   ├── llm.py              # LangChain ChatOpenAI factory (HF router, user's token, provider suffix)
│   │   └── chat.py             # Orchestrates: history + retrieve + chain + persist
│   └── utils/
│       └── titles.py           # Auto-title from first message
├── storage/                    # gitignored
│   └── {user_id}/
│       ├── files/{document_id}{ext}
│       └── index/              # Chroma persist dir for this user only
└── tests/
    ├── conftest.py             # Test DB (folio_test), app client, user factory
    ├── test_auth.py
    ├── test_documents.py
    ├── test_users.py
    ├── test_rag_scoping.py     # Two users, no cross-retrieval (Phase 10)
    └── test_chat.py
```

### Collections and indexes

| Collection | Fields (fixed) | Indexes |
|---|---|---|
| `users` | `_id, email, password_hash, created_at, onboarding_completed, hf_token_encrypted, selected_provider, selected_model` | unique `email` (lowercased) |
| `documents` | `_id, user_id, filename, size_bytes, mime_type, storage_path, status, uploaded_at, chunk_count` | `user_id, uploaded_at` |
| `chat_sessions` | `_id, user_id, title, created_at, updated_at` | `user_id, updated_at` |
| `chat_messages` | `_id, session_id, role, content, sources[], created_at` | `session_id, created_at` |

`sources[]` items store `{document_id, chunk_text, page_or_section}`; the API response
also adds `filename` (looked up from `documents`) so the UI can render "verify source"
without a second call.

### Security rules baked into the design

- **10MB cap**: `storage.py` streams the upload in chunks and aborts with **413** the moment
  the byte count passes `MAX_UPLOAD_BYTES` (does not trust `Content-Length` or the client).
  MIME is checked by extension **and** magic bytes (`%PDF`, DOCX zip header, UTF-8 decode for TXT).
- **HF token**: only `hf_token_encrypted` is stored. `UserOut` exposes `hf_token_masked`
  (`hf_****1234`) and `has_hf_token`; plaintext exists only in memory inside `llm.py` for
  the duration of a provider call. Logging filter redacts `hf_[A-Za-z0-9]+`.
- **Retrieval scoping**: each user has their own Chroma directory at
  `storage/{user_id}/index`. `rag.retrieve()` takes `user_id` from `get_current_user`
  only (never from the request body) and additionally applies a `user_id` metadata filter.
  There is no global index object.
- **Ownership**: every document/session query filters on `user_id`; a foreign id returns **404**
  (not 403) to avoid leaking existence.
- **CORS**: `allow_origins=[CORS_ORIGIN]` (exactly one), `allow_credentials=True`.
- **Onboarding enforcement (server side)**: `require_onboarded` guards `/chat/*`.
  `PATCH /users/me/onboarding` only succeeds if the user has ≥1 document, a saved token,
  and a provider/model; otherwise **409** with the missing step.

### API surface

| Method | Path | Auth | Phase |
|---|---|---|---|
| GET | `/`, `/health` | — | 2 |
| POST | `/auth/signup` | — | 3 |
| POST | `/auth/signin` | — (sets refresh cookie) | 3 |
| POST | `/auth/refresh` | refresh cookie (rotates both) | 3 |
| POST | `/auth/signout` | refresh cookie (clears it) | 3 |
| GET | `/users/me` | access | 3 |
| POST | `/documents/upload` | access | 4 |
| GET | `/documents` | access | 4 |
| DELETE | `/documents/{id}` | access | 4 (index cleanup in 6) |
| PATCH | `/users/me/hf-token` | access | 5 |
| GET | `/providers` | access | 5 |
| PATCH | `/users/me/provider` | access | 5 |
| PATCH | `/users/me/onboarding` | access | 5 |
| POST | `/documents/{id}/reindex` | access | 6 |
| POST / GET | `/chat/sessions` | access + onboarded | 7 |
| GET | `/chat/sessions/{id}/messages` | access + onboarded | 7 |
| POST | `/chat/sessions/{id}/messages` | access + onboarded | 7 |
| PATCH / DELETE | `/chat/sessions/{id}` | access + onboarded | 8 |

`GET /users/me` returns a derived `onboarding` object (not stored) so the frontend can
route to the right step:

```json
{
  "id": "…", "email": "…", "created_at": "…",
  "has_hf_token": true, "hf_token_masked": "hf_****1234",
  "selected_provider": "groq", "selected_model": "meta-llama/Llama-3.3-70B-Instruct",
  "onboarding_completed": false,
  "onboarding": { "has_document": true, "has_token": true, "has_provider": false, "next_step": "provider" }
}
```

### Provider allowlist (initial, verified against the HF router in Phase 5)

The HF router selects the provider via a model suffix (`<model>:<provider>`).

| Provider key | Models offered |
|---|---|
| `groq` | `meta-llama/Llama-3.3-70B-Instruct`, `openai/gpt-oss-120b` |
| `cerebras` | `meta-llama/Llama-3.3-70B-Instruct`, `openai/gpt-oss-120b` |
| `auto` (HF picks fastest available) | `meta-llama/Llama-3.1-8B-Instruct`, `Qwen/Qwen2.5-72B-Instruct` |

---

## 4. Frontend breakdown

Route groups do not add URL segments, so the `/app/*` URLs live under `app/(app)/app/`.

```
frontend/
├── app/
│   ├── layout.js                       # Root: Inter font, <Providers>, globals.css
│   ├── globals.css
│   ├── not-found.js
│   ├── (public)/
│   │   ├── layout.js                   # Marketing header/footer
│   │   ├── page.js                     # /            landing
│   │   ├── signup/page.js              # /signup
│   │   └── signin/page.js              # /signin
│   ├── (onboarding)/
│   │   ├── layout.js                   # <AuthGuard mode="onboarding"> + step indicator
│   │   └── onboarding/
│   │       ├── upload/page.js          # /onboarding/upload    step 1
│   │       ├── token/page.js           # /onboarding/token     step 2
│   │       └── provider/page.js        # /onboarding/provider  step 3
│   └── (app)/
│       ├── layout.js                   # <AuthGuard mode="app"> + AppShell (nav)
│       └── app/
│           ├── page.js                 # /app -> redirect /app/chat
│           ├── chat/
│           │   ├── layout.js           # Sessions sidebar (persistent across chat routes)
│           │   ├── page.js             # /app/chat            new chat
│           │   └── [sessionId]/page.js # /app/chat/[sessionId]
│           ├── history/page.js         # /app/history
│           ├── documents/page.js       # /app/documents
│           └── settings/page.js        # /app/settings
├── components/
│   ├── ui/                 # Button, Input, Card, Badge, Spinner, Alert, EmptyState, Modal, ProgressBar
│   ├── auth/               # AuthForm, AuthGuard
│   ├── onboarding/         # StepIndicator, ProviderCard
│   ├── documents/          # Dropzone, DocumentList, DocumentRow, StatusBadge
│   ├── chat/               # MessageList, MessageBubble, Composer, CitationChip, SourcePanel, ModelBadge
│   ├── history/            # SessionList, SessionRow
│   └── layout/             # AppShell, SessionSidebar, MarketingNav, Footer
├── hooks/
│   ├── useAuth.js          # Bootstrap (refresh → me), signin/signup/signout
│   ├── useDocuments.js     # List/upload(progress)/delete/reindex + polling while indexing
│   ├── useSessions.js      # List/create/rename/delete
│   └── useChat.js          # Messages for a session, send, pending state
├── lib/
│   ├── api.js              # axios instance, Bearer interceptor, single-flight refresh on 401
│   ├── authStore.js        # zustand: accessToken (memory only), user, status
│   ├── routes.js           # Route constants + nextOnboardingRoute(user)
│   └── format.js           # Bytes, dates
├── .env.example
└── tailwind / eslint / next configs (from create-next-app)
```

### Auth and route protection model

- **Access token**: memory only (zustand), never `localStorage`.
- **Refresh token**: httpOnly cookie set by the API; axios uses `withCredentials: true`.
- **Bootstrap**: on first load of a protected group, `AuthGuard` calls `POST /auth/refresh`
  → `GET /users/me`, then redirects:
  - not signed in → `/signin?next=…`
  - `mode="onboarding"`: if completed → `/app/chat`; if the user jumps ahead (e.g. opens
    `/onboarding/provider` without a token) → the first incomplete step
  - `mode="app"`: if `onboarding_completed` is false → first incomplete onboarding step
- **401 handling**: one in-flight refresh shared by concurrent requests; on refresh
  failure → clear store → `/signin`.
- Server enforcement mirrors this (§3), so the client guard is UX, not the security boundary.

### Design defaults

Neutral palette (Tailwind `zinc`), one accent (`indigo-600`), Inter via `next/font`,
generous spacing, `rounded-xl` cards, subtle borders over shadows. Tailwind config extended
only for `fontFamily.sans`. Replaced wholesale if brand guidelines arrive.

---

## 5. Environment variables (placeholders only)

### `backend/.env.example`

| Variable | Purpose |
|---|---|
| `APP_ENV` | `development` / `production` |
| `MONGODB_URI` | e.g. local Compass instance |
| `MONGODB_DB_NAME` | Database name |
| `JWT_SECRET` | Signs access tokens |
| `JWT_REFRESH_SECRET` | Signs refresh tokens (different from `JWT_SECRET`) |
| `JWT_ALGORITHM` | e.g. HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | e.g. 15 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | e.g. 7 |
| `REFRESH_COOKIE_NAME` | Cookie name |
| `COOKIE_SECURE` | `true` in production |
| `COOKIE_SAMESITE` | `lax` locally, `none` if API and app are on different sites |
| `ENCRYPTION_KEY` | Fernet key (urlsafe base64, 32 bytes) |
| `CORS_ORIGIN` | Exactly one origin: the Next.js app |
| `STORAGE_DIR` | Root for uploads + per-user indexes |
| `MAX_UPLOAD_BYTES` | 10MB = 10485760 |
| `EMBED_MODEL` | Local embedding model id |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 512 / 50 |
| `RETRIEVAL_TOP_K` | Chunks retrieved per question |
| `HF_ROUTER_BASE_URL` | HF Inference Providers OpenAI-compatible base URL |
| `LLM_TIMEOUT_SECONDS` | Provider call timeout |
| `RATE_LIMIT_AUTH` / `RATE_LIMIT_UPLOAD` / `RATE_LIMIT_CHAT` | Phase 10 limits |

```env
APP_ENV=
MONGODB_URI=
MONGODB_DB_NAME=
JWT_SECRET=
JWT_REFRESH_SECRET=
JWT_ALGORITHM=
ACCESS_TOKEN_EXPIRE_MINUTES=
REFRESH_TOKEN_EXPIRE_DAYS=
REFRESH_COOKIE_NAME=
COOKIE_SECURE=
COOKIE_SAMESITE=
ENCRYPTION_KEY=
CORS_ORIGIN=
STORAGE_DIR=
MAX_UPLOAD_BYTES=
EMBED_MODEL=
CHUNK_SIZE=
CHUNK_OVERLAP=
RETRIEVAL_TOP_K=
HF_ROUTER_BASE_URL=
LLM_TIMEOUT_SECONDS=
RATE_LIMIT_AUTH=
RATE_LIMIT_UPLOAD=
RATE_LIMIT_CHAT=
```

### `frontend/.env.example`

```env
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_MAX_UPLOAD_BYTES=
```

`NEXT_PUBLIC_MAX_UPLOAD_BYTES` drives the client-side pre-check only (UX); the server is the
enforcement point.

---

## 6. Sequence: auth → onboarding → chat

```
User            Next.js (frontend)                    FastAPI (backend)                 MongoDB / Disk / HF
 │                     │                                     │                                │
 │── /signup ─────────▶│                                     │                                │
 │   submit form       │── POST /auth/signup ───────────────▶│ validate email, len≥8, bcrypt  │
 │                     │                                     │── insert users ───────────────▶│
 │                     │◀── 201 {user} ──────────────────────│                                │
 │                     │── POST /auth/signin ───────────────▶│ verify bcrypt                  │
 │                     │◀── 200 {access_token, user}         │                                │
 │                     │     + Set-Cookie refresh (httpOnly) │                                │
 │                     │   store access token in memory      │                                │
 │                     │   route by user.onboarding.next_step│                                │
 │                     │                                     │                                │
 │── /onboarding/upload│  AuthGuard: POST /auth/refresh ────▶│ verify cookie, rotate          │
 │                     │             GET /users/me ─────────▶│                                │
 │   drop file         │── POST /documents/upload (multipart, progress) ─▶ stream, 413 >10MB, │
 │                     │                                     │   check MIME, save file ──────▶│ storage/{uid}/files
 │                     │                                     │── insert documents(uploaded) ─▶│
 │                     │◀── 201 {document} ──────────────────│   (Phase 6+: BackgroundTask    │
 │                     │                                     │    ingest → indexing→indexed)  │
 │                     │── GET /documents ──────────────────▶│ (list, Continue enabled ≥1)    │
 │                     │                                     │                                │
 │── /onboarding/token │── PATCH /users/me/hf-token ────────▶│ Fernet encrypt ───────────────▶│ users.hf_token_encrypted
 │                     │◀── 200 {hf_token_masked:"hf_****1234"}                               │
 │                     │                                     │                                │
 │── /onboarding/      │── GET /providers ──────────────────▶│ allowlist                      │
 │   provider          │── PATCH /users/me/provider ────────▶│ validate vs allowlist ────────▶│
 │                     │── PATCH /users/me/onboarding ──────▶│ check doc+token+provider ─────▶│ onboarding_completed=true
 │                     │◀── 200 {user}  → redirect /app/chat │                                │
 │                     │                                     │                                │
 │── /app/chat         │  AuthGuard (app): refresh → me      │                                │
 │                     │── GET /chat/sessions ──────────────▶│ (sidebar)                      │
 │   type question     │── POST /chat/sessions ─────────────▶│ insert session ───────────────▶│
 │                     │   router.replace(/app/chat/{id})    │                                │
 │                     │── POST /chat/sessions/{id}/messages▶│ 1. decrypt HF token (memory)   │
 │                     │                                     │ 2. load last N messages ──────▶│
 │                     │                                     │ 3. retrieve top-k from         │
 │                     │                                     │    storage/{uid}/index only ──▶│ Chroma (per user)
 │                     │                                     │ 4. LangChain prompt(history,   │
 │                     │                                     │    context, question)          │
 │                     │                                     │ 5. ChatOpenAI → HF router ────▶│ Groq / Cerebras / …
 │                     │                                     │ 6. persist user + assistant    │
 │                     │                                     │    (sources[]) ───────────────▶│ chat_messages
 │                     │                                     │ 7. auto-title, bump updated_at │
 │                     │◀── 200 {user_msg, assistant_msg {content, sources[{document_id,      │
 │                     │        filename, chunk_text, page_or_section}]}}                     │
 │   click citation    │   expand SourcePanel (excerpt)      │                                │
 │                     │                                     │                                │
 │   any 401           │── POST /auth/refresh (single-flight) ▶ new access token → retry once │
 │                     │   refresh fails → clear → /signin   │                                │
```

---

## 7. Git workflow

- `main`: releases only. Never committed to directly.
- `develop`: integration branch; each phase merges here through a pull request.
- `phase-N/<slug>`: one branch per phase, cut from the latest `develop`, e.g.
  `phase-2/scaffolding`, `phase-3/auth`, `phase-4/upload`, `phase-5/token-provider`,
  `phase-6/indexing`, `phase-7/chat`, `phase-8/history`, `phase-9/landing-polish`,
  `phase-10/hardening`.
- Conventional commit messages (`feat:`, `fix:`, `chore:`, `docs:`, `test:`).
- After Phase 10, `develop` → `main` pull request tagged `v1.0.0`.

## 8. Decisions taken by default (change before Phase 2 if needed)

1. Vector store: **Chroma**, one persist dir per user.
2. Embeddings: **local** `BAAI/bge-small-en-v1.5` via fastembed.
3. Chat transport: **non-streaming JSON** first; streaming is a follow-up if wanted.
4. Refresh tokens: **stateless** JWT, rotated on every refresh; no revocation collection.
5. Signout endpoint `POST /auth/signout` added (clears the cookie).
