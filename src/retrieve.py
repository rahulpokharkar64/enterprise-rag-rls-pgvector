"""Phase 5 - secure retrieval. RLS filters rows INSIDE PostgreSQL before Python sees them.

Usage:
    python -m src.retrieve --user priya --q "How does a Deployment manage replicas?"
    python -m src.retrieve --user meena --q "RBAC good practices" --k 3 --strategy markdown
    python -m src.retrieve --user nobody --q "..." --json

The --user flag SIMULATES a verified identity for this local demo only.
Production: a trusted backend derives the identity from a verified token (OIDC/JWT)
and the end user never chooses it or holds database credentials.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from tabulate import tabulate

from .chunkers import STRATEGIES
from .config import settings
from .db import reader_session
from .embed import embed_query
from .log_setup import setup_logging

SQL = """
SELECT c.doc_id, d.title, c.heading_path, c.seq, d.access_class, d.source_url,
       (c.embedding <=> %(q)s)::float AS cosine_distance, c.content
FROM   rag.chunks c
JOIN   rag.documents d USING (doc_id)
WHERE  c.strategy = %(strategy)s
ORDER  BY c.embedding <=> %(q)s
LIMIT  %(k)s
"""


@dataclass
class Hit:
    rank: int
    doc_id: str
    title: str
    heading_path: str | None
    seq: int
    access_class: str
    source_url: str
    cosine_distance: float
    content: str


def retrieve(user: str | None, question: str, k: int | None = None,
             strategy: str | None = None, qvec=None) -> list[Hit]:
    """Return ranked chunks visible to `user`. Unauthorised rows never leave the DB."""
    qvec = embed_query(question) if qvec is None else qvec
    with reader_session(user) as cur:
        # Optional: exact search for small data so RLS-filtered top-k is never short
        cur.execute("SET LOCAL hnsw.ef_search = 100")
        cur.execute(SQL, {"q": qvec, "strategy": strategy or settings.retrieval_strategy,
                          "k": k or settings.top_k})
        rows = cur.fetchall()
    return [Hit(i, *r) for i, r in enumerate(rows, 1)]


def main() -> None:
    ap = argparse.ArgumentParser(description="RLS-protected retrieval")
    ap.add_argument("--user", required=True, help="demo identity: priya|arjun|meena|divya|<unknown>")
    ap.add_argument("--q", required=True, help="question")
    ap.add_argument("--k", type=int, default=settings.top_k)
    ap.add_argument("--strategy", choices=STRATEGIES, default=settings.retrieval_strategy)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    hits = retrieve(a.user, a.q, a.k, a.strategy)
    if a.json:
        print(json.dumps([asdict(h) for h in hits], indent=2, ensure_ascii=False))
        return
    print(f"user={a.user}  strategy={a.strategy}  k={a.k}\nQ: {a.q}\n")
    if not hits:
        print("No authorised results (0 rows returned by RLS).")
        return
    print(tabulate([[h.rank, h.doc_id, h.access_class, f"{h.cosine_distance:.4f}",
                     (h.heading_path or "")[:50], h.source_url] for h in hits],
                   headers=["#", "doc_id", "access", "cos_dist", "heading", "source"],
                   tablefmt="github"))
    print(f"\nTop chunk preview:\n{hits[0].content[:400]}")


if __name__ == "__main__":
    setup_logging("retrieve")
    main()
