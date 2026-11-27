"""Embedding model wrapper (BAAI/bge-small-en-v1.5, 384-dim, L2-normalised).

bge models expect a query instruction prefix for retrieval queries only;
passages are embedded as-is.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from .config import settings

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def model():
    from sentence_transformers import SentenceTransformer  # heavy import, lazy
    m = SentenceTransformer(settings.embed_model, device="cpu")
    dim = m.get_sentence_embedding_dimension()
    if dim != settings.embed_dim:
        raise RuntimeError(f"Model dim {dim} != EMBED_DIM {settings.embed_dim}")
    return m


def embed_passages(texts: list[str], batch_size: int = 32) -> np.ndarray:
    return model().encode(texts, batch_size=batch_size, normalize_embeddings=True,
                          show_progress_bar=len(texts) > 64, convert_to_numpy=True)


def embed_query(q: str) -> np.ndarray:
    return model().encode(QUERY_PREFIX + q, normalize_embeddings=True, convert_to_numpy=True)
