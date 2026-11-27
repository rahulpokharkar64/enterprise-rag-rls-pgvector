-- 10_retrieval_query.sql  (reference query - Exercise B)
-- The exact query used by src/retrieve.py. Run as rag_reader so RLS applies.
-- :'q_vec' = query embedding as '[0.01, ...]' (384 dims), :'username', :'strategy', :k
--
-- Example in psql:
--   \set username priya
--   \set strategy markdown
--   \set k 5
--   \set q_vec '[...]'
BEGIN;
SELECT set_config('app.current_user', :'username', true);   -- transaction-local identity

SELECT c.doc_id,
       d.title,
       c.heading_path,
       c.seq,
       d.access_class,
       d.source_url,
       round((c.embedding <=> :'q_vec'::vector)::numeric, 4) AS cosine_distance,
       left(c.content, 160)                                 AS preview
FROM   rag.chunks    c
JOIN   rag.documents d USING (doc_id)          -- both tables filtered by RLS
WHERE  c.strategy = :'strategy'
ORDER  BY c.embedding <=> :'q_vec'::vector     -- HNSW index, cosine distance
LIMIT  :k;
COMMIT;
