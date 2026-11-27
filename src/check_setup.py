"""Phase 1 verification: python -m src.check_setup"""
from __future__ import annotations

import sys

from .db import ingest_connection, reader_session
from .log_setup import setup_logging

ok = True


def check(label: str, cond: bool, detail: str = "") -> None:
    global ok
    ok &= cond
    print(f"[{'PASS' if cond else 'FAIL'}] {label} {detail}")


def main() -> None:
    with ingest_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT extversion FROM pg_extension WHERE extname='vector'")
        row = cur.fetchone()
        check("pgvector installed", row is not None, f"(version {row[0] if row else '-'})")

        cur.execute("""SELECT c.relname, c.relrowsecurity FROM pg_class c
                       JOIN pg_namespace n ON n.oid=c.relnamespace
                       WHERE n.nspname='rag' AND c.relname IN ('documents','chunks')""")
        for name, rls in cur.fetchall():
            check(f"RLS enabled on rag.{name}", rls)

        cur.execute("SELECT rolbypassrls, rolsuper FROM pg_roles WHERE rolname=current_setting('app.reader_role', true)"
                    " OR rolname = %s", ("rag_reader",))
        r = cur.fetchone()
        check("reader role is NOBYPASSRLS / not superuser", r is not None and not r[0] and not r[1])

        cur.execute("SELECT count(*) FROM rag.app_users")
        check("4 demo users seeded", cur.fetchone()[0] == 4)
        cur.execute("SELECT count(*) FROM rag.user_groups")
        check("9 memberships seeded", cur.fetchone()[0] == 9)

    # Reader: must not see membership tables, unknown identity sees nothing
    with reader_session("nobody") as cur:
        cur.execute("SELECT count(*) FROM rag.chunks")
        check("unknown identity sees 0 chunks", cur.fetchone()[0] == 0)
    try:
        with reader_session("priya") as cur:
            cur.execute("SELECT count(*) FROM rag.user_groups")
        check("reader blocked from rag.user_groups", False)
    except Exception as exc:  # permission denied expected
        check("reader blocked from rag.user_groups", "permission denied" in str(exc).lower())

    print("\nALL CHECKS PASSED" if ok else "\nSOME CHECKS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    setup_logging("check_setup")
    main()
