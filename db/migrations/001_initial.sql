-- Folio initial schema (Neon Postgres + pgvector)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
  id            TEXT PRIMARY KEY,
  email         TEXT NOT NULL,
  display_name  TEXT,
  theme         TEXT NOT NULL DEFAULT 'system' CHECK (theme IN ('dark','light','system')),
  default_provider TEXT NOT NULL DEFAULT 'groq',
  default_model TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS documents (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title         TEXT NOT NULL,
  file_type     TEXT NOT NULL CHECK (file_type IN ('pdf','docx','txt')),
  byte_size     INTEGER NOT NULL,
  page_count    INTEGER NOT NULL,
  chunk_count   INTEGER NOT NULL DEFAULT 0,
  status        TEXT NOT NULL CHECK (status IN ('queued','extracting','embedding','ready','failed')),
  failure_reason TEXT,
  is_sample     BOOLEAN NOT NULL DEFAULT false,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS documents_user_idx ON documents(user_id);

CREATE TABLE IF NOT EXISTS document_chunks (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id   UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index   INTEGER NOT NULL,
  page          INTEGER NOT NULL,
  content       TEXT NOT NULL,
  token_count   INTEGER NOT NULL,
  embedding     VECTOR(384) NOT NULL
);
CREATE INDEX IF NOT EXISTS chunks_doc_idx ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
  ON document_chunks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS threads (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  document_id   UUID REFERENCES documents(id) ON DELETE SET NULL,
  title         TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS threads_user_idx ON threads(user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS messages (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  thread_id     UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
  role          TEXT NOT NULL CHECK (role IN ('user','assistant')),
  content       TEXT NOT NULL,
  provider      TEXT,
  model         TEXT,
  stopped       BOOLEAN NOT NULL DEFAULT false,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS messages_thread_idx ON messages(thread_id, created_at);

CREATE TABLE IF NOT EXISTS citations (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id    UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
  marker        INTEGER NOT NULL,
  chunk_id      UUID REFERENCES document_chunks(id) ON DELETE SET NULL,
  page          INTEGER NOT NULL,
  excerpt       TEXT NOT NULL,
  score         REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS provider_keys (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider      TEXT NOT NULL CHECK (provider IN ('groq','cerebras','novita','huggingface')),
  key_ciphertext BYTEA NOT NULL,
  key_nonce     BYTEA NOT NULL,
  key_last4     TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, provider)
);

CREATE TABLE IF NOT EXISTS usage_daily (
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  day           DATE NOT NULL,
  questions     INTEGER NOT NULL DEFAULT 0,
  uploads       INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, day)
);
