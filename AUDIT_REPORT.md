# Folio Audit Report (Part A)

**Date:** 2026-10-30  
**PRD:** Folio_PRD.pdf v1.1 (source of truth)  
**Scope:** Repository walk only — no code changes for Parts B–D yet.

**Assumptions**
- `Folio_UI_Master_Prompt.txt` and `Folio_Project_Init_Prompt.txt` are **not in the repository**; Quiet Light UI was previously implemented from an in-chat prompt + Figma.
- Local machine runs **Python 3.11.9**; CI and PRD require **Python 3.12**.
- Neon project `soft-hall-31528204` / branch `production` is linked; migrations applied; sample trial works without Clerk.

---

## A1. Inventory

### Runtime / toolchain versions

| Tool | Version | Notes |
| --- | --- | --- |
| Python (local venv) | 3.11.9 | **DRIFT** vs PRD/CI 3.12 |
| Node | 24.13.0 | CI uses Node 20 |
| npm | 11.12.1 | — |
| Next.js | 15.5.28 | Matches PRD stack |
| React | 19.1.0 | — |
| FastAPI | 0.115.6 | — |
| SQLAlchemy | 2.0.36 | — |
| asyncpg | 0.30.0 | — |
| llama-index-core | 0.12.15 | — |
| fastembed | 0.5.1 | BAAI/bge-small-en-v1.5 |
| Framer Motion | 11.15.0 | — |
| Tailwind | 4.3.3 | — |
| Clerk SDK | **not installed** | Auth is stub UI only |
| Vitest / Playwright / mypy | **not present** | Required by PRD testing plan |

### Pinned backend dependencies (`backend/requirements.txt`)

| Package | Version | Status |
| --- | --- | --- |
| fastapi | 0.115.6 | used |
| uvicorn | 0.34.0 | used (local) |
| pydantic / pydantic-settings | 2.10.4 / 2.7.1 | used |
| sqlalchemy / asyncpg / greenlet / pgvector | 2.0.36 / 0.30.0 / 3.1.1 / 0.3.6 | used |
| httpx / python-multipart | 0.28.1 / 0.0.20 | used |
| **slowapi** | **0.1.9** | **unused** (custom `rate_limit.py` instead) |
| cryptography / PyJWT | 44.0.0 / 2.10.1 | used |
| pypdf / python-docx | 5.1.0 / 1.1.2 | used |
| llama-index-core / fastembed | 0.12.15 / 0.5.1 | used (chunking + embeddings; LLM path is raw httpx) |

Dev: pytest 8.3.4, pytest-asyncio 0.25.2, ruff 0.8.6. **No mypy.**

### File / folder inventory

| Path | Purpose | Status |
| --- | --- | --- |
| `Folio_PRD.pdf` | Product requirements v1.1 | complete (reference) |
| `README.md` | Setup + status | partial (ahead of reality on “product features”) |
| `AUDIT_REPORT.md` | This audit | complete |
| `.env.example` | Env var documentation | complete |
| `.env.local` | Neon-pulled secrets (gitignored) | complete (local) |
| `.gitignore` / `.neon` / `neon.ts` | Ignore rules, Neon link, IaC | complete |
| `package.json` (root) | Neon deps + build/migrate scripts | complete |
| `vercel.json` | Next + Python `/api` routing | partial (no warm cron) |
| `api/index.py` | Vercel FastAPI entry | complete |
| `.github/workflows/ci.yml` | Ruff, pytest, frontend build | partial (no pip-audit/npm audit/mypy/e2e) |
| `db/migrate.py` | Apply SQL migrations (prefers unpooled) | complete |
| `db/migrations/001_initial.sql` | Schema + HNSW + pgvector | complete |
| `eval/run_eval.py` + `sample_eval.json` | Lexical sample retrieval harness | partial (not full RAG eval) |
| `scripts/verify_neon.py` | Neon connectivity smoke | complete |
| `scripts/inspect_db_url.py` | Redacted URL inspector | unused (dev helper) |
| `backend/app/main.py` | App factory, CORS, routers | complete |
| `backend/app/config/settings.py` | Settings from `.env.local`/`.env` | complete |
| `backend/app/config/providers.json` | Provider catalog | complete |
| `backend/app/db.py` | Async engine/session + Neon SSL | complete |
| `backend/app/models.py` | SQLAlchemy ORM models | complete |
| `backend/app/providers.py` | Catalog loader (not LLM adapters) | partial / naming drift |
| `backend/app/routes/*` | HTTP routers (documents, threads, me, providers, sample, health, limits) | partial (logic in routes) |
| `backend/app/rag/*` | validate/extract/chunk/embed/ingest/retrieve/prompt/generate/sample | partial (generate uses httpx not LlamaIndex LLM class) |
| `backend/app/security/*` | auth, crypto, logging filter, rate_limit | partial (JWT missing aud/iss) |
| `backend/app/services/usage.py` | Daily usage counters | partial (only usage) |
| `backend/app/schemas/*` | Pydantic document/thread schemas | complete |
| `backend/app/data/sample_report.txt` | Sample trial document | complete |
| `backend/tests/*` | 10 test modules, 24 tests | partial vs PRD coverage |
| `frontend/app/*` | App Router pages | partial (missing PRD routes; no Clerk) |
| `frontend/components/*` | UI by feature | partial (demo/mock heavy) |
| `frontend/lib/api.js` | Single fetch helper | partial (not per-area modules) |
| `frontend/lib/sse.js` | SSE + sample/demo streams | partial |
| `frontend/lib/mock-data.js` | Demo documents/sources | stub / demo |
| `frontend/next.config.js` | CSP, rewrites, turbopack root | complete |
| `frontend/public/*.svg` | Default Next assets | unused (template leftovers) |

