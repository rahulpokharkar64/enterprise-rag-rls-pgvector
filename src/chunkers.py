"""Phase 3 - four chunking strategies over the same Kubernetes Markdown files.

Every strategy returns list[Chunk] with: seq, text, heading_path, start, end
(start/end = character offsets in the cleaned document, used for overlap stats).

  fixed      - fixed character windows with overlap (structure-blind baseline)
  recursive  - RecursiveCharacterTextSplitter: paragraphs -> lines -> sentences -> words
  markdown   - split on #/##/### headings, keep heading path, recursive-split long sections
  semantic   - sentence embeddings; cut where cosine similarity between neighbours drops
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
from langchain_text_splitters import (CharacterTextSplitter, MarkdownHeaderTextSplitter,
                                      RecursiveCharacterTextSplitter)

# -------- shared parameters (same budget for a fair comparison) --------
CHUNK_SIZE = 800          # characters
CHUNK_OVERLAP = 100       # characters (fixed + recursive only)
MIN_CHUNK = 120           # merge smaller tail fragments (markdown / semantic)
SEMANTIC_PERCENTILE = 85  # breakpoint = similarity drops in the lowest (100-p)% ...
SEMANTIC_MAX = 1200       # hard cap so a semantic chunk cannot grow without bound

STRATEGIES = ("fixed", "recursive", "markdown", "semantic")
HEADERS = [("#", "h1"), ("##", "h2"), ("###", "h3")]


@dataclass
class Chunk:
    seq: int
    text: str
    heading_path: str | None
    start: int = -1
    end: int = -1

    @property
    def size(self) -> int:
        return len(self.text)


# ---------------------------------------------------------------- cleaning
FRONT_MATTER = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
SHORTCODE_LINE = re.compile(r"^\s*\{\{[<%].*?[>%]\}\}\s*$", re.MULTILINE)
INLINE_SHORTCODE = re.compile(r"\{\{[<%]\s*glossary_tooltip[^}]*?text=\"([^\"]+)\"[^}]*[>%]\}\}")
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def clean(md: str, title: str | None = None) -> str:
    """Strip Hugo front matter, comments and layout-only shortcodes; keep content + headings."""
    text = FRONT_MATTER.sub("", md)
    text = COMMENT.sub("", text)
    text = INLINE_SHORTCODE.sub(r"\1", text)      # {{< glossary_tooltip text="Pod" ... >}} -> Pod
    text = SHORTCODE_LINE.sub("", text)           # {{< note >}}, {{< /note >}}, {{% capture %}}
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if title and not text.lstrip().startswith("# "):
        text = f"# {title}\n\n{text}"             # give every doc an H1 so heading paths start at the title
    return text


# ---------------------------------------------------------------- helpers
def _locate(doc: str, pieces: list[str]) -> list[tuple[int, int]]:
    """Find character offsets of each piece in order (pieces may overlap)."""
    spans, cursor = [], 0
    for p in pieces:
        probe = p[:60]
        i = doc.find(probe, max(0, cursor - CHUNK_OVERLAP - 60))
        if i < 0:
            i = doc.find(probe)
        if i < 0:
            spans.append((-1, -1))
            continue
        spans.append((i, i + len(p)))
        cursor = i + len(p)
    return spans


def _heading_at(doc: str, pos: int) -> str | None:
    """Heading path in effect at a character offset (used for structure-blind strategies)."""
    if pos < 0:
        return None
    path: dict[int, str] = {}
    for m in re.finditer(r"^(#{1,3})\s+(.+)$", doc[:pos + 1], re.MULTILINE):
        lvl = len(m.group(1))
        path = {k: v for k, v in path.items() if k < lvl}
        path[lvl] = m.group(2).strip()
    return " > ".join(path[k] for k in sorted(path)) or None


def _build(doc: str, pieces: list[str], headings: list[str | None] | None = None) -> list[Chunk]:
    pieces = [p.strip() for p in pieces if p and p.strip()]
    spans = _locate(doc, pieces)
    out = []
    for i, (p, (s, e)) in enumerate(zip(pieces, spans)):
        hp = headings[i] if headings else _heading_at(doc, s)
        out.append(Chunk(seq=i, text=p, heading_path=hp, start=s, end=e))
    return out


def _recursive_splitter(size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    return RecursiveCharacterTextSplitter(
        chunk_size=size, chunk_overlap=overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""])


# ---------------------------------------------------------------- strategies
def fixed_chunks(doc: str) -> list[Chunk]:
    splitter = CharacterTextSplitter(separator="", chunk_size=CHUNK_SIZE,
                                     chunk_overlap=CHUNK_OVERLAP, strip_whitespace=False)
    return _build(doc, splitter.split_text(doc))


def recursive_chunks(doc: str) -> list[Chunk]:
    return _build(doc, _recursive_splitter().split_text(doc))


def markdown_chunks(doc: str) -> list[Chunk]:
    sections = MarkdownHeaderTextSplitter(HEADERS, strip_headers=False).split_text(doc)
    inner = _recursive_splitter(overlap=0)
    pieces, heads = [], []
    for sec in sections:
        hp = " > ".join(sec.metadata[k] for k in ("h1", "h2", "h3") if k in sec.metadata) or None
        for part in inner.split_text(sec.page_content):
            # merge tiny fragments (e.g. a lone heading) into the previous chunk of the same section
            if pieces and len(part) < MIN_CHUNK and heads[-1] == hp and len(pieces[-1]) + len(part) <= CHUNK_SIZE:
                pieces[-1] += "\n\n" + part
            else:
                pieces.append(part)
                heads.append(hp)
    return _build(doc, pieces, heads)


SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z`*\[])|\n{2,}|\n(?=#{1,6}\s|[-*]\s|\d+\.\s|```)")


def semantic_chunks(doc: str, embed_fn=None) -> list[Chunk]:
    """Greg Kamradt-style semantic chunking with a size cap.

    1. split into sentences/blocks  2. embed each with a 1-sentence context window
    3. cosine distance between neighbours  4. break at distances above the percentile
    """
    if embed_fn is None:
        from .embed import embed_passages as embed_fn
    sents = [s.strip() for s in SENT_SPLIT.split(doc) if s and s.strip()]
    if len(sents) <= 2:
        return _build(doc, ["\n".join(sents)])
    windows = [" ".join(sents[max(0, i - 1): i + 2]) for i in range(len(sents))]
    vecs = np.asarray(embed_fn(windows))
    dist = 1.0 - np.sum(vecs[:-1] * vecs[1:], axis=1)       # vectors are normalised
    threshold = float(np.percentile(dist, SEMANTIC_PERCENTILE))

    pieces, cur = [], [sents[0]]
    for i in range(1, len(sents)):
        cur_len = sum(len(s) + 1 for s in cur)
        if (dist[i - 1] > threshold and cur_len >= MIN_CHUNK) or cur_len + len(sents[i]) > SEMANTIC_MAX:
            pieces.append("\n".join(cur))
            cur = []
        cur.append(sents[i])
    if cur:
        if pieces and sum(len(s) for s in cur) < MIN_CHUNK:
            pieces[-1] += "\n" + "\n".join(cur)
        else:
            pieces.append("\n".join(cur))
    return _build(doc, pieces)


def chunk(doc: str, strategy: str, embed_fn=None) -> list[Chunk]:
    if strategy == "fixed":
        return fixed_chunks(doc)
    if strategy == "recursive":
        return recursive_chunks(doc)
    if strategy == "markdown":
        return markdown_chunks(doc)
    if strategy == "semantic":
        return semantic_chunks(doc, embed_fn)
    raise ValueError(f"unknown strategy {strategy!r}; choose from {STRATEGIES}")
