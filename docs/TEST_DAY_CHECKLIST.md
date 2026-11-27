# Test-Day Checklist (target Windows machine)

> Run on the machine that **already has** Python 3.12, Docker Desktop and Git installed.
> Tick each box. If one fails, see the **If it fails** column, then re-run that step only.
> Deadline: **Sat 28 Nov 2026**. Budget about 60–90 min.

## A. Before you start (5 min)
| ✔ | Check | Command / expected | If it fails |
|---|---|---|---|
| ☐ | Python 3.12 | `py -3.12 --version` → `Python 3.12.x` | install 3.12 x64 |
| ☐ | Docker Desktop running | `docker info` → server version shown | start Docker Desktop, wait for 'Engine running' |
| ☐ | Port 5432 free | `Get-NetTCPConnection -LocalPort 5432 -ErrorAction SilentlyContinue` → nothing | set another `PG_PORT` in `.env` |
| ☐ | Project copied / cloned | `cd k8s-rag-rls` | – |

## B. Configure (5 min)
| ✔ | Step | Expected | If it fails |
|---|---|---|---|
| ☐ | `Copy-Item .env.example .env` (if not present) | `.env` exists | – |
| ☐ | Replace all `<...>` / `ChangeMe_*` values in `.env` | no placeholders left | setup_db prints which key is missing |
| ☐ | Proxy (only if needed): `HTTPS_PROXY`, `HF_ENDPOINT` | – | ask local IT for the proxy URL |

## C. Preflight (2 min)
| ✔ | Command | Expected |
|---|---|---|
| ☐ | `powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1 -Preflight` | all `[OK]`, `Preflight passed` |

## D. Run the pipeline (30–45 min, first run downloads ~330 MB)
Either run everything at once with `.\scripts\run_all.ps1`, or step by step:

| ✔ | Phase | Command | Pass criteria | If it fails |
|---|---|---|---|---|
| ☐ | 0 venv | `.\scripts\setup_venv.ps1 -CpuTorch` | `Done. Activate with...` | pip proxy → set `HTTPS_PROXY` |
| ☐ | – | `.\.venv\Scripts\Activate.ps1` | prompt shows `(.venv)` | `Set-ExecutionPolicy -Scope Process Bypass` |
| ☐ | 0 network | `python -m src.check_network` | 2 × `[PASS]` | proxy / `HF_ENDPOINT`; use `--mode raw` for fetch |
| ☐ | 1 DB | `.\scripts\db_docker.ps1` | all verify checks `PASS`, `Database ready on localhost:5432/k8s_rag` | `docker not found` / `engine not running` → start Docker Desktop; image pull blocked → proxy in Docker Desktop settings; password changed after first run → `-Action reset` |
| ☐ | 1 verify | `python -m src.check_setup` | `ALL CHECKS PASSED` | `db_docker.ps1 -Action reset` |
| ☐ | 2 dataset | `python -m src.fetch_docs` | `Saved 30 docs` (10/10/5/5), no WARNING | `--mode raw`; renamed file → warning is OK if count = 30 |
| ☐ | 3 chunking | `python -m src.compare_chunking` | table with 4 rows | model download blocked → `--skip-semantic` (min 3 still meets the assignment) |
| ☐ | 4 ingest | `python -m src.ingest` | `embedding dims: 384`, 4 strategies × 4 access classes | re-run; it's idempotent |
| ☐ | 5 retrieve | `python -m src.retrieve --user priya --q "How does a Kubernetes Deployment manage application replicas?"` | top hit `app-*` | – |
| ☐ | 5 deny | `python -m src.retrieve --user nobody --q "What are the main Kubernetes components?"` | `No authorised results` | **security bug**, stop and check RLS |
| ☐ | 6 matrix | `python -m src.run_matrix` | `PASS: 0 unauthorised results` | **security bug**, check `sql/03_rls.sql` and grants |
| ☐ | 7 negative | `python -m src.negative_tests` | `Summary: 9/9 passed` | read the FAIL line; membership is auto-restored |

## E. Spot-checks by hand (5 min, good screenshot evidence)
| ✔ | Command | Expected |
|---|---|---|
| ☐ | `python -m src.retrieve --user arjun --q "What are recommended Kubernetes RBAC practices?"` | no `sec-*` docs |
| ☐ | `python -m src.retrieve --user divya --q "What are recommended Kubernetes RBAC practices?"` | `sec-*` docs present |
| ☐ | `python -m src.retrieve --user meena --q "How does a Kubernetes Deployment manage application replicas?"` | no `app-*` docs |

## F. Evidence (10 min)
| ✔ | Item | Location |
|---|---|---|
| ☐ | Chunking table | `evidence/chunking_comparison.md` |
| ☐ | Boundary examples | `evidence/chunking_examples.md` |
| ☐ | Matrix | `evidence/matrix.md` |
| ☐ | Negative tests log | `evidence/negative_tests.md` |
| ☐ | Screenshots 01–09 (see `evidence/README.md`); use `.\scripts\capture_evidence.ps1 -Name <name> -Command "..."` | `evidence/screenshots/*.png` + `.txt` |
| ☐ | Dataset list | `data/SOURCES.md` |
| ☐ | Logs reviewed, no errors | `logs/app.log`, `logs/run_all.log` |

## G. README updates (15 min)
| ✔ | Section | Fill in from |
|---|---|---|
| ☐ | §4 file list | `data/SOURCES.md` |
| ☐ | §5 chunking table + confirm recommendation | `evidence/chunking_comparison.md` |
| ☐ | §8 Exercise D summary + PASS | `evidence/matrix.md` |
| ☐ | §9 Exercise E results | `evidence/negative_tests.md` |
| ☐ | §12 Q1 evidence numbers | chunking table |
| ☐ | Search for leftover TODOs | `Select-String -Path README.md -Pattern TODO` → none |

## H. Before pushing to GitHub (5 min)
| ✔ | Check | Command / expected |
|---|---|---|
| ☐ | `.env` NOT staged | `git status` → `.env` not listed |
| ☐ | No secrets in tracked files | `git grep -n -i "password=[REDACTED_PASSWORD] → only placeholders / variable names |
| ☐ | `.venv/`, `logs/*`, `.cache/` ignored | `git status --ignored` |
| ☐ | Fresh reproduce (optional) | `run_all.ps1 -ResetDb -SkipFetch` → all phases pass |
| ☐ | Push and open the repo page | README renders, links work |

## Quick troubleshooting
| Symptom | Fix |
|---|---|
| `running scripts is disabled` | `Set-ExecutionPolicy -Scope Process Bypass` |
| Container unhealthy | `.\scripts\db_docker.ps1 -Action logs` |
| Superuser password changed in `.env` after first run | the volume keeps the old one → `-Action reset` |
| `permission denied for schema rag` (reader) | `db_docker.ps1` (it repairs missing grants) |
| Fewer than k results for a user | expected when RLS hides many top hits; see README limitations |
| HF download timeout | set `HF_ENDPOINT` / proxy, or pre-copy the model into `.cache\huggingface` |
| Port 5432 in use / other server | change `PG_PORT` in `.env` |
