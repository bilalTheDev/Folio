# Folio — Deployment checklist (Phase 10)

This is a readiness checklist, not a deployment. Work through each section before the first
production release.

## 1. Backend (FastAPI, Docker)

The image is defined in [`backend/Dockerfile`](../backend/Dockerfile).

```bash
cd backend
docker build -t folio-api .
docker run --rm -p 8000:8000 --env-file .env.production \
  -v folio-storage:/data/storage -v folio-models:/srv/.cache folio-api
```

- [ ] `requirements.txt` is regenerated from a clean venv (`pip freeze > requirements.txt`) and the
      image builds from it.
- [ ] Run as a single worker (`uvicorn` default) or put the rate limiter on shared storage first:
      `slowapi` currently counts in process memory, and Chroma's on-disk stores expect one writer
      process per user directory.
- [ ] Mount a **persistent volume** at `/data/storage` (uploads + per-user Chroma indexes) and at
      `/srv/.cache` (the fastembed model, ~70 MB, downloaded on first start). Without them every
      restart loses all indexes.
- [ ] Back up `/data/storage` together with MongoDB; the two must stay consistent (documents
      reference files and index entries by id).
- [ ] TLS terminates at the load balancer / platform; uvicorn runs with `--proxy-headers` so client
      IPs used by the rate limiter come from `X-Forwarded-For`. Restrict `--forwarded-allow-ips` to
      the proxy's address range if the platform documents it.
- [ ] The proxy's request body limit is at least 11 MB (10 MB file + multipart overhead). The API
      itself rejects anything larger with 413.
- [ ] Health check: `GET /health` returns `{"status": "ok"}`.
- [ ] Logs: the app redacts `hf_…` tokens and bearer credentials from every log record. Do not
      enable request-body logging at the proxy for `/users/me/hf-token` or `/auth/*`.
- [ ] `APP_ENV=production` disables the interactive docs (`/docs`, `/openapi.json`).

## 2. Frontend (Next.js, Vercel-style hosting)

- [ ] Set `NEXT_PUBLIC_API_URL` to the public HTTPS API origin and `NEXT_PUBLIC_MAX_UPLOAD_BYTES=10485760`.
- [ ] `npm ci && npm run build` succeeds (`cacheComponents` is on, so client hooks that read the URL
      must sit inside `Suspense`; the build fails loudly if one does not).
- [ ] Production domain decided **before** setting backend CORS and cookie options (below).

## 3. Cookies and CORS (must match the hosting layout)

| Layout | `CORS_ORIGIN` | `COOKIE_SECURE` | `COOKIE_SAMESITE` |
|---|---|---|---|
| Same site, e.g. `app.folio.com` + `api.folio.com` | `https://app.folio.com` | `true` | `lax` |
| Different sites, e.g. `folio.vercel.app` + `folio-api.fly.dev` | `https://folio.vercel.app` | `true` | `none` |

- [ ] `CORS_ORIGIN` is exactly one origin (scheme + host, no trailing slash, no wildcard).
- [ ] Prefer the same-site layout: some browsers block third-party cookies, which breaks the refresh
      cookie in the cross-site layout.

## 4. MongoDB: local Compass → Atlas

1. Create an Atlas cluster (M10+ for production; M0 is fine for staging) in the same region as the API.
2. Create a database user with `readWrite` on the `folio` database only.
3. Network access: allow the API's egress IPs (avoid `0.0.0.0/0`).
4. Migrate local data if needed:
   ```bash
   mongodump --uri "mongodb://localhost:27017" --db folio --out ./dump
   mongorestore --uri "mongodb+srv://<user>:<password>@<cluster>/" --nsInclude "folio.*" ./dump
   ```
   Copy `backend/storage/` to the production volume at the same time, or reindex every document.
5. Set `MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>/?retryWrites=true&w=majority`.
6. Indexes are created automatically at API startup (`ensure_indexes`): unique `users.email`, plus
   `user_id`/`session_id` compound indexes on the other collections.
7. Enable Atlas backups (continuous or daily snapshots).
8. In Compass, connect with the same `mongodb+srv://` string to inspect production read-only.

## 5. Production environment variables

### Backend

| Variable | Production value / rule |
|---|---|
| `APP_ENV` | `production` |
| `MONGODB_URI` | Atlas SRV string (secret) |
| `MONGODB_DB_NAME` | `folio` |
| `JWT_SECRET` | New random 64+ chars (secret) — never reuse dev values |
| `JWT_REFRESH_SECRET` | Different random 64+ chars (secret) |
| `JWT_ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` |
| `REFRESH_COOKIE_NAME` | `folio_refresh` |
| `COOKIE_SECURE` | `true` |
| `COOKIE_SAMESITE` | `lax` or `none` (see §3) |
| `ENCRYPTION_KEY` | New Fernet key (secret). **Losing it makes every saved HF token unreadable**; store it in a secrets manager and back it up. |
| `CORS_ORIGIN` | The frontend's HTTPS origin |
| `STORAGE_DIR` | `/data/storage` (set by the Dockerfile) |
| `MAX_UPLOAD_BYTES` | `10485760` (cannot be raised above 10 MB) |
| `EMBED_MODEL` | `BAAI/bge-small-en-v1.5` (changing it requires reindexing everything) |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `512` / `50` |
| `RETRIEVAL_TOP_K` | `5` |
| `HF_ROUTER_BASE_URL` | `https://router.huggingface.co/v1` |
| `LLM_TIMEOUT_SECONDS` | `60` |
| `RATE_LIMIT_AUTH` / `RATE_LIMIT_UPLOAD` / `RATE_LIMIT_CHAT` | e.g. `10/minute`, `20/minute`, `30/minute` |

Generate secrets:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Frontend

| Variable | Production value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://api.<your-domain>` |
| `NEXT_PUBLIC_MAX_UPLOAD_BYTES` | `10485760` |

## 6. Pre-release verification

- [ ] `cd backend && pytest` passes against a disposable database (it uses `folio_test` and drops it).
- [ ] Upload an 11 MB file → 413; a 10 MB file → accepted.
- [ ] Save an HF token, then search API responses and logs for it: only `hf_****1234` appears.
- [ ] Two test accounts with different documents cannot retrieve each other's passages
      (`tests/test_rag.py::test_retrieval_never_crosses_users`).
- [ ] Hitting `/auth/signin` repeatedly returns 429 after the configured limit.
- [ ] Re-check the provider/model allowlist in `backend/app/services/providers.py` against
      `GET https://router.huggingface.co/v1/models`; providers drop models over time.
