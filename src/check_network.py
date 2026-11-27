"""Pre-flight: can this machine reach GitHub and Hugging Face?  python -m src.check_network"""
from __future__ import annotations

import os

import requests

from . import config  # noqa: F401  (applies proxy / HF_ENDPOINT from .env)
from .log_setup import setup_logging

setup_logging("check_network")

hf = os.getenv("HF_ENDPOINT") or "https://huggingface.co"
TARGETS = {
    "GitHub (dataset)": "https://github.com/kubernetes/website",
    "Hugging Face (model)": f"{hf.rstrip('/')}/BAAI/bge-small-en-v1.5/resolve/main/config.json",
}

for name, url in TARGETS.items():
    try:
        r = requests.get(url, timeout=15)
        print(f"[{'PASS' if r.ok else 'FAIL'}] {name}: HTTP {r.status_code}")
    except Exception as exc:
        print(f"[FAIL] {name}: {type(exc).__name__}: {exc}")
        print("       -> set HTTPS_PROXY / HF_ENDPOINT in .env, or try another network")
