"""Phase 7 / Exercise E - negative tests and revocation.

Demonstrates, against the live database:
  T1  authorised user (meena) retrieves a restricted SECURITY document
  T2  unauthorised user (priya) cannot retrieve that same document
  T3  revoking meena's 'security' membership removes access IMMEDIATELY
      (same chunk_ids / embeddings - no re-embedding or re-ingest)
  T4  unknown identity and empty identity read 0 protected chunks
  T5  restoring the membership returns access
  T6  extra: reader role cannot write chunks or read membership tables

Usage:
    python -m src.negative_tests
    python -m src.negative_tests --user meena --group security --q "What are recommended Kubernetes RBAC practices?"

Output: terminal log + evidence/negative_tests.md (keep it as the screenshot evidence).
The membership is ALWAYS restored in a finally block, even if a test fails.
"""
from __future__ import annotations

import argparse
from datetime import datetime

from .config import EVIDENCE_DIR, settings
from .db import ingest_connection, reader_session
from .embed import embed_query
from .retrieve import retrieve
from .log_setup import setup_logging

LOG: list[str] = []
RESULTS: list[tuple[str, bool]] = []


def log(msg: str = "") -> None:
    print(msg)
    LOG.append(msg)


def record(name: str, ok: bool, detail: str) -> None:
    RESULTS.append((name, ok))
    log(f"[{'PASS' if ok else 'FAIL'}] {name} - {detail}")


def doc_hits(user, q, qvec, doc_id, strategy, k):
    hits = retrieve(user, q, k, strategy, qvec=qvec)
    return hits, [h for h in hits if h.doc_id == doc_id]


def count_visible(user, doc_id, strategy) -> int:
    """Direct count of the doc's chunks visible to user (independent of ranking)."""
    with reader_session(user) as cur:
        cur.execute("SELECT count(*) FROM rag.chunks WHERE doc_id=%s AND strategy=%s", (doc_id, strategy))
        return cur.fetchone()[0]


def membership(conn, user, group, action: str) -> None:
    with conn.cursor() as cur:
        if action == "revoke":
            cur.execute("""DELETE FROM rag.user_groups ug USING rag.app_users u, rag.groups g
                           WHERE ug.user_id=u.user_id AND ug.group_id=g.group_id
                             AND u.username=%s AND g.group_key=%s""", (user, group))
        else:
            cur.execute("""INSERT INTO rag.user_groups (user_id, group_id)
                           SELECT u.user_id, g.group_id FROM rag.app_users u, rag.groups g
                           WHERE u.username=%s AND g.group_key=%s
                           ON CONFLICT DO NOTHING""", (user, group))
        n = cur.rowcount
    conn.commit()
    log(f"    SQL: {action} {user} -> {group}  ({n} row(s) changed, committed)")


def fingerprint(conn, doc_id, strategy):
    """chunk_ids + embedding checksum: proves no re-embedding happened."""
    with conn.cursor() as cur:
        cur.execute("""SELECT count(*), min(chunk_id), max(chunk_id),
                              md5(string_agg(embedding::text, '|' ORDER BY chunk_id))
                       FROM rag.chunks WHERE doc_id=%s AND strategy=%s""", (doc_id, strategy))
        return cur.fetchone()


