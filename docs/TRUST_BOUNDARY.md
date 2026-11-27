# Trust boundary & database roles

## Enforcement point
Permissions are enforced by **PostgreSQL Row-Level Security** on `rag.documents` and `rag.chunks`.
The similarity search runs as `rag_reader`, so PostgreSQL removes unauthorised rows **inside the query**.
They are never ranked, returned to Python, or passed to an LLM.
No department label check or post-retrieval filter is used as the security boundary.

```
 User --> [Trusted backend: verifies identity] --> rag_reader session
                                                   SET LOCAL app.current_user = '<verified>'
                                                          |
                                         PostgreSQL RLS: can_read_doc(doc_id)
                                         (document_groups JOIN user_groups)
                                                          |
                                       only authorised chunks --> (optional) LLM
```

## Roles
| Role | Login | Privileges | Used by |
|---|---|---|---|
| `postgres` (superuser) | yes | everything | `db_docker.ps1` (or `setup_db.ps1`) only, never by Python |
| `ingest_admin` | yes | owns schema `rag`, all tables; writes data | `src/ingest.py` (trusted batch job) |
| `rag_reader` | yes | `SELECT` on `documents`, `chunks` only; `NOBYPASSRLS`; no access to membership tables | `src/retrieve.py` |

## Policy
```sql
CREATE POLICY chunks_read_by_group ON rag.chunks FOR SELECT TO rag_reader
USING (rag.can_read_doc(doc_id));
```
`can_read_doc()` is `SECURITY DEFINER` and returns true only if the current identity
(`current_setting('app.current_user')`) is an **active** user in a group linked to the document.
- Unknown or empty identity -> no match -> **0 rows**.
- Revoking access = `DELETE FROM rag.user_groups ...` -> takes effect on the next query. No re-embedding.
- No INSERT/UPDATE/DELETE policy or grant for the reader -> writes are denied.

## Identity
`app.current_user` is set with `set_config(..., is_local => true)` inside one transaction, so it cannot leak to a pooled connection.

**Demo limitation:** the `--user` CLI flag *simulates* a verified identity. Anyone holding the `rag_reader` password could set any name.
In production:
- A trusted backend sets the identity from a verified OIDC/JWT token, never from user input.
- End users never receive database credentials.
- Credentials are kept in a secret store, not in `.env`.
- Optionally, use one database role per tenant, or sign the identity claim and verify it in the DB.
