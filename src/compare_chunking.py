"""Phase 3 - compare the 4 chunking strategies on the SAME 30 documents.

Usage:
    python -m src.compare_chunking                 # all 4 strategies
    python -m src.compare_chunking --skip-semantic # quick run without the model

Outputs (evidence/):
    chunking_comparison.md / .csv   - per-strategy metrics table
    chunking_examples.md            - good vs poor boundary examples per strategy
    chunks_<strategy>.jsonl         - every chunk (reused by Phase 4 ingest)

Metrics
    total_chunks, avg/min/max/median size (chars), stdev
    overlap_avg        - mean characters shared between consecutive chunks (from offsets)
    heading_preserved  - % chunks that carry a heading path (traceable to a section)
    starts_at_heading  - % chunks whose text begins with a Markdown heading
    clean_end          - % chunks ending at a sentence/paragraph/code boundary
    mid_word_cut       - % chunks starting or ending inside a word (poor boundary)
    split_code_fence   - % chunks with an unbalanced ``` (code block cut in half)
    tiny_chunks        - % chunks shorter than 120 chars (low context)
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics as st
import time
from pathlib import Path

from tabulate import tabulate

from .chunkers import MIN_CHUNK, STRATEGIES, Chunk, chunk, clean
from .config import DATA_DIR, EVIDENCE_DIR, ROOT
from .log_setup import setup_logging


def load_docs() -> list[dict]:
    manifest = DATA_DIR / "manifest.csv"
    if not manifest.exists():
        raise SystemExit("data/manifest.csv missing - run: python -m src.fetch_docs")
    with manifest.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        raw = (ROOT / r["local_path"]).read_text(encoding="utf-8")
        r["text"] = clean(raw, r["title"])
    return rows


# ---------------------------------------------------------------- boundary checks
def _mid_word(doc: str, c: Chunk) -> bool:
    if c.start < 0:
        return False
    bad_start = c.start > 0 and doc[c.start - 1].isalnum() and doc[c.start].isalnum()
    bad_end = c.end < len(doc) and doc[c.end - 1].isalnum() and doc[c.end].isalnum()
    return bad_start or bad_end


def _clean_end(c: Chunk) -> bool:
    t = c.text.rstrip()
    return t.endswith((".", ":", "!", "?", "```", "|", ")")) or t.endswith("\n")


def _split_code(c: Chunk) -> bool:
    return c.text.count("```") % 2 == 1


def _overlap(chunks: list[Chunk]) -> list[int]:
    out = []
    for a, b in zip(chunks, chunks[1:]):
        if a.start >= 0 and b.start >= 0:
            out.append(max(0, a.end - b.start))
    return out


def pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 1) if d else 0.0


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-semantic", action="store_true")
    args = ap.parse_args()
    EVIDENCE_DIR.mkdir(exist_ok=True)

    docs = load_docs()
    print(f"Loaded {len(docs)} documents ({sum(len(d['text']) for d in docs):,} chars)")

    strategies = [s for s in STRATEGIES if not (args.skip_semantic and s == "semantic")]
    table, examples = [], {}

    for strat in strategies:
        t0 = time.perf_counter()
        all_chunks: list[tuple[dict, Chunk]] = []
        overlaps: list[int] = []
        with (EVIDENCE_DIR / f"chunks_{strat}.jsonl").open("w", encoding="utf-8") as out:
            for d in docs:
                cs = chunk(d["text"], strat)
                overlaps += _overlap(cs)
                for c in cs:
                    all_chunks.append((d, c))
                    out.write(json.dumps({"doc_id": d["doc_id"], "strategy": strat, "seq": c.seq,
                                          "heading_path": c.heading_path, "content": c.text,
                                          "char_len": c.size}, ensure_ascii=False) + "\n")
        secs = time.perf_counter() - t0
        sizes = [c.size for _, c in all_chunks]
        n = len(sizes)
        mid = [(d, c) for d, c in all_chunks if _mid_word(d["text"], c)]
        good = [(d, c) for d, c in all_chunks
                if c.text.lstrip().startswith("#") and _clean_end(c) and not _split_code(c)]
        bad = mid + [(d, c) for d, c in all_chunks if _split_code(c) and (d, c) not in mid]
        table.append({
            "strategy": strat, "total_chunks": n,
            "avg": round(st.mean(sizes)), "min": min(sizes), "median": round(st.median(sizes)),
            "max": max(sizes), "stdev": round(st.pstdev(sizes)),
            "overlap_avg": round(st.mean(overlaps)) if overlaps else 0,
            "heading_preserved_%": pct(sum(1 for _, c in all_chunks if c.heading_path), n),
            "starts_at_heading_%": pct(sum(1 for _, c in all_chunks if c.text.lstrip().startswith("#")), n),
            "clean_end_%": pct(sum(1 for _, c in all_chunks if _clean_end(c)), n),
            "mid_word_cut_%": pct(len(mid), n),
            "split_code_fence_%": pct(sum(1 for _, c in all_chunks if _split_code(c)), n),
            "tiny_chunks_%": pct(sum(1 for s in sizes if s < MIN_CHUNK), n),
            "seconds": round(secs, 1),
        })
        examples[strat] = (good[:1], bad[:2])
        print(f"  {strat:<10} {n:>5} chunks  avg {table[-1]['avg']:>4}  ({secs:.1f}s)")

    # ---- write table
    with (EVIDENCE_DIR / "chunking_comparison.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0].keys()))
        w.writeheader()
        w.writerows(table)
    md_table = tabulate(table, headers="keys", tablefmt="github")
    (EVIDENCE_DIR / "chunking_comparison.md").write_text(
        "# Chunking comparison (same 30 documents)\n\n"
        f"Parameters: size=800 chars, overlap=100 (fixed/recursive), min chunk=120, "
        f"semantic percentile=85, semantic cap=1200.\n\n{md_table}\n", encoding="utf-8")

    # ---- write boundary examples
    lines = ["# Chunk boundary examples", "",
             "Auto-selected. *Good* = starts at a heading, ends cleanly, code intact. "
             "*Poor* = cuts mid-word or splits a code block.", ""]
    for strat, (good, bad) in examples.items():
        lines.append(f"## {strat}")
        for label, items in (("Good", good), ("Poor", bad)):
            if not items:
                lines.append(f"_{label}: none found_\n")
            for d, c in items:
                snippet = c.text if c.size <= 500 else c.text[:220] + "\n...\n" + c.text[-220:]
                lines += [f"**{label}** - `{d['doc_id']}` seq {c.seq}, {c.size} chars, "
                          f"heading: `{c.heading_path}`", "", "```text", snippet, "```", ""]
    (EVIDENCE_DIR / "chunking_examples.md").write_text("\n".join(lines), encoding="utf-8")

    print("\n" + md_table)
    print(f"\nWrote {EVIDENCE_DIR / 'chunking_comparison.md'} and chunking_examples.md")


if __name__ == "__main__":
    setup_logging("compare_chunking")
    main()
