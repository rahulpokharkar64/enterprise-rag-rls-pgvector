# evidence/

This folder is **empty until the pipeline runs** on the target machine. The scripts write their output here automatically.

## Files generated automatically
| File | Created by | Used in README |
|---|---|---|
| `chunking_comparison.md` / `.csv` | `python -m src.compare_chunking` | §5 chunking table |
| `chunking_examples.md` | `python -m src.compare_chunking` | §5 good vs poor boundaries |
| `chunks_<strategy>.jsonl` | `python -m src.compare_chunking` | input to `ingest` |
| `matrix.md` / `.csv` / `.json` | `python -m src.run_matrix` | §8 Exercise D |
| `negative_tests.md` | `python -m src.negative_tests` | §9 Exercise E |

## Screenshots (you add these)
Put them in `evidence/screenshots/`.

| # | File name | What to capture |
|---|---|---|
| 1 | `01_preflight.png` | `run_all.ps1 -Preflight` showing all `[OK]` |
| 2 | `02_db_docker.png` | `db_docker.ps1` verify table showing all `PASS` and `Database ready` |
| 3 | `03_check_setup.png` | `python -m src.check_setup` showing `ALL CHECKS PASSED` |
| 4 | `04_chunking.png` | the comparison table printed by `compare_chunking` |
| 5 | `05_run_matrix.png` | end of `run_matrix` showing `PASS: 0 unauthorised results` |
| 6 | `06_negative_tests.png` | `negative_tests` T1–T6 lines and `Summary: 9/9 passed` |
| 7 | `07_arjun_rbac.png` | Arjun's RBAC search with no `sec-*` docs |
| 8 | `08_divya_rbac.png` | Divya's RBAC search with `sec-*` docs |
| 9 | `09_nobody.png` | `--user nobody` showing `No authorised results` |

### Option A: automatic (recommended)
`scripts\capture_evidence.ps1` runs a command, saves its full output as `.txt`, and takes a screenshot of the screen:
```powershell
.\scripts\capture_evidence.ps1 -Name 06_negative_tests -Command "python -m src.negative_tests"
.\scripts\capture_evidence.ps1 -Name 05_run_matrix     -Command "python -m src.run_matrix"
```
Maximise the terminal window before running so the screenshot is readable.

### Option B: manual
1. Run the command in a maximised terminal.
2. Press **Win + Shift + S**, then drag over the output.
3. Paste into Paint (Ctrl+V) and save as `evidence\screenshots\<name>.png`.

For long output, scroll so the **summary lines** are visible. The full text is already in the `.md` files and in `logs\app.log`.
