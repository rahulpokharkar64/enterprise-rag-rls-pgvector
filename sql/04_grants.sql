-- 04_grants.sql
-- Run as the INGESTION role. Least privilege for the reader role.

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA rag FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA rag FROM PUBLIC;

GRANT USAGE ON SCHEMA rag TO :"reader_user";

-- Reader may only SELECT documents and chunks (rows filtered by RLS).
GRANT SELECT ON rag.documents, rag.chunks TO :"reader_user";

-- Needed by the RLS policies
GRANT EXECUTE ON FUNCTION rag.can_read_doc(text), rag.current_app_user() TO :"reader_user";

-- Deliberately NOT granted to reader: groups, app_users, user_groups, document_groups.
