<!-- Auto-loaded by GitHub Copilot. Source of truth: docs/AI_ASSISTANT_GUIDE.md (keep both in sync). -->
# AI Assistant Guide – enterprise-rag-rls-pgvector

> For VS Code AI assistants (GitHub Copilot Chat, Amazon Q, Cursor, Continue, etc.).
> Read this **before** suggesting or editing code in this repository.
> A copy lives at `.github/copilot-instructions.md`, which Copilot loads automatically.

## 1. Project scope (what this repo is)
A **Week 7 homework** that builds a secure enterprise RAG retrieval layer:
1. Ingest **30 Kubernetes docs** (10 workloads → application, 10 storage → platform, 5 security → security, 5 overview → shared).
2. Compare **4 chunking strategies**: fixed, recursive, markdown, semantic.
3. Embed with **`BAAI/bge-small-en-v1.5`** (384-dim) into **PostgreSQL 16 + pgvector** (Docker Desktop).
4. Enforce department access with **PostgreSQL Row-Level Security**, inside the SQL query, before any LLM.
5. Prove it with a test matrix (Exercise D) and negative / revocation tests (Exercise E).

**Out of scope:** LLM answer generation, web UI, real authentication, cloud deployment. Don't add these unless asked.

## 2. Environment facts
| Item | Value |
|---|---|
| OS | Windows 10/11, PowerShell 5.1 **and** 7 must both work |
| Python | **3.12**, venv at `.venv\` |
| Database | Docker Desktop (WSL2, Linux containers), image `pgvector/pgvector:pg16`, container `k8s-rag-pg`, volume `k8s-rag-pgdata` |
| Host / port | `127.0.0.1:5432` (use `127.0.0.1`, not `localhost`, to avoid IPv6 `::1`) |
| DB name | `k8s_rag`, schema `rag` |
| Config | `.env` (git-ignored) loaded by `src/config.py`; template `.env.example` |
| Logs | `logs/app.log` (Python), `logs/*.log` (PowerShell transcripts) |
| Evidence | `evidence/` (generated), `evidence/screenshots/` |

## 3. Run order (never skip or reorder)
```powershell
Copy-Item .env.example .env                                     # then set the 3 passwords
powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1 -Preflight
powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1
```
Manual equivalent:
| # | Command | Depends on |
|---|---|---|
| 0 | `scripts\setup_venv.ps1 -CpuTorch` | Python 3.12 |
| 1 | `scripts\db_docker.ps1` (ensure) | Docker running, `.env` |
| 1b | `python -m src.check_setup` | step 1 |
| 2 | `python -m src.fetch_docs` (`--mode raw` fallback) | network |
| 3 | `python -m src.compare_chunking` | step 2 (+ model for semantic) |
| 4 | `python -m src.ingest` | steps 1, 3 |
| 5 | `python -m src.retrieve --user <u> --q "<q>"` | step 4 |
| 6 | `python -m src.run_matrix` | step 4 |
| 7 | `python -m src.negative_tests` | step 4 |

Always run Python as a module from the repo root (`python -m src.xxx`), never `python src\xxx.py`, because the imports are relative.

## 4. Architecture map
| File | Responsibility | Touch carefully? |
|---|---|---|
| `src/config.py` | loads `.env`, builds DSNs per role | yes: never add the superuser here |
| `src/db.py` | `ingest_connection()` (owner), `reader_session(user)` (RLS) | **critical** |
| `src/log_setup.py` | tees stdout/stderr to `logs/app.log`, masks passwords | yes |
| `src/embed.py` | bge model, query prefix, normalisation | keep the prefix query-only |
| `src/chunkers.py` | 4 strategies + `clean()` | params shared for a fair comparison |
| `src/compare_chunking.py` | metrics → `evidence/chunking_*` + `chunks_*.jsonl` | – |
| `src/ingest.py` | upsert docs, `document_groups`, chunks + embeddings | – |
| `src/retrieve.py` | RLS-protected cosine search | **critical** |
| `src/run_matrix.py` | Exercise D | uses the owner connection for **audit only** |
| `src/negative_tests.py` | Exercise E | must always restore membership |
| `sql/00`–`05` | roles, DB, extension, schema, RLS, grants, seed | idempotent, run in order |
| `sql/20_verify.sql` | PASS/FAIL health checks | – |
| `scripts/db_docker.ps1` | ensure / verify / reset container + DB | – |

## 5. Hard rules (DO / DON'T)
### Security – never violate
- ❌ **Never** filter results in Python as the security mechanism. RLS in SQL is the boundary.
- ❌ **Never** run retrieval as `ingest_admin` or `postgres`. Retrieval must use `reader_session()` (`rag_reader`).
- ❌ **Never** grant `BYPASSRLS`, `SUPERUSER`, write privileges, or access to `user_groups` / `app_users` / `document_groups` to `rag_reader`.
- ❌ **Never** `FORCE ROW LEVEL SECURITY` on tables without adjusting ingestion, because the owner must still load data.
- ❌ **Never** hard-code passwords, print DSNs, or commit `.env`. Read credentials only from `.env` via `config.py`.
- ❌ **Never** use `SET app.current_user` (session-wide). Use `set_config('app.current_user', x, true)` inside a transaction, as `db.py` does.
- ❌ **Never** build SQL with f-strings from user input. Use psycopg parameters (`%s` / `%(name)s`).
- ✅ Unknown or empty identity must return **0 rows**, not an error and not everything.

### Data / correctness
- ✅ Keep `EMBED_DIM=384` and `vector(384)` in sync. Changing the model means a schema change and full re-ingest.
- ✅ Add the bge query prefix **only** to queries (`embed_query`), never to passages.
- ✅ Keep `normalize_embeddings=True` (cosine distance assumes unit vectors).
- ✅ Keep the same chunk size budget across strategies, otherwise the comparison is unfair.
- ✅ Keep `doc_id` formats (`app-001`, `plat-001`, `sec-001`, `shr-001`) and the `access_class` values `application|platform|security|shared`.
- ✅ SQL scripts must stay **idempotent** (`IF NOT EXISTS`, `ON CONFLICT`, `\gexec` guards).

### Windows / PowerShell
- ✅ Scripts use `$ErrorActionPreference = "Continue"` and check `$LASTEXITCODE`. Don't switch back to `"Stop"`, because docker and psql write to stderr and PS 5.1 would abort.
- ✅ Don't name a PowerShell parameter `$args` (it's an automatic variable).
- ✅ `.sql`, `.yml`, `.py`, `.md` use LF and `.ps1` uses CRLF (`.gitattributes`).
- ✅ Run psql **inside the container** (`docker exec`), not with a local client.

## 6. Known risks & likely bugs (check these first)
| # | Symptom | Likely cause | Fix |
|---|---|---|---|
| 1 | `docker not found` / `engine not running` | Docker Desktop not started | start it, wait for "Engine running" |
| 2 | Port 5432 in use | local PostgreSQL or another container | change `PG_PORT` in `.env`, then `-Action reset` |
| 3 | `password authentication failed for user "postgres"` | superuser password changed after the volume was created | `db_docker.ps1 -Action reset` (deletes data) |
| 4 | Password with `$ # " '` or spaces breaks `.env` | Compose / PowerShell parsing | use only `A-Z a-z 0-9 _ - . @` |
| 5 | `UnicodeEncodeError` in console | cp1252 pipe | `log_setup` reconfigures stdout to UTF-8; set `PYTHONIOENCODING=utf-8` if run without it |
| 6 | `fetch_docs` warning: fewer than N files | upstream rename | script fills from the same folder; check the count is 30 |
| 7 | GitHub / HF blocked | corporate proxy | `HTTPS_PROXY`, `HF_ENDPOINT` in `.env`; `--mode raw`; `--skip-semantic` |
| 8 | Fewer than k results for a user | HNSW candidates filtered by RLS | `hnsw.ef_search=100` already set; acceptable and documented |
| 9 | `permission denied for schema rag` as reader | grants missing | rerun `db_docker.ps1` (it repairs) |
| 10 | `langchain_text_splitters` API differences | version drift | keep the pinned `<0.4`; `MarkdownHeaderTextSplitter(HEADERS, strip_headers=False)` |
| 11 | `pgvector` adapter errors on numpy | `register_vector` not called | always connect via `db.py` helpers |
| 12 | Semantic chunking slow | CPU embedding of every sentence | expected (minutes); use `--skip-semantic` for quick runs |
| 13 | `negative_tests` leaves a membership revoked | crash before `finally` | rerun `sql/05_seed_users.sql` via `db_docker.ps1` (it re-seeds) |
| 14 | `ModuleNotFoundError: src` | ran a file directly | run `python -m src.<module>` from the repo root |
| 15 | Script blocked by execution policy | Windows policy | `powershell -ExecutionPolicy Bypass -File ...` |

## 7. What NOT to do
- Don't change the 4 demo users, their groups, or the 4 test questions. They are defined by the assignment.
- Don't remove any chunking strategy or the comparison metrics (25 marks).
- Don't fabricate results in the README or `evidence/`. Values must come from a real run. The README TODO cells are filled from `evidence/`.
- Don't commit `logs/`, `.venv/`, `.cache/`, `data/_k8s_sparse/` or `.env`.
- Don't replace Docker with a cloud database or add docker-in-docker.
- Don't add an LLM call that receives chunks from anything other than `retrieve()`.
- Don't "fix" a failing security test by relaxing RLS or grants. Find the real cause.

## 8. When asked to help
- **"Run / debug the project"** → follow §3 and check `logs/app.log` (last 50 lines) and `logs/db_docker.log`.
- **"Fill the README"** → copy numbers from `evidence/chunking_comparison.md`, `evidence/matrix.md` and `evidence/negative_tests.md` only.
- **"Improve chunking"** → change only `chunkers.py` constants, rerun `compare_chunking` then `ingest`, and keep all 4 strategies.
- **"Add a user or group"** → edit `sql/05_seed_users.sql` and `EXPECTED` in `run_matrix.py` together.
- **"Change model"** → update `.env` `EMBED_MODEL`/`EMBED_DIM`, `vector(N)` in `02_schema.sql`, then `-Action reset` and full re-ingest.

## 9. Definition of done
- `run_all.ps1` completes; `check_setup` passes; matrix `PASS: 0 unauthorised results`; negative tests `9/9 passed`.
- `evidence/` filled; screenshots 01–09 present; README has no `TODO`; `.env` not committed.
- [`docs/ASSIGNMENT_COMPLETION.md`](../docs/ASSIGNMENT_COMPLETION.md) fully ticked.
