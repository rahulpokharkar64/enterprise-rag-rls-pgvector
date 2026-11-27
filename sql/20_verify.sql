-- 20_verify.sql
-- Read-only health check of the k8s_rag database. Run as SUPERUSER on the target DB.
-- Prints one row per check: check | ok | detail.  Used by scripts\db_docker.ps1 -Action verify.
-- psql variables: ingest_user, reader_user

WITH checks(check_name, ok, detail) AS (
    SELECT 'extension vector',
           EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector'),
           coalesce((SELECT extversion FROM pg_extension WHERE extname = 'vector'), 'missing')
UNION ALL
    SELECT 'schema rag',
           EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'rag'), ''
UNION ALL
    SELECT 'table rag.' || t,
           to_regclass('rag.' || t) IS NOT NULL, ''
    FROM unnest(ARRAY['groups','app_users','user_groups','documents','document_groups','chunks']) AS t
UNION ALL
    SELECT 'column chunks.embedding vector(384)',
           EXISTS (SELECT 1 FROM pg_attribute a
                   WHERE a.attrelid = to_regclass('rag.chunks') AND a.attname = 'embedding'
                     AND format_type(a.atttypid, a.atttypmod) = 'vector(384)'), ''
UNION ALL
    SELECT 'index chunks_embedding_hnsw',
           to_regclass('rag.chunks_embedding_hnsw') IS NOT NULL, ''
UNION ALL
    SELECT 'RLS enabled on rag.' || t,
           coalesce((SELECT relrowsecurity FROM pg_class WHERE oid = to_regclass('rag.' || t)), false), ''
    FROM unnest(ARRAY['documents','chunks']) AS t
UNION ALL
    SELECT 'policy ' || p,
           EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'rag' AND policyname = p), ''
    FROM unnest(ARRAY['documents_read_by_group','chunks_read_by_group']) AS p
UNION ALL
    SELECT 'function rag.can_read_doc',
           to_regprocedure('rag.can_read_doc(text)') IS NOT NULL, ''
UNION ALL
    SELECT 'role ' || :'ingest_user',
           EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'ingest_user' AND rolcanlogin), ''
UNION ALL
    SELECT 'role ' || :'reader_user' || ' NOBYPASSRLS',
           EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'reader_user'
                   AND rolcanlogin AND NOT rolbypassrls AND NOT rolsuper), ''
UNION ALL
    SELECT 'reader SELECT on rag.chunks',
           CASE WHEN to_regclass('rag.chunks') IS NULL THEN false
                ELSE has_table_privilege(:'reader_user', 'rag.chunks', 'SELECT') END, ''
UNION ALL
    SELECT 'reader blocked from rag.user_groups',
           CASE WHEN to_regclass('rag.user_groups') IS NULL THEN false
                ELSE NOT has_table_privilege(:'reader_user', 'rag.user_groups', 'SELECT') END, ''
UNION ALL
    SELECT 'groups seeded (4)',
           CASE WHEN to_regclass('rag.groups') IS NULL THEN false
                ELSE (SELECT count(*) FROM rag.groups) = 4 END, ''
UNION ALL
    SELECT 'demo users seeded (4)',
           CASE WHEN to_regclass('rag.app_users') IS NULL THEN false
                ELSE (SELECT count(*) FROM rag.app_users) = 4 END, ''
UNION ALL
    SELECT 'memberships seeded (>=9)',
           CASE WHEN to_regclass('rag.user_groups') IS NULL THEN false
                ELSE (SELECT count(*) FROM rag.user_groups) >= 9 END, ''
)
SELECT check_name AS check, CASE WHEN ok THEN 'PASS' ELSE 'FAIL' END AS result, detail
FROM checks;

-- Informational (not pass/fail): data loaded by later phases
SELECT 'documents' AS item, CASE WHEN to_regclass('rag.documents') IS NULL THEN 0
                                 ELSE (SELECT count(*) FROM rag.documents) END AS rows
UNION ALL
SELECT 'chunks',    CASE WHEN to_regclass('rag.chunks') IS NULL THEN 0
                         ELSE (SELECT count(*) FROM rag.chunks) END;
