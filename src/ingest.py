"""Phase 4 - load documents, permissions, chunks + embeddings into PostgreSQL/pgvector.

Runs as the INGESTION role (table owner, trusted backend job). Idempotent:
documents are upserted, chunks for each (doc, strategy) are replaced.

Usage:
    python -m src.ingest                          # all strategies found in evidence/chunks_*.jsonl
    python -m src.ingest --strategies markdown    # only one strategy
    python -m src.ingest --rechunk                # re-chunk from data/raw instead of reading jsonl

Prerequisites: scripts/db_docker.ps1, src.fetch_docs, src.compare_chunking (or --rechunk)
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from collections import defaultdict

from .chunkers import STRATEGIES, chunk, clean
from .config import DATA_DIR, EVIDENCE_DIR, ROOT, settings
from .db import ingest_connection
from .embed import embed_passages
from .log_setup import setup_logging

BATCH = 64


def load_manifest() -> list[dict]:
    path = DATA_DIR / "manifest.csv"
    if not path.exists():
        raise SystemExit("data/manifest.csv missing - run: python -m src.fetch_docs")
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_chunks(strategy: str, docs: list[dict], rechunk: bool) -> dict[str, list[dict]]:
    """Return {doc_id: [ {seq, heading_path, content, char_len}, ... ]}."""
    by_doc: dict[str, list[dict]] = defaultdict(list)
    jsonl = EVIDENCE_DIR / f"chunks_{strategy}.jsonl"
    if not rechunk and jsonl.exists():
        with jsonl.open(encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                by_doc[r["doc_id"]].append(r)
        return by_doc
    for d in docs:
        text = clean((ROOT / d["local_path"]).read_text(encoding="utf-8"), d["title"])
        for c in chunk(text, strategy):
            by_doc[d["doc_id"]].append({"seq": c.seq, "heading_path": c.heading_path,
                                        "content": c.text, "char_len": c.size})
    return by_doc


def upsert_documents(cur, docs: list[dict]) -> None:
    for d in docs:
        cur.execute("""
            INSERT INTO rag.documents (doc_id, title, source_path, source_url, access_class,
                                       license, sha256, char_len)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (doc_id) DO UPDATE SET
                title=EXCLUDED.title, source_path=EXCLUDED.source_path,
                source_url=EXCLUDED.source_url, access_class=EXCLUDED.access_class,
                license=EXCLUDED.license, sha256=EXCLUDED.sha256,
                char_len=EXCLUDED.char_len, ingested_at=now()
        """, (d["doc_id"], d["title"], d["source_path"], d["source_url"], d["access_class"],
              d["license"], d["sha256"], int(d["char_len"])))
        # Permission = document's access class -> matching group (replace on re-run)
        cur.execute("DELETE FROM rag.document_groups WHERE doc_id=%s", (d["doc_id"],))
        cur.execute("""
            INSERT INTO rag.document_groups (doc_id, group_id)
            SELECT %s, group_id FROM rag.groups WHERE group_key=%s
        """, (d["doc_id"], d["access_class"]))
        if cur.rowcount != 1:
            raise RuntimeError(f"No group '{d['access_class']}' for {d['doc_id']} - run scripts\\db_docker.ps1")


def ingest_strategy(conn, strategy: str, docs: list[dict], rechunk: bool) -> int:
    by_doc = load_chunks(strategy, docs, rechunk)
    rows = [(doc_id, c) for doc_id, cs in by_doc.items() for c in cs]
    if not rows:
        print(f"  {strategy}: no chunks found (run compare_chunking or use --rechunk)")
        return 0
    t0 = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM rag.chunks WHERE strategy=%s", (strategy,))
        for i in range(0, len(rows), BATCH):
            batch = rows[i:i + BATCH]
            vecs = embed_passages([c["content"] for _, c in batch])
            cur.executemany("""
                INSERT INTO rag.chunks (doc_id, strategy, seq, heading_path, content, char_len, embedding)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, [(doc_id, strategy, c["seq"], c["heading_path"], c["content"], c["char_len"], v)
                  for (doc_id, c), v in zip(batch, vecs)])
    conn.commit()
    print(f"  {strategy:<10} {len(rows):>5} chunks embedded + stored ({time.perf_counter() - t0:.1f}s)")
    return len(rows)


def summary(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT d.access_class, c.strategy, count(DISTINCT d.doc_id) docs, count(*) chunks
            FROM rag.chunks c JOIN rag.documents d USING (doc_id)
            GROUP BY 1,2 ORDER BY 2,1
        """)
        print("\naccess_class  strategy    docs  chunks")
        for a, s, d, c in cur.fetchall():
            print(f"{a:<13} {s:<10} {d:>5} {c:>7}")
        cur.execute("SELECT vector_dims(embedding) FROM rag.chunks LIMIT 1")
        r = cur.fetchone()
        print(f"\nembedding dims: {r[0] if r else '-'} (expected {settings.embed_dim})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategies", nargs="+", choices=STRATEGIES, default=list(STRATEGIES))
    ap.add_argument("--rechunk", action="store_true")
    args = ap.parse_args()

    docs = load_manifest()
    print(f"Ingesting {len(docs)} documents with model {settings.embed_model}")
    with ingest_connection() as conn:
        with conn.cursor() as cur:
            upsert_documents(cur, docs)
        conn.commit()
        total = sum(ingest_strategy(conn, s, docs, args.rechunk) for s in args.strategies)
        with conn.cursor() as cur:
            cur.execute("ANALYZE rag.chunks")
        conn.commit()
        summary(conn)
    print(f"\nDone: {total} chunks.")


if __name__ == "__main__":
    setup_logging("ingest")
    main()
