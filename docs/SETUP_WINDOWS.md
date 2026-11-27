# Windows Setup Guide (Phase 0–1)

> **IMPORTANT – Target machine note**
> These files were authored on a machine where **nothing was installed** (no PostgreSQL, no pgvector, no Docker, no Python 3.12).
> Install, setup and execution are meant to be done on a **different Windows machine that already has all required software installed** (listed below).
> Follow this guide on that machine.

## 1. Prerequisites (must already exist on the target machine)
| Software | Version | Check |
|---|---|---|
| Windows 10/11 x64 | – | – |
| Python | 3.12 (x64) | `py -3.12 --version` |
| Docker Desktop (WSL2), running | 4.x | `docker info` |
| Git | 2.x | `git --version` |
| Internet to GitHub + Hugging Face (or proxy) | – | `python -m src.check_network` |

PostgreSQL + pgvector runs in Docker (`docker-compose.yml`). No local PostgreSQL is needed.

## 2. Configure credentials
```powershell
cd k8s-rag-rls
Copy-Item .env.example .env      # skip if .env already exists
notepad .env                      # replace every <...> value
```
`.env` is git-ignored. Only `.env.example` (placeholders) is committed.

## 3. Python environment
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_venv.ps1 -CpuTorch
.\.venv\Scripts\Activate.ps1
python -m src.check_network
```

## 4. Database (Docker)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1                # create if missing, else verify
powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1 -Action reset  # rebuild from scratch
python -m src.check_setup                                                # expect ALL CHECKS PASSED
```

## What db_docker.ps1 runs (inside the container)
| Script | Runs as | Purpose |
|---|---|---|
| `sql/00_roles_and_db.sql` | superuser | `ingest_admin`, `rag_reader` (NOBYPASSRLS), database |
| `sql/01_extensions.sql` | superuser | `CREATE EXTENSION vector` |
| `sql/02_schema.sql` | ingest_admin | tables + HNSW cosine index |
| `sql/03_rls.sql` | ingest_admin | `can_read_doc()` + RLS policies |
| `sql/04_grants.sql` | ingest_admin | reader gets SELECT on documents/chunks only |
| `sql/05_seed_users.sql` | ingest_admin | Priya, Arjun, Meena, Divya + groups |

Extra: `sql/20_verify.sql` checks that every object exists. The superuser password is used only by `db_docker.ps1`. The Python app never uses it.

## 5. Dataset (Phase 2)
```powershell
python -m src.fetch_docs              # git sparse clone of kubernetes/website
python -m src.fetch_docs --mode raw   # fallback if git is blocked
```
Outputs:
- `data/raw/<access>/<doc_id>__<path>.md` – 30 original Markdown files (10 app, 10 platform, 5 security, 5 shared)
- `data/manifest.csv` – doc_id, title, access_class, source_path, source_url, github_url, sha256, license
- `data/SOURCES.md` – attribution table (CC BY 4.0, pinned commit)

If a preferred file was renamed upstream, the script fills from the same folder and prints a warning.

## 6. Chunking comparison (Phase 3)
```powershell
python -m src.compare_chunking                  # all 4 strategies (first run downloads the model, ~130 MB)
python -m src.compare_chunking --skip-semantic  # quick run without the model
```
Outputs in `evidence/`:
- `chunking_comparison.md` / `.csv` – chunks, avg/min/median/max size, overlap, heading preservation, boundary quality
- `chunking_examples.md` – good vs poor boundary examples per strategy
- `chunks_<strategy>.jsonl` – every chunk, reused by Phase 4 ingestion

Shared parameters: 800 chars, 100 overlap (fixed/recursive), min chunk 120, semantic percentile 85, semantic cap 1200.

## 7. Ingest + embeddings (Phase 4)
```powershell
python -m src.ingest                         # all 4 strategies from evidence/chunks_*.jsonl
python -m src.ingest --strategies markdown   # one strategy only
python -m src.ingest --rechunk               # re-chunk from data/raw instead of jsonl
```
- Runs as `ingest_admin` (table owner). Never uses the superuser.
- Upserts 30 documents + `document_groups` (access_class -> group), replaces chunks per strategy.
- Embeds with `BAAI/bge-small-en-v1.5` (384-dim, normalised) and stores in `vector(384)`.
- Prints docs/chunks per access class and strategy, and checks the embedding dimension.

Reference cosine query: `sql/10_retrieval_query.sql` (run as `rag_reader`).

## 8. Secure retrieval (Phase 5)
```powershell
python -m src.retrieve --user priya --q "How does a Kubernetes Deployment manage application replicas?"
python -m src.retrieve --user arjun --q "What are recommended Kubernetes RBAC practices?"   # security docs hidden
python -m src.retrieve --user nobody --q "What are the main Kubernetes components?"        # 0 rows
python -m src.retrieve --user divya --q "..." --k 3 --strategy recursive --json
```
Connects as `rag_reader`, sets `app.current_user` for one transaction, and ranks by cosine distance (`<=>`).
RLS removes unauthorised rows inside PostgreSQL before results are returned.
See `docs/TRUST_BOUNDARY.md` for the roles and trust model.

## 9. Test matrix – Exercise D (Phase 6)
```powershell
python -m src.run_matrix                                   # 4 questions x (priya, arjun, meena, divya, nobody)
python -m src.run_matrix --strategy recursive --k 3        # compare another strategy
```
Outputs in `evidence/`:
- `matrix.md` – per question and user: doc_id, access, cosine distance, heading, source URL, authorised. Also lists the chunks hidden by RLS compared with the unfiltered top-k.
- `matrix.csv` / `matrix.json` – the same data for analysis.

