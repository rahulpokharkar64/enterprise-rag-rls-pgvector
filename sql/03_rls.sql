-- 03_rls.sql
-- Run as the INGESTION role. Row-Level Security = the enforcement boundary.
-- Identity comes from the session setting  app.current_user  set by the trusted backend
-- (src/db.py) inside each transaction. Unknown/empty identity => zero rows.
SET search_path = rag, public;

-- Current application identity (NULL if not set)
CREATE OR REPLACE FUNCTION rag.current_app_user() RETURNS text
LANGUAGE sql STABLE
AS $$ SELECT nullif(lower(current_setting('app.current_user', true)), '') $$;

-- Membership check. SECURITY DEFINER so the reader role never needs
-- direct access to user_groups / app_users / document_groups.
CREATE OR REPLACE FUNCTION rag.can_read_doc(p_doc_id text) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = rag, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM rag.document_groups dg
        JOIN rag.user_groups     ug ON ug.group_id = dg.group_id
        JOIN rag.app_users       u  ON u.user_id   = ug.user_id
        WHERE dg.doc_id  = p_doc_id
          AND u.is_active
          AND u.username = rag.current_app_user()
    )
$$;

REVOKE ALL ON FUNCTION rag.can_read_doc(text)  FROM PUBLIC;
REVOKE ALL ON FUNCTION rag.current_app_user() FROM PUBLIC;

-- Enable RLS. Not FORCED: the owner (ingestion role) must load all rows.
-- The reader role is NOT the owner and has NOBYPASSRLS, so it is always filtered.
ALTER TABLE rag.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag.chunks    ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS documents_read_by_group ON rag.documents;
CREATE POLICY documents_read_by_group ON rag.documents
    FOR SELECT TO :"reader_user"
    USING (rag.can_read_doc(doc_id));

DROP POLICY IF EXISTS chunks_read_by_group ON rag.chunks;
CREATE POLICY chunks_read_by_group ON rag.chunks
    FOR SELECT TO :"reader_user"
    USING (rag.can_read_doc(doc_id));
-- No INSERT/UPDATE/DELETE policies for the reader => all writes denied.
