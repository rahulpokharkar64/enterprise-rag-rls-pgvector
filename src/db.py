"""Database connections.

Trust boundary
--------------
* ingest_connection()  -> table owner, used only by the trusted ingestion job.
* reader_session(user) -> rag_reader (NOBYPASSRLS). The identity is set with
  set_config('app.current_user', <user>, is_local=true), so it lives only for the
  current transaction and RLS filters every row BEFORE Python sees it.
  In this demo the CLI --user flag simulates identity; in production a trusted
  backend sets it from a verified token (OIDC/JWT), never from user input.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
from pgvector.psycopg import register_vector

from .config import settings


def ingest_connection() -> psycopg.Connection:
    conn = psycopg.connect(settings.dsn("ingest"))
    register_vector(conn)
    return conn


@contextmanager
def reader_session(username: str | None) -> Iterator[psycopg.Cursor]:
    """Yield a cursor scoped to one transaction with the given app identity."""
    with psycopg.connect(settings.dsn("reader")) as conn:
        register_vector(conn)
        with conn.transaction(), conn.cursor() as cur:
            cur.execute("SELECT set_config('app.current_user', %s, true)",
                        ((username or "").strip().lower(),))
            yield cur