Exits with code 1 if any unauthorised chunk is returned (an audit failure).
The unfiltered owner view is for audit evidence only; it is never used in the retrieval path.

## 10. Negative tests + revocation – Exercise E (Phase 7)
```powershell
python -m src.negative_tests
python -m src.negative_tests --user divya --other arjun --group security
```
| Test | Shows |
|---|---|
| T1 | Meena retrieves a restricted security document |
| T2 | Priya gets 0 chunks of it (ranked search and direct SELECT) |
| T3 | Revoking Meena's membership removes access immediately; chunk IDs and embedding checksum are unchanged, so nothing was re-embedded |
| T4 | Unknown (`mallory`) and empty identities see 0 chunks |
| T5 | Restoring the membership returns access (always restored, even if a test fails) |
| T6 | Reader can't UPDATE chunks, read `user_groups`, or change its own membership |

Output: terminal log plus `evidence/negative_tests.md`. Also take a screenshot of the terminal for the submission.

## 11. Logs
All runs are logged with timestamps to the `logs\` folder (created automatically):

| File | Written by |
|---|---|
| `logs\app.log` | every Python command (`check_*`, `fetch_docs`, `compare_chunking`, `ingest`, `retrieve`, `run_matrix`, `negative_tests`) |
| `logs\setup_venv.log`, `logs\setup_db.log` | PowerShell setup scripts (transcripts, appended) |

Line format: `2026-11-26 19:44:01 | ingest           | INFO  | message`
- Console output is unchanged. Everything printed is also written to the file.
- Each run records START (with the full command line), END (with duration) and full tracebacks of any error.
- `app.log` rotates at 5 MB and keeps 5 backups. `password=...` values are masked.
- `logs\` is git-ignored (only `.gitkeep` is committed). Copy the relevant log extracts into `evidence\` if you want them in the submission.

```powershell
Get-Content .\logs\app.log -Tail 50 -Wait     # follow the log live
```

## Database via Docker (default)
PostgreSQL 16 + pgvector runs in a Docker container (`pgvector/pgvector:pg16`), bound to `127.0.0.1:${PG_PORT}` (default 5432).
User names and passwords come from `.env`. No local PostgreSQL install or `psql.exe` is needed, because psql runs inside the container.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1                 # ensure: create if missing, else verify
powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1 -Action verify   # check only
powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1 -Action status
powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1 -Action stop     # keep data
powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1 -Action reset    # delete volume + rebuild
powershell -ExecutionPolicy Bypass -File .\scripts\db_docker.ps1 -Action psql     # interactive shell
```

What `ensure` does:
1. Starts the container (it is created on the first run, data is kept in volume `k8s-rag-pgdata`) and waits until it is healthy.
2. **Database missing** → runs `sql/00`–`05`: roles, database, pgvector, tables, HNSW index, RLS, grants and demo users.
3. **Database present** → runs `sql/20_verify.sql` (about 20 PASS/FAIL checks: extension, 6 tables, `vector(384)`, HNSW index, RLS, policies, roles, grants, seed data). If any check fails, it re-applies the idempotent scripts and verifies again.
4. Logs to `logs/db_docker.log`.

`scripts/setup_db.ps1` is kept as an **alternative** for a native Windows PostgreSQL install.

### Who creates the database users?
You don't create any users by hand. Fill in the three passwords in `.env` and run `db_docker.ps1`.

| Object | Created by | When |
|---|---|---|
| `postgres` superuser (`PG_SUPERUSER` / `PG_SUPERUSER_PASSWORD`) | Docker image | first container start |
| `ingest_admin` (owns tables, loads data) | `db_docker.ps1` -> `sql/00` | first run |
| `rag_reader` (read-only, NOBYPASSRLS) | `db_docker.ps1` -> `sql/00` | first run |
| `k8s_rag` DB, pgvector, tables, HNSW index, RLS, grants | `db_docker.ps1` -> `sql/01`-`04` | first run |
| Priya, Arjun, Meena, Divya + groups | `db_docker.ps1` -> `sql/05` | first run |

Later runs verify these objects and repair anything missing. They also re-apply the `ingest_admin` and `rag_reader` passwords from `.env`.

**Password rules:**
- Use only letters, digits and `_ - . @`. Avoid `$ # " '` and spaces, which Docker/PowerShell can misread in `.env`.
- The superuser password is fixed when the container volume is first created. If you change it later, run `db_docker.ps1 -Action reset` (this deletes the data).

### Docker Desktop notes (Windows)
- Use Docker Desktop 4.x with the **WSL2 backend** and **Linux containers**. In Settings, check that "Use the WSL 2 based engine" is on.
- Start Docker Desktop and wait for **Engine running** before you run any script.
- The project folder is bind-mounted (`./sql:/sql:ro`). With WSL2 this works for any folder under `C:\Users\...`, so no extra file-sharing setup is needed.
- The port is published on `127.0.0.1` only, so `.env` uses `PG_HOST=127.0.0.1` rather than `localhost`, which avoids IPv6 `::1` issues.
- Behind a corporate proxy, set it in **Docker Desktop → Settings → Resources → Proxies** so `pgvector/pgvector:pg16` can be pulled.
- Works in Windows PowerShell 5.1 and PowerShell 7.