**Missing vs PRD layout (Part B targets):** `backend/app/api/`, `services/` (full), `repositories/`, `errors.py`, `deps.py`, `providers/` adapters; `frontend/lib/api/*` modules; Vitest/Playwright; Clerk packages; rehype-sanitize; theme boot script.

---

## A2. Feature status against PRD Section 5

### 5.1 Landing (LP)

| ID | Priority | Status | Notes |
| --- | --- | --- | --- |
| LP-01 | P0 | PARTIAL | Hero + CTAs exist; copy/layout diverge from PRD §9.6 “seven sections only” |
| LP-02 | P0 | PARTIAL | Preview present; not a true answered-with-citations animation loop |
| LP-03 | P0 | DONE | Upload / Ask / Verify style pillars present |
| LP-04 | P0 | PARTIAL | Provider messaging exists; not a dedicated provider strip as specified |
| LP-05 | P0 | PARTIAL | Limits mentioned loosely; not a dedicated limits section |
| LP-06 | P0 | DONE | “Free to use. Bring your own key.” in footer/CTA |
| LP-07 | P1 | DONE | FAQ accordion present |
| LP-08 | P0 | PARTIAL | Footer has GitHub/privacy/terms; contact email unclear |
| LP-09 | P0 | TODO | No Lighthouse measurement recorded |

### 5.2 Authentication (AU)

| ID | Priority | Status | Notes |
| --- | --- | --- | --- |
| AU-01 | P0 | TODO | UI stub only; no `@clerk/*`; form posts nowhere real |
| AU-02 | P0 | TODO | No real session / sign-out |
| AU-03 | P0 | TODO | `/app/*` not protected; portal layout has no auth gate |
| AU-04 | P0 | PARTIAL | Backend JWT verify exists, but **no audience/issuer**; unusable without Clerk env |
| AU-05 | P1 | TODO | No delete-account API or UI wiring |

### 5.3 Documents (DU)

| ID | Priority | Status | Notes |
| --- | --- | --- | --- |
| DU-01–DU-09 | P0 | PARTIAL | Backend pipeline implemented; frontend upload falls back to **demo** without session |
| DU-05 | P0 | DONE | Magic-byte validation in `validate.py` |
| DU-10 | P0 | PARTIAL | UI shows steps; not driven by real document status polling |
| DU-11 | P0 | PARTIAL | Backend failure reasons exist; UI retry incomplete |
| DU-12 | P0 | PARTIAL | Backend delete + SET NULL on threads; UI “source deleted” note missing |
| DU-13 | P0 | DONE (backend) | OCR/no-text rejection message implemented |
| DU-14 | P0 | DONE (backend) | Bytes discarded after ingest |

### 5.4 Chat (CH)

