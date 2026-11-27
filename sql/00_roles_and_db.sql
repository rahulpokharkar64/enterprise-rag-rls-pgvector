-- 00_roles_and_db.sql
-- Run as SUPERUSER against the 'postgres' maintenance DB (by db_docker.ps1 / setup_db.ps1).
-- psql variables: db_name, ingest_user, ingest_pw, reader_user, reader_pw
-- Idempotent: safe to re-run; passwords are re-applied from .env.

-- Ingestion role: owns all objects, loads data. Trusted backend job only.
SELECT format('CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS', :'ingest_user')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'ingest_user') \gexec

-- Reader role: used by the retrieval path. Cannot bypass RLS, cannot write.
SELECT format('CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS', :'reader_user')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'reader_user') \gexec

-- (Re)apply passwords from .env
SELECT format('ALTER ROLE %I PASSWORD %L', :'ingest_user', :'ingest_pw') \gexec
SELECT format('ALTER ROLE %I PASSWORD %L', :'reader_user', :'reader_pw') \gexec

-- Database owned by the ingestion role
SELECT format('CREATE DATABASE %I OWNER %I ENCODING ''UTF8''', :'db_name', :'ingest_user')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'db_name') \gexec

-- Lock down: only our two roles may connect
SELECT format('REVOKE ALL ON DATABASE %I FROM PUBLIC', :'db_name') \gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', :'db_name', :'reader_user') \gexec