def fmt(hits) -> str:
    return ", ".join(f"{h.doc_id}#{h.seq}({h.access_class},{h.cosine_distance:.3f})" for h in hits) or "0 rows"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="meena", help="authorised user")
    ap.add_argument("--other", default="priya", help="unauthorised user")
    ap.add_argument("--group", default="security")
    ap.add_argument("--q", default="What are recommended Kubernetes RBAC practices?")
    ap.add_argument("--strategy", default=settings.retrieval_strategy)
    ap.add_argument("--k", type=int, default=settings.top_k)
    a = ap.parse_args()

    log(f"# Exercise E - negative tests and revocation")
    log(f"Run: {datetime.now():%Y-%m-%d %H:%M:%S}  strategy={a.strategy}  k={a.k}")
    log(f"Question: {a.q}\n")
    qvec = embed_query(a.q)

    admin = ingest_connection()
    try:
        # pick the most relevant restricted doc as seen by the authorised user
        base, _ = doc_hits(a.user, a.q, qvec, None, a.strategy, a.k)
        target = next((h for h in base if h.access_class == a.group), None)
        if target is None:
            raise SystemExit(f"{a.user} got no '{a.group}' doc - check ingest / memberships")
        doc = target.doc_id
        log(f"Target restricted document: {doc} '{target.title}' ({a.group})  {target.source_url}\n")
        fp_before = fingerprint(admin, doc, a.strategy)

        # T1
        log("## T1 authorised user retrieves restricted doc")
        hits, d = doc_hits(a.user, a.q, qvec, doc, a.strategy, a.k)
        log(f"    {a.user}: {fmt(hits)}")
        record("T1 authorised access", bool(d), f"{a.user} received {len(d)} chunk(s) of {doc}")

        # T2
        log("\n## T2 unauthorised user cannot retrieve it")
        hits, d = doc_hits(a.other, a.q, qvec, doc, a.strategy, a.k)
        vis = count_visible(a.other, doc, a.strategy)
        log(f"    {a.other}: {fmt(hits)}")
        record("T2 unauthorised denied", not d and vis == 0,
               f"{a.other} ranked hits on {doc}={len(d)}, direct SELECT count={vis}")

        # T3
        log(f"\n## T3 revoke {a.user} from '{a.group}' (no re-embedding)")
        membership(admin, a.user, a.group, "revoke")
        hits, d = doc_hits(a.user, a.q, qvec, doc, a.strategy, a.k)
        vis = count_visible(a.user, doc, a.strategy)
        fp_after = fingerprint(admin, doc, a.strategy)
        log(f"    {a.user}: {fmt(hits)}")
        log(f"    chunk fingerprint before={fp_before[0]} chunks ids {fp_before[1]}-{fp_before[2]} md5 {fp_before[3][:12]}")
        log(f"    chunk fingerprint after ={fp_after[0]} chunks ids {fp_after[1]}-{fp_after[2]} md5 {fp_after[3][:12]}")
        record("T3 revocation immediate", not d and vis == 0 and fp_before == fp_after,
               f"visible={vis}, embeddings unchanged={fp_before == fp_after}")

        # T4
        log("\n## T4 unknown / empty identity")
        for ident in ("mallory", ""):
            hits = retrieve(ident, a.q, a.k, a.strategy, qvec=qvec)
            with reader_session(ident) as cur:
                cur.execute("SELECT count(*) FROM rag.chunks")
                total = cur.fetchone()[0]
            record(f"T4 identity '{ident or '<empty>'}'", not hits and total == 0,
                   f"ranked hits={len(hits)}, SELECT count(*) on all chunks={total}")
    finally:
        # T5 - always restore
        log(f"\n## T5 restore {a.user} -> '{a.group}'")
        membership(admin, a.user, a.group, "restore")

    hits, d = doc_hits(a.user, a.q, qvec, doc, a.strategy, a.k)
    log(f"    {a.user}: {fmt(hits)}")
    record("T5 access restored", bool(d), f"{a.user} received {len(d)} chunk(s) of {doc}")
    admin.close()

    # T6 - extra hardening
    log("\n## T6 reader role cannot write or read memberships")
    for label, sql in (("UPDATE chunks", "UPDATE rag.chunks SET content='x' WHERE false"),
                       ("SELECT user_groups", "SELECT * FROM rag.user_groups"),
                       ("change own membership", "INSERT INTO rag.user_groups VALUES (1,1)")):
        try:
            with reader_session(a.other) as cur:
                cur.execute(sql)
            record(f"T6 {label}", False, "statement was allowed")
        except Exception as exc:
            record(f"T6 {label}", "permission denied" in str(exc).lower(),
                   str(exc).splitlines()[0])

    passed = sum(ok for _, ok in RESULTS)
    log(f"\n## Summary: {passed}/{len(RESULTS)} passed")
    EVIDENCE_DIR.mkdir(exist_ok=True)
    (EVIDENCE_DIR / "negative_tests.md").write_text(
        "\n".join(LOG[:1]) + "\n\n```text\n" + "\n".join(LOG[1:]) + "\n```\n", encoding="utf-8")
    print("Wrote evidence/negative_tests.md")
    raise SystemExit(0 if passed == len(RESULTS) else 1)


if __name__ == "__main__":
    setup_logging("negative_tests")
    main()