| ID | Priority | Status | Notes |
| --- | --- | --- | --- |
| CH-01 | P0 | PARTIAL | Workspace UI exists; mostly mock/demo stream, not document-scoped API threads |
| CH-02 | P0 | DONE (backend) | Top-6 pgvector cosine retrieval |
| CH-03 | P0 | DONE (backend) | Prompt matches §6.7 |
| CH-04 | P0 | PARTIAL | Exact refuse string in prompt; “suggest related sections” not implemented |
| CH-05 | P0 | PARTIAL | Backend SSE exists; authenticated workspace uses `demoAnswerStream` |
| CH-06–CH-07 | P0 | PARTIAL | Citation UI + sources panel in demo; not wired to live thread citations consistently |
| CH-08 | P0 | PARTIAL | Stop aborts client stream; backend `stopped` flag not set in live path |
| CH-09 | P1 | PARTIAL | UI regenerate + backend flag; not end-to-end on real threads |
| CH-10 | P1 | DONE (UI) | Copy button |
| CH-11 | P1 | PARTIAL | Fixed suggested questions; not generated at ingest / opt-in |
| CH-12 | P0 | TODO | No Markdown renderer / rehype-sanitize |
| CH-13 | P0 | PARTIAL | Backend supports multi-thread; UI does not |
| CH-14 | P1 | PARTIAL | Backend rename/delete; UI incomplete |
| CH-15 | P0 | DONE | 1000-char limit enforced |
| CH-16 | P0 | PARTIAL | Backend persists messages/citations; UI demo does not |

### 5.5 History (HI)

| ID | Priority | Status | Notes |
| --- | --- | --- | --- |
| HI-01 | P0 | PARTIAL | History page + API list; demo fallback without auth |
| HI-02 | P1 | PARTIAL | Title search on API; **message text** search missing |
| HI-03 | P0 | DONE (backend) | First question → title ≤60 |
| HI-04 | P1 | PARTIAL | Backend Markdown export; UI only when API threads load |
| HI-05 | P0 | DONE (schema) | No TTL deletion |

### 5.6 Providers / keys (PK)

| ID | Priority | Status | Notes |
| --- | --- | --- | --- |
| PK-01 | P0 | DONE | providers.json: groq, cerebras, novita, huggingface |
| PK-02–PK-03 | P0 | PARTIAL | Settings UI; workspace header switcher incomplete vs PRD |
| PK-04 | P0 | PARTIAL | Backend test-key route; UI not fully wired |
| PK-05 | P0 | PARTIAL | Header transport in `api.js`; needs E2E with Clerk |
| PK-06–PK-07 | P0 | PARTIAL | Backend remember/delete; Settings mostly sessionStorage demo |
| PK-08 | P0 | PARTIAL | ProviderError maps rate limits; UI messaging incomplete |
| PK-09 | P1 | PARTIAL | Backend stores last4; UI masking incomplete |
| PK-10 | P1 | TODO | No guided switch-and-retry UX |

### 5.7 Settings (ST)

| ID | Priority | Status | Notes |
| --- | --- | --- | --- |
| ST-01 | P0 | TODO | No Clerk profile |
| ST-02 | P0 | PARTIAL | Theme buttons exist; **no light CSS tokens / no FOUC-safe boot script** |
| ST-03 | P0 | PARTIAL | Backend me settings; UI partial |
| ST-04 | P0 | TODO | Delete chats/docs/account not implemented end-to-end |
| ST-05 | P1 | PARTIAL | Backend usage on `/me`; UI incomplete |

### 5.8 Limits (LM)

| ID | Priority | Status | Notes |
| --- | --- | --- | --- |
| LM-01–LM-05, LM-07 | P0 | PARTIAL | Backend settings + ingest/usage checks; need E2E tests |
| LM-06 | P0 | DONE | Public middleware 30/min/IP |
| LM-08 | P1 | DONE | Limits from Settings / env |

### 5.9 Demo (DM)

| ID | Priority | Status | Notes |
| --- | --- | --- | --- |
| DM-01 | P0 | DONE | Sample report + `/try` |
| DM-02 | P0 | DONE | Sample path does not increment user daily usage |
| DM-03 | P1 | PARTIAL | IP daily=5 + optional `FOLIO_SAMPLE_GROQ_KEY`; offline lexical answer if unset (acceptable) |

---

## A3. Architecture check

| Question | Finding |
| --- | --- |
| FastAPI factory? | **Yes** — `create_app()` in `main.py` |
| Routes by domain? | **Yes** — documents, threads, me, providers, sample, health |
| Dependency injection? | **Mixed** — FastAPI `Depends` for user/session/settings; also module globals for engine and embedding model |
| Service layer? | **Weak** — only `services/usage.py`; routes contain SQL + RAG orchestration (`threads.ask_question` ~165 lines) |
| DB sessions per request? | **Yes** — `get_session` yields session, commits/rolls back |
| Consistent errors? | **No** — FastAPI `detail={code,message}` vs PRD `{"error":{code,message,retry_after}}` |
| Config in one place? | **Mostly** — `Settings`; still raw `os.getenv` in `main.py`, `db.py`, `embed.py`, `sample.py` |
| RAG vs HTTP boundary? | **Partial** — `rag/` is importable, but routes call retrieve/generate/session SQL directly; generate imports provider catalog |

