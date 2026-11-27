# Assignment Completion Checklist

**Testleaf FDE Program – Week 7: Enterprise RAG: Chunking & Role-Based Security**
Repository: `enterprise-rag-rls-pgvector` · Due: **28 Nov 2026** · Total: 100 marks

> **Legend**
> - ✅ `[x]` = done (code and docs are written and in the repo)
> - ⬜ `[ ]` = **to be ticked by the learner after running on the target machine**. Each one links to the evidence file it produces.
>
> The code was authored on a machine with no software installed. Execution happens on a separate Windows machine with Python 3.12, Docker Desktop and Git (see [README §1](../README.md#1-prerequisites)).
> Evidence lives in [`../evidence/`](../evidence/) and screenshots in [`../evidence/screenshots/`](../evidence/screenshots/).

---

## 1. Environment & setup
| ✔ | Item | How / file | Evidence |
|---|---|---|---|
| [x] | Python project with pinned `requirements.txt` (Python 3.12) | [`requirements.txt`](../requirements.txt) | – |
| [x] | `.venv` setup script | [`scripts/setup_venv.ps1`](../scripts/setup_venv.ps1) | – |
| [x] | `.env.example` with placeholders only; `.env` git-ignored | [`.env.example`](../.env.example), [`.gitignore`](../.gitignore) | – |
| [x] | Docker Desktop PostgreSQL 16 + pgvector container on `127.0.0.1` | [`docker-compose.yml`](../docker-compose.yml) | – |
| [x] | Database script: creates if missing, otherwise verifies and repairs | [`scripts/db_docker.ps1`](../scripts/db_docker.ps1), [`sql/20_verify.sql`](../sql/20_verify.sql) | – |
| [x] | One-command pipeline with preflight | [`scripts/run_all.ps1`](../scripts/run_all.ps1) | – |
| [x] | Timestamped logging to `logs/` | [`src/log_setup.py`](../src/log_setup.py) | – |
| [ ] | Preflight passed on the target machine | `run_all.ps1 -Preflight` | [01_preflight.png](../evidence/screenshots/01_preflight.png) |
| [x] | `.venv` created, packages installed | `setup_venv.ps1 -CpuTorch` | `logs/setup_venv.log` |
| [ ] | Network check passed (GitHub + Hugging Face) | `python -m src.check_network` | `logs/app.log` |
| [x] | Container healthy, all verify checks PASS | `db_docker.ps1` | [1_docker_container.png](../evidence/screenshots/1_docker_container.png) |
| [x] | `check_setup` → `ALL CHECKS PASSED` | `python -m src.check_setup` | [03_check_setup.png](../evidence/screenshots/03_check_setup.png) |

## 2. Public dataset – Kubernetes docs (rubric: ingestion & metadata, 15)
| ✔ | Item | How / file | Evidence |
|---|---|---|---|
| [x] | Fetch script (git sparse clone + raw HTTPS fallback) | [`src/fetch_docs.py`](../src/fetch_docs.py) | – |
| [x] | Plan of 10 workloads / 10 storage / 5 security / 5 overview | `PLAN` in `fetch_docs.py` | – |
| [x] | Original filename, title, source path, URL, GitHub commit link, SHA-256, license | `manifest.csv` columns | – |
| [x] | CC BY 4.0 attribution; access policies declared fictional | README §4 | – |
| [x] | 30 docs downloaded (10/10/5/5) with no shortfall warning | `python -m src.fetch_docs` | [`data/manifest.csv`](../data/manifest.csv) |
| [x] | Attribution table generated | – | [`data/SOURCES.md`](../data/SOURCES.md) |
| [ ] | README §4 file list filled in from `SOURCES.md` | edit README | [README §4](../README.md#4-dataset--attribution) |

## 3. Exercise A – Chunking comparison (rubric: 25)
| ✔ | Item | How / file | Evidence |
|---|---|---|---|
| [x] | Fixed-size chunking (800 / 100) | [`src/chunkers.py`](../src/chunkers.py) | – |
| [x] | Recursive chunking (800 / 100) | `chunkers.py` | – |
| [x] | Markdown structure-aware chunking with heading path | `chunkers.py` | – |
| [x] | Semantic chunking (bge embeddings, 85th percentile, 1200 cap) | `chunkers.py` | – |
| [x] | Metrics: total, avg/min/median/max, overlap, heading preservation, boundary quality | [`src/compare_chunking.py`](../src/compare_chunking.py) | – |
| [x] | Comparison run on the same 30 docs (4 strategies) | `python -m src.compare_chunking` | [chunking_comparison.md](../evidence/chunking_comparison.md), [.csv](../evidence/chunking_comparison.csv) |
| [x] | Good / poor boundary examples generated | – | [chunking_examples.md](../evidence/chunking_examples.md) |
| [x] | Screenshot of the comparison table | `3_chunkingdata.png` | [3_chunkingdata.png](../evidence/screenshots/3_chunkingdata.png) |
| [x] | README §5 table filled with real numbers | edit README | [README §5](../README.md#5-chunking-comparison--recommendation) |
| [x] | Recommendation (Markdown) confirmed or changed based on real numbers | edit README | README §5 |

## 4. Exercise B – Embeddings & pgvector (rubric: 20)
| ✔ | Item | How / file | Evidence |
|---|---|---|---|
| [x] | `BAAI/bge-small-en-v1.5`, 384-dim, normalised, query prefix | [`src/embed.py`](../src/embed.py) | – |
| [x] | Schema: documents (id, title, URL, path), chunks (text, seq, heading, `vector(384)`) | [`sql/02_schema.sql`](../sql/02_schema.sql) | – |
| [x] | Access classification + `document_groups` permissions | `02_schema.sql`, [`src/ingest.py`](../src/ingest.py) | – |
| [x] | HNSW index with `vector_cosine_ops` | `02_schema.sql` | – |
| [x] | Cosine-distance query returning ranked, attributable results | [`src/retrieve.py`](../src/retrieve.py), [`sql/10_retrieval_query.sql`](../sql/10_retrieval_query.sql) | – |
| [x] | Ingest completed; `embedding dims: 384` printed | `python -m src.ingest` | `logs/app.log` |
| [ ] | Sample retrieval as Priya returns `app-*` with URLs and distances | `python -m src.retrieve --user priya --q "..."` | `logs/app.log` |

## 5. Exercise C – Role-based access with RLS (rubric: 25)
| ✔ | Item | How / file | Evidence |
|---|---|---|---|
| [x] | 4 demo identities with group membership (Priya, Arjun, Meena, Divya) | [`sql/05_seed_users.sql`](../sql/05_seed_users.sql) | – |
| [x] | RLS enabled on `documents` and `chunks`; `can_read_doc()` policy | [`sql/03_rls.sql`](../sql/03_rls.sql) | – |
| [x] | Least-privilege roles: `ingest_admin`, `rag_reader` (NOBYPASSRLS, SELECT only) | [`sql/00_roles_and_db.sql`](../sql/00_roles_and_db.sql), [`sql/04_grants.sql`](../sql/04_grants.sql) | – |
| [x] | Enforcement in the retrieval path, before any LLM | `src/db.py` → `reader_session()` | – |
| [x] | Trust boundary and database roles explained | [`docs/TRUST_BOUNDARY.md`](TRUST_BOUNDARY.md) | – |
| [x] | `--user` documented as a demo-only simulation; superuser never used by Python | TRUST_BOUNDARY, README §7 | – |
| [ ] | Arjun's RBAC search returns no `sec-*` docs | `capture_evidence.ps1 -Name 07_arjun_rbac ...` | [07_arjun_rbac.png](../evidence/screenshots/07_arjun_rbac.png) |
| [ ] | Divya's RBAC search returns `sec-*` docs | `capture_evidence.ps1 -Name 08_divya_rbac ...` | [08_divya_rbac.png](../evidence/screenshots/08_divya_rbac.png) |

## 6. Exercise D – Same question, different results
| ✔ | Item | How / file | Evidence |
|---|---|---|---|
| [x] | 4 test questions × 4 users + unknown identity | [`src/run_matrix.py`](../src/run_matrix.py) | – |
| [x] | Records doc IDs, source links, cosine distances, authorised flag, hidden-by-RLS list | `run_matrix.py` | – |
| [x] | Matrix run → `PASS: 0 unauthorised results` | `python -m src.run_matrix` | [matrix.md](../evidence/matrix.md), [.csv](../evidence/matrix.csv), [.json](../evidence/matrix.json) |
| [ ] | Screenshot of the matrix summary | `capture_evidence.ps1 -Name 05_run_matrix ...` | [05_run_matrix.png](../evidence/screenshots/05_run_matrix.png) |
| [x] | README §8 summary table filled in | edit README | [README §8](../README.md#8-role-by-role-retrieval-results-exercise-d) |

## 7. Exercise E – Negative tests & revocation (rubric: 15)
| ✔ | Item | How / file | Evidence |
|---|---|---|---|
| [x] | T1–T6 implemented; membership auto-restored on failure | [`src/negative_tests.py`](../src/negative_tests.py) | – |
| [x] | T1 authorised user retrieves a restricted doc | `python -m src.negative_tests` | [negative_tests.md](../evidence/negative_tests.md) |
| [x] | T2 unauthorised user is denied the same doc | ″ | ″ |
| [x] | T3 revocation is immediate; embedding fingerprint unchanged | ″ | ″ |
| [x] | T4 unknown and empty identity see 0 chunks | ″ | ″ |
| [x] | T5 restoring membership returns access | ″ | ″ |
| [x] | T6 reader cannot write or read memberships | ″ | ″ |
| [x] | `Summary: 9/9 passed` | ″ | [06_negative_tests.png](../evidence/screenshots/06_negative_tests.png) |
| [ ] | Unknown user denial screenshot | `capture_evidence.ps1 -Name 09_nobody ...` | [09_nobody.png](../evidence/screenshots/09_nobody.png) |
| [x] | README §9 results table filled in | edit README | [README §9](../README.md#9-negative-access--revocation-exercise-e) |

## 8. README & submission checklist
| ✔ | Item | Where |
|---|---|---|
| [x] | Installation & execution instructions | README §2, [SETUP_WINDOWS.md](SETUP_WINDOWS.md) |
| [x] | Dataset source, license, selection plan | README §4 |
| [x] | Schema, group memberships, RLS explanation | README §7 |
| [x] | Known limitations & improvements | README §11 |
| [x] | Final reflection Q1–Q3 answered | README §12 |
| [x] | LICENSE (MIT code + CC BY 4.0 docs note) | [`LICENSE`](../LICENSE) |
| [x] | Reflection Q1 updated with real chunking numbers | README §12 |
| [x] | No `TODO` left: `Select-String -Path README.md -Pattern TODO` → none | README |
| [ ] | `.env` not staged: `git status` | – |
| [ ] | No secrets in tracked files: `git grep -n -i "passw"` shows placeholders only | – |
| [ ] | Fresh reproduce: `run_all.ps1 -ResetDb -SkipFetch` passes | `logs/run_all.log` |
| [ ] | Pushed to GitHub `enterprise-rag-rls-pgvector`; README renders | repo URL: `________` |

## 9. Steps followed (execution log)
Fill in the date and time and tick each step as you run it on the target machine.

| # | Step | Command | Date / time | ✔ |
|---|---|---|---|---|
| 1 | Clone repo, copy `.env.example` → `.env`, set passwords | `Copy-Item .env.example .env` | | [ ] |
| 2 | Start Docker Desktop (Engine running) | – | | [ ] |
| 3 | Preflight | `.\scripts\run_all.ps1 -Preflight` | | [ ] |
| 4 | Full pipeline | `.\scripts\run_all.ps1` | | [ ] |
| 5 | Capture screenshots 01–09 | `.\scripts\capture_evidence.ps1 ...` | | [ ] |
| 6 | Fill README TODOs from `evidence/` | – | | [ ] |
| 7 | Security checks (`git status`, `git grep`) | – | | [ ] |
| 8 | Push to GitHub | `git push` | | [ ] |

## 10. Rubric self-assessment
| Area | Max | Evidence | Self-score |
|---|---|---|---|
| Document ingestion & metadata quality | 15 | manifest.csv, SOURCES.md | ___ |
| Chunking implementation & comparison | 25 | chunking_comparison.md, chunking_examples.md | ___ |
| Embeddings & relevant retrieval | 20 | matrix.md (distances, top hits) | ___ |
| Group authorisation & PostgreSQL RLS | 25 | 03_rls.sql, TRUST_BOUNDARY.md, matrix PASS | ___ |
| Negative tests, revocation & explanation | 15 | negative_tests.md, 06 screenshot | ___ |
| **Total** | **100** | | ___ |

---
**Sign-off:** Learner ____________________ · Date ________ · Reviewer ____________________
