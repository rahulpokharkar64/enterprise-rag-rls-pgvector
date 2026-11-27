-- 02_schema.sql
-- Run as the INGESTION role (owner). Creates schema 'rag' and all tables.

CREATE SCHEMA IF NOT EXISTS rag;
SET search_path = rag, public;

-- Access groups (departments + shared)
CREATE TABLE IF NOT EXISTS rag.groups (
    group_id      smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    group_key     text NOT NULL UNIQUE,           -- application | platform | security | shared
    display_name  text NOT NULL
);

-- Application identities (NOT database logins). Resolved from app.current_user.
CREATE TABLE IF NOT EXISTS rag.app_users (
    user_id       integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username      text NOT NULL UNIQUE CHECK (username = lower(username)),
    display_name  text NOT NULL,
    is_active     boolean NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- Group membership: revoke = DELETE a row here (no re-embedding needed)
CREATE TABLE IF NOT EXISTS rag.user_groups (
    user_id    integer  NOT NULL REFERENCES rag.app_users(user_id) ON DELETE CASCADE,
    group_id   smallint NOT NULL REFERENCES rag.groups(group_id)   ON DELETE CASCADE,
    granted_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, group_id)
);

-- Source documents with full attribution
CREATE TABLE IF NOT EXISTS rag.documents (
    doc_id        text PRIMARY KEY,               -- e.g. app-001
    title         text NOT NULL,
    source_path   text NOT NULL UNIQUE,           -- content/en/docs/concepts/...
    source_url    text NOT NULL,                  -- https://kubernetes.io/docs/...
    access_class  text NOT NULL CHECK (access_class IN ('application','platform','security','shared')),
    license       text NOT NULL DEFAULT 'CC BY 4.0',
    sha256        text,
    char_len      integer,
    ingested_at   timestamptz NOT NULL DEFAULT now()
);

-- Which groups may read a document (many-to-many, extensible)
CREATE TABLE IF NOT EXISTS rag.document_groups (
    doc_id    text     NOT NULL REFERENCES rag.documents(doc_id) ON DELETE CASCADE,
    group_id  smallint NOT NULL REFERENCES rag.groups(group_id)  ON DELETE CASCADE,
    PRIMARY KEY (doc_id, group_id)
);

-- Chunks for every strategy, each traceable to file + heading
CREATE TABLE IF NOT EXISTS rag.chunks (
    chunk_id      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    doc_id        text NOT NULL REFERENCES rag.documents(doc_id) ON DELETE CASCADE,
    strategy      text NOT NULL CHECK (strategy IN ('fixed','recursive','markdown','semantic')),
    seq           integer NOT NULL,               -- order within doc for this strategy
    heading_path  text,                           -- e.g. "Deployments > Scaling a Deployment"
    content       text NOT NULL,
    char_len      integer NOT NULL,
    embedding     vector(384) NOT NULL,           -- BAAI/bge-small-en-v1.5
    created_at    timestamptz NOT NULL DEFAULT now(),
    UNIQUE (doc_id, strategy, seq)
);

-- Indexes
CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
    ON rag.chunks USING hnsw (embedding vector_cosine_ops);   -- cosine distance (<=>)
CREATE INDEX IF NOT EXISTS chunks_strategy_idx       ON rag.chunks (strategy);
CREATE INDEX IF NOT EXISTS chunks_doc_idx            ON rag.chunks (doc_id);
CREATE INDEX IF NOT EXISTS document_groups_group_idx ON rag.document_groups (group_id);
CREATE INDEX IF NOT EXISTS user_groups_group_idx     ON rag.user_groups (group_id);