**Verdict:** Functional skeleton, not yet the Part B package boundaries (`api/`, `services/`, `repositories/`, `errors.py`, `deps.py`, provider adapters).

---

## A4. Code health

### Dead / unused

| Item | Evidence |
| --- | --- |
| `slowapi` dependency | Never imported; custom rate limiter used |
| `frontend/public/*.svg` (next/vercel/globe/…) | Unused template assets |
| Alias pages `/workspace`, `/admin`, `/settings` | Extra vs PRD §7.1; admin portal not in PRD |
| `scripts/inspect_db_url.py` | One-off helper |
| depcheck (noisy) | Flagged `@tailwindcss/postcss`, `tailwindcss`, `eslint-config-next` as unused — **false positives** (used via PostCSS/ESLint config) |

### Ruff F401/F811/F841

`ruff check backend --select F401,F811,F841` → **clean**.

### Long functions (>60 lines)

| Location | Lines |
| --- | --- |
| `routes/threads.py::ask_question` | ~165 |
| `routes/sample.py::ask_sample` | ~101 |
| `rag/ingest.py::ingest_document` | ~84 |
| `rag/generate.py::stream_chat_completion` | ~79 |
| nested `event_stream` in threads | ~75 |

### Duplication

- Demo answer / sample offline answer / seed workspace answer (same margin narrative).
- Client history/library demo fallbacks duplicated patterns.
- Error raising pattern repeated in every route (should be `errors.py`).

### Secrets in repo

- No real API keys found in tracked source.
- Test fixture string `gsk_test_secret_key` in `test_crypto.py` (harmless).
- `.env.local` gitignored (contains live Neon URL — do not commit).

### Type hints

Public Python APIs generally annotated; async route handlers typed. Gaps are minor (`lifespan` return). **mypy not configured.**

---

## A5. Security check (PRD §6.8)

| Requirement | Status |
| --- | --- |
| HTTPS via Vercel | Assumed at deploy; N/A locally |
| Clerk JWT signature + expiry | PARTIAL — JWKS + exp/sub; **audience & issuer not verified** |
| Provider keys header-only | PARTIAL — designed correctly; remember path encrypts at rest |
| AES-256-GCM unique 12-byte nonce | DONE |
| Master key from env | DONE (`FOLIO_ENCRYPTION_KEY`) |
| Logging filter for key fields | DONE |
| Pydantic body validation | DONE on typed routes |
| File signature + size + pages | DONE in validate/ingest |
| Markdown sanitization (rehype-sanitize) | **MISSING** |
| CORS to app origin | DONE via Settings |
| Prompt injection rule 5 | DONE in system prompt |
| Security headers in next.config | DONE (CSP, XFO, Referrer-Policy) |
| pip-audit / npm audit in CI | **MISSING** |
| Rate limits LM-01–07 | PARTIAL (backend present; not fully E2E tested) |

---

## A6. Performance check (PRD §6.9)

| Requirement | Status |
| --- | --- |
| Embedding model loaded once per process | DONE — `@lru_cache` + lock in `embed.py`; Vercel cache `/tmp/fastembed` |
| HNSW on `document_chunks` | DONE — in `001_initial.sql` (applied on Neon) |
| Stream starts before full response | DONE (backend SSE); UI demo also streams |
| Workspace JS ≤ 180 KB gzipped | **LIKELY OK** — Next “First Load JS” for `/app` ~127 KB; largest shared chunk gzip ~89 KB (measure more precisely in Part D) |
| TTFT < 1.5s warm (excl. provider) | **NOT MEASURED** |
| 10 MB / 100-page ingest ≤ 25s | **NOT MEASURED** |
| Warm cron every 5 min on `/api/health` | **MISSING** from `vercel.json` |

---

## A7. Deployment check

