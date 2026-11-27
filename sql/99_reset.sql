-- 99_reset.sql  (DESTRUCTIVE - used only by setup_db.ps1 -Reset; Docker uses db_docker.ps1 -Action reset)
-- Run as SUPERUSER against 'postgres'.
SELECT format('DROP DATABASE IF EXISTS %I WITH (FORCE)', :'db_name') \gexec
SELECT format('DROP ROLE IF EXISTS %I', :'reader_user') \gexec
SELECT format('DROP ROLE IF EXISTS %I', :'ingest_user') \gexec
