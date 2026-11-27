"""Phase 6 / Exercise D - same question, different users.

Runs the 4 assignment questions under every demo identity (plus an unknown one),
records doc IDs, source links, cosine distances and whether each result is authorised.

Usage:
    python -m src.run_matrix
    python -m src.run_matrix --k 5 --strategy markdown --users priya arjun meena divya nobody

Outputs (evidence/):
    matrix.md     - per question: one table per user + "hidden by RLS" comparison
    matrix.csv    - flat rows for analysis
    matrix.json   - raw results

"authorised" is computed INDEPENDENTLY from the expected policy below (an audit check),
not used for enforcement. Enforcement is PostgreSQL RLS. Any 'NO' is a security failure.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime

from tabulate import tabulate

from .chunkers import STRATEGIES
from .config import EVIDENCE_DIR, settings
from .db import ingest_connection
from .embed import embed_query
from .retrieve import SQL, retrieve
from .log_setup import setup_logging

QUESTIONS = [
    ("Q1", "How does a Kubernetes Deployment manage application replicas?", "application"),
    ("Q2", "What are PersistentVolumes and PersistentVolumeClaims?", "platform"),
    ("Q3", "What are recommended Kubernetes RBAC practices?", "security"),
    ("Q4", "What are the main Kubernetes components?", "shared"),
]

# Expected policy (mirrors sql/05_seed_users.sql) - used only to AUDIT RLS output
EXPECTED = {
    "priya": {"application", "shared"},
    "arjun": {"platform", "shared"},
    "meena": {"security", "shared"},
    "divya": {"application", "security", "shared"},
}
DEFAULT_USERS = ["priya", "arjun", "meena", "divya", "nobody"]


def unfiltered_top(qvec, strategy: str, k: int):
    """Ground truth WITHOUT RLS (table owner, audit only) - shows what RLS hid."""
    with ingest_connection() as conn, conn.cursor() as cur:
        cur.execute(SQL, {"q": qvec, "strategy": strategy, "k": k})
        return cur.fetchall()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=settings.top_k)
    ap.add_argument("--strategy", choices=STRATEGIES, default=settings.retrieval_strategy)
    ap.add_argument("--users", nargs="+", default=DEFAULT_USERS)
    a = ap.parse_args()
    EVIDENCE_DIR.mkdir(exist_ok=True)

    flat, raw, failures = [], {}, 0
    md = [f"# Exercise D - same question, different results",
          f"", f"Run: {datetime.now():%Y-%m-%d %H:%M}  |  strategy=`{a.strategy}`  |  k={a.k}  |  "
          f"model=`{settings.embed_model}`", "",
          "*authorised* = audit against expected group policy (enforcement is RLS). "
          "*Hidden by RLS* = chunks in the unfiltered top-k that this user did not receive.", ""]

    for qid, question, area in QUESTIONS:
        qvec = embed_query(question)
        truth = unfiltered_top(qvec, a.strategy, a.k)
        truth_ids = [(r[0], r[3]) for r in truth]
        md += [f"## {qid}: {question}", f"Primary area: **{area}**", "",
               "**Unfiltered top-k (owner view, audit only):** " +
               ", ".join(f"`{r[0]}`({r[4]}, {r[6]:.3f})" for r in truth), ""]
        raw[qid] = {}

        for user in a.users:
            hits = retrieve(user, question, a.k, a.strategy, qvec=qvec)
            allowed = EXPECTED.get(user, set())
            rows = []
            for h in hits:
                ok = h.access_class in allowed
                failures += not ok
                rows.append([h.rank, h.doc_id, h.access_class, f"{h.cosine_distance:.4f}",
                             (h.heading_path or "")[:45], h.source_url, "YES" if ok else "NO !!"])
                flat.append({"question_id": qid, "question": question, "user": user,
                             "rank": h.rank, "doc_id": h.doc_id, "title": h.title,
                             "heading_path": h.heading_path, "access_class": h.access_class,
                             "cosine_distance": round(h.cosine_distance, 4),
                             "source_url": h.source_url, "authorised": ok})
            got = {(h.doc_id, h.seq) for h in hits}
            hidden = sorted({d for d, s in truth_ids if (d, s) not in got})
            raw[qid][user] = [h.__dict__ | {"content": h.content[:300]} for h in hits]

            md.append(f"### {user}  (groups: {', '.join(sorted(allowed)) or 'none - unknown identity'})")
            if rows:
                md.append(tabulate(rows, headers=["#", "doc_id", "access", "cos_dist", "heading",
                                                  "source", "authorised"], tablefmt="github"))
            else:
                md.append("_0 rows returned - RLS denied all chunks._")
            md += ["", f"Hidden by RLS from unfiltered top-k: {', '.join(f'`{d}`' for d in hidden) or 'none'}", ""]
            print(f"{qid} {user:<7} {len(hits)} hits  top={hits[0].doc_id if hits else '-'}  hidden={len(hidden)}")

    md += ["## Result",
           f"**{'PASS' if failures == 0 else 'FAIL'}** - {failures} unauthorised chunk(s) returned "
           f"across {len(QUESTIONS)} questions x {len(a.users)} identities."]

    (EVIDENCE_DIR / "matrix.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (EVIDENCE_DIR / "matrix.json").write_text(json.dumps(raw, indent=2, ensure_ascii=False, default=str),
                                              encoding="utf-8")
    if flat:
        with (EVIDENCE_DIR / "matrix.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(flat[0].keys()))
            w.writeheader()
            w.writerows(flat)
    print(f"\n{'PASS' if failures == 0 else 'FAIL'}: {failures} unauthorised results. "
          f"Wrote evidence/matrix.md, .csv, .json")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    setup_logging("run_matrix")
    main()