| Check | Status |
| --- | --- |
| `vercel.json` routes `/api/(.*)` → `/api/index` | DONE |
| Python runtime 3.12, maxDuration 60, `includeFiles: backend/**` | DONE |
| **Python bundle size** | **AT RISK / OVER** — local full `site-packages` ≈ **263.5 MB** (limit **250 MB** unzipped). Selected heavy deps alone ≈ **161 MB** (onnxruntime ~46, numpy ~53 with libs, sqlalchemy ~17, cryptography ~9, llama_index ~8, …). Embedding **weights** intentionally excluded (download to `/tmp`). **PRD §6.3 fallback (HF feature-extraction) is likely needed** after a real Vercel build measure. |
| Env vars from `.env.example` read in code | DONE for listed vars via Settings / migrate / sample |
| Documented setup | PARTIAL — README has Neon notes; Clerk E2E steps incomplete |

---

## Prioritized work list (Blockers → Correctness → Cleanup → Polish)

### Blockers (must before claiming P0 done)

1. **Clerk end-to-end (AU-01–AU-04):** install Clerk, protect `/app/*`, verify JWT with **aud + iss**, wire session token to `apiFetch`.
2. **Wire authenticated workspace to real APIs (CH/DU core):** replace demo stream with threads/messages SSE; upload → real `POST /api/documents`; document/thread routes from PRD §7.1 (`/app/documents/[id]`, `/app/threads/[id]`).
3. **Python function size / embeddings (deploy):** measure real Vercel unzipped size; if >250 MB, implement §6.3 HF embedding fallback and keep model out of bundle.
4. **Unified error contract:** `{"error":{"code","message","retry_after"}}` everywhere + frontend mapping.

### Correctness

5. JWT audience/issuer; stop generation → persist `stopped=true`.
6. Markdown answers + **rehype-sanitize** (CH-12).
7. Theme: light + system tokens + **inline script before first paint** (ST-02 / §7.5).
8. Data controls & account deletion (ST-04, AU-05).
9. Limits E2E tests (LM-01–07) including daily_limit / invalid_key UX.
10. HI-02 message-text search; DU-11 retry; CH-04 related-section suggestions.
11. Provider test-key / remember / mask fully in Settings (PK-04–PK-09).

### Cleanup (Part B)

12. Restructure to `api/`, `services/`, `repositories/`, `errors.py`, `deps.py`, `providers/` adapters (LlamaIndex OpenAI-like LLM).
13. Remove unused `slowapi`, unused public SVGs, decide fate of `/admin` (not in PRD — remove or mark out-of-scope).
14. Split long route handlers; eliminate `os.getenv` outside Settings.
15. Frontend `lib/api/*` modules; no raw `fetch` in components.

### Polish

16. Landing alignment to PRD §9.6; Lighthouse ≥90 (LP-09).
17. Warm cron on `/api/health`; TTFT measurement.
18. Vitest + Playwright + axe; pip-audit/npm audit in CI; mypy on rag/services/security.
19. Local Python 3.12 alignment with CI.
20. Add missing design/spec files to repo or document where they live.

---

## Test snapshot (current)

- Backend: **24 passed** (pytest), **ruff clean** (incl. F401/F811/F841).
- Frontend: **build passes**; no unit/e2e suite.
- Neon: migrations applied; `/api/health` returns `database=ok`, `schema=ready` when API runs with `.env.local`.

---

**Part A complete.** Per instructions, **Part B will not start until you review this prioritized list.** Reply to proceed with Part B (or adjust priorities / scope, e.g. keep Admin out-of-scope).

---

## Part B status (architecture cleanup)

Completed after approval. Admin portal removed (out of PRD §7.1). Tests: **26 passed**. Frontend build: **pass**.

### Move table (old → new)

| Old location | New location | Reason |
| --- | --- | --- |
| Ad-hoc `HTTPException(detail={…})` | `backend/app/errors.py` + `{"error":{code,message,retry_after}}` | Single error contract |
| `backend/app/routes/*` | `backend/app/api/*` | HTTP routers only |
| SQL / ask orchestration in routes | `backend/app/services/*` + `repositories/*` | Business logic / SQL boundaries |
| `backend/app/providers.py` | `backend/app/providers/` (`catalog`, `openai_compatible`) | Provider adapter interface |
| `os.getenv` in main/db/embed/sample | Mostly `Settings` | Config in one place |
| `frontend/lib/api.js` only | `frontend/lib/api/{client,documents,threads,me}.js` | Per-area API modules |
| Dark-only CSS | `[data-theme=light\|dark]` + boot script in `layout.js` | FOUC-safe themes |
| `slowapi` dep | removed | Unused |
| Template `public/*.svg`, Admin UI | removed | Dead / out of PRD |
| JWT verify without aud/iss | Optional `CLERK_JWT_AUDIENCE` / `CLERK_JWT_ISSUER` | PRD §6.8 |
