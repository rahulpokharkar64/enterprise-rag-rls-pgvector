-- 01_extensions.sql
-- Run as SUPERUSER on the target DB. Requires pgvector binaries installed into PostgreSQL 16.
CREATE EXTENSION IF NOT EXISTS vector;

-- Show installed version (expect 0.5+ for HNSW support)
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
