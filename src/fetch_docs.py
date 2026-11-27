"""Phase 2 - fetch ~30 official Kubernetes docs and build data/manifest.csv

Usage:
    python -m src.fetch_docs              # git sparse clone (preferred)
    python -m src.fetch_docs --mode raw   # fallback: download preferred files over HTTPS

Source : https://github.com/kubernetes/website  (content/en/docs/concepts/...)
License: Kubernetes documentation is CC BY 4.0. Department restrictions are FICTIONAL.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

import requests

from .config import DATA_DIR, settings
from .log_setup import setup_logging

BASE = "content/en/docs/concepts"
LICENSE = "CC BY 4.0"
RAW_DIR = DATA_DIR / "raw"
SPARSE_DIR = DATA_DIR / "_k8s_sparse"          # git-ignored working clone
MANIFEST = DATA_DIR / "manifest.csv"

# category -> (source folder, access_class, target count, preferred files in priority order)
PLAN: dict[str, tuple[str, str, int, list[str]]] = {
    "app": ("workloads", "application", 10, [
        "workloads/controllers/deployment.md", "workloads/controllers/replicaset.md",
        "workloads/controllers/statefulset.md", "workloads/controllers/daemonset.md",
        "workloads/controllers/job.md", "workloads/controllers/cron-jobs.md",
        "workloads/pods/_index.md", "workloads/pods/pod-lifecycle.md",
        "workloads/pods/init-containers.md", "workloads/pods/disruptions.md",
    ]),
    "plat": ("storage", "platform", 10, [
        "storage/persistent-volumes.md", "storage/volumes.md", "storage/storage-classes.md",
        "storage/dynamic-provisioning.md", "storage/volume-snapshots.md",
        "storage/volume-snapshot-classes.md", "storage/ephemeral-volumes.md",
        "storage/projected-volumes.md", "storage/storage-capacity.md", "storage/volume-pvc-datasource.md",
    ]),
    "sec": ("security", "security", 5, [
        "security/rbac-good-practices.md", "security/pod-security-standards.md",
        "security/secrets-good-practices.md", "security/security-checklist.md",
        "security/controlling-access.md",
    ]),
    "shr": ("overview", "shared", 5, [
        "overview/components.md", "overview/_index.md", "overview/kubernetes-api.md",
        "overview/working-with-objects/_index.md", "overview/working-with-objects/namespaces.md",
    ]),
}


# ---------------------------------------------------------------- helpers
def run(cmd: list[str], cwd: Path | None = None) -> str:
    print("  $", " ".join(cmd))
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip())
    return res.stdout.strip()


def title_of(text: str, fallback: str) -> str:
    m = re.search(r"^title:\s*['\"]?(.+?)['\"]?\s*$", text, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def url_of(rel: str) -> str:
    """concepts/workloads/controllers/deployment.md -> https://kubernetes.io/docs/concepts/workloads/controllers/deployment/"""
    path = rel.removesuffix(".md")
    path = path.removesuffix("/_index").removesuffix("_index")
    return f"https://kubernetes.io/docs/concepts/{path.strip('/')}/"


def pick(available: list[str], preferred: list[str], n: int) -> list[str]:
    """Preferred files that exist first, then fill alphabetically from the same folder."""
    chosen = [p for p in preferred if p in available]
    for p in sorted(available):
        if len(chosen) >= n:
            break
        if p not in chosen:
            chosen.append(p)
    return chosen[:n]


# ---------------------------------------------------------------- sources
def sparse_clone() -> tuple[dict[str, str], str]:
    if shutil.which("git") is None:
        raise RuntimeError("git not found on PATH")
    if not (SPARSE_DIR / ".git").exists():
        SPARSE_DIR.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
             "--branch", settings.k8s_ref, settings.k8s_repo_url, str(SPARSE_DIR)])
    folders = [f"{BASE}/{v[0]}" for v in PLAN.values()]
    run(["git", "sparse-checkout", "set", *folders], cwd=SPARSE_DIR)
    commit = run(["git", "rev-parse", "HEAD"], cwd=SPARSE_DIR)
    root = SPARSE_DIR / BASE
    files = {p.relative_to(root).as_posix(): p.read_text(encoding="utf-8")
             for p in root.rglob("*.md")}
    return files, commit


def raw_download() -> tuple[dict[str, str], str]:
    """Fallback without git: fetch only the preferred files."""
    repo = settings.k8s_repo_url.removesuffix(".git").replace("https://github.com/", "")
    files: dict[str, str] = {}
    for _, (_, _, _, pref) in PLAN.items():
        for rel in pref:
            url = f"https://raw.githubusercontent.com/{repo}/{settings.k8s_ref}/{BASE}/{rel}"
            r = requests.get(url, timeout=30)
            print(f"  GET {rel} -> {r.status_code}")
            if r.ok:
                files[rel] = r.text
    return files, settings.k8s_ref


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["git", "raw"], default="git")
    args = ap.parse_args()

    print(f"Fetching Kubernetes docs via {args.mode} ...")
    try:
        files, commit = sparse_clone() if args.mode == "git" else raw_download()
    except Exception as exc:
        sys.exit(f"Fetch failed: {exc}\nTry: python -m src.fetch_docs --mode raw  (or set HTTPS_PROXY in .env)")

    if RAW_DIR.exists():
        shutil.rmtree(RAW_DIR)
    rows = []
    for prefix, (folder, access, n, pref) in PLAN.items():
        available = [k for k in files if k.startswith(folder + "/")]
        chosen = pick(available, pref, n)
        if len(chosen) < n:
            print(f"  WARNING: only {len(chosen)}/{n} files found for {folder}")
        for i, rel in enumerate(chosen, 1):
            text = files[rel]
            doc_id = f"{prefix}-{i:03d}"
            local = RAW_DIR / access / f"{doc_id}__{rel.replace('/', '__')}"
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text(text, encoding="utf-8")
            rows.append({
                "doc_id": doc_id,
                "title": title_of(text, Path(rel).stem),
                "access_class": access,
                "source_path": f"{BASE}/{rel}",
                "source_url": url_of(rel),
                "github_url": f"https://github.com/kubernetes/website/blob/{commit}/{BASE}/{rel}",
                "local_path": local.relative_to(DATA_DIR.parent).as_posix(),
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
                "char_len": len(text),
                "license": LICENSE,
            })

    with MANIFEST.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # Attribution file for the README
    lines = ["# Dataset attribution", "",
             f"Source: https://github.com/kubernetes/website (commit `{commit}`)  ",
             f"License: Kubernetes documentation, {LICENSE} - (c) The Kubernetes Authors.  ",
             "Department access restrictions are fictional, for an educational exercise only.", "",
             "| doc_id | access | title | source |", "|---|---|---|---|"]
    lines += [f"| {r['doc_id']} | {r['access_class']} | {r['title']} | [{r['source_path']}]({r['source_url']}) |"
              for r in rows]
    (DATA_DIR / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    by = {}
    for r in rows:
        by[r["access_class"]] = by.get(r["access_class"], 0) + 1
    print(f"\nSaved {len(rows)} docs -> {MANIFEST}")
    print("  " + ", ".join(f"{k}={v}" for k, v in by.items()))


if __name__ == "__main__":
    setup_logging("fetch_docs")
    main()
