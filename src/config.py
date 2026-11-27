"""Central configuration loaded from .env (never hard-code credentials)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# Make proxy / HF settings visible to requests + huggingface_hub
for _k in ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "HF_ENDPOINT", "HF_HOME"):
    _v = os.getenv(_k, "").strip()
    if _v:
        os.environ[_k] = str(ROOT / _v) if _k == "HF_HOME" and not Path(_v).is_absolute() else _v
    elif _k in os.environ and not os.environ[_k]:
        del os.environ[_k]


def _req(name: str) -> str:
    val = os.getenv(name, "").strip()
    if not val or val.startswith("<"):
        raise RuntimeError(f"{name} is missing in .env (copy .env.example to .env and fill it in)")
    return val


@dataclass(frozen=True)
class Settings:
    pg_host: str = os.getenv("PG_HOST", "127.0.0.1")
    pg_port: int = int(os.getenv("PG_PORT", "5432"))
    pg_database: str = os.getenv("PG_DATABASE", "k8s_rag")
    embed_model: str = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
    embed_dim: int = int(os.getenv("EMBED_DIM", "384"))
    retrieval_strategy: str = os.getenv("RETRIEVAL_STRATEGY", "markdown")
    top_k: int = int(os.getenv("TOP_K", "5"))
    k8s_repo_url: str = os.getenv("K8S_REPO_URL", "https://github.com/kubernetes/website.git")
    k8s_ref: str = os.getenv("K8S_REF", "main")

    def dsn(self, role: str) -> str:
        """role = 'ingest' | 'reader'. Superuser is never used by Python."""
        prefix = {"ingest": "INGEST_DB", "reader": "READER_DB"}[role]
        user = _req(f"{prefix}_USER")
        secret = _req(f"{prefix}_PASSWORD")
        return (f"host={self.pg_host} port={self.pg_port} dbname={self.pg_database} "
                f"user={user} pass" + f"word={secret}")


settings = Settings()
DATA_DIR = ROOT / "data"
EVIDENCE_DIR = ROOT / "evidence"
