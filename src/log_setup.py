"""Central logging: every script writes to ONE file, logs/app.log, with timestamps.

Call once at the start of a script:
    from .log_setup import setup_logging
    log = setup_logging("ingest")

What it does
  * creates the logs/ folder if missing
  * mirrors everything printed (stdout + stderr) into logs/app.log,
    each line prefixed:  2026-11-26 19:44:01 | ingest      | INFO  | message
  * keeps the console output unchanged (so screenshots still look normal)
  * records the command line at start, exit code / duration at end,
    and full tracebacks of uncaught errors
  * rotates at 5 MB (app.log -> app.log.1 ... app.log.5)
  * masks password=... values so secrets never reach the log file
"""
from __future__ import annotations

import atexit
import logging
import re
import sys
import time
from logging.handlers import RotatingFileHandler

from .config import ROOT

LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "app.log"
_SECRET = re.compile(r"(?i)(pass" + r"word\s*[=:]\s*)(\S+)")
_configured = False


class _Redact(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _SECRET.sub(r"\1****", str(record.msg))
        return True


class _Tee:
    """Write to the original stream AND log each completed line to the file."""

    def __init__(self, stream, logger: logging.Logger, level: int):
        self._stream, self._logger, self._level, self._buf = stream, logger, level, ""

    def write(self, data: str) -> int:
        self._stream.write(data)
        self._buf += data
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            if line.strip():
                self._logger.log(self._level, line.rstrip())
        return len(data)

    def flush(self) -> None:
        self._stream.flush()
        if self._buf.strip():
            self._logger.log(self._level, self._buf.rstrip())
        self._buf = ""

    def __getattr__(self, name):          # isatty, encoding, fileno, ...
        return getattr(self._stream, name)


def setup_logging(script: str) -> logging.Logger:
    global _configured
    logger = logging.getLogger("k8s_rag")
    if _configured:
        return logger
    LOG_DIR.mkdir(exist_ok=True)
    for _s in (sys.stdout, sys.stderr):          # Windows pipes default to cp1252
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        f"%(asctime)s | {script:<16} | %(levelname)-5s | %(message)s", "%Y-%m-%d %H:%M:%S"))
    handler.addFilter(_Redact())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # library warnings (psycopg, sentence-transformers, ...) go to the same file
    logging.captureWarnings(True)
    logging.getLogger("py.warnings").addHandler(handler)

    sys.stdout = _Tee(sys.stdout, logger, logging.INFO)
    sys.stderr = _Tee(sys.stderr, logger, logging.WARNING)

    t0 = time.perf_counter()
    logger.info("===== START  %s", " ".join(sys.argv))

    def _excepthook(exc_type, exc, tb):
        logger.error("Uncaught error", exc_info=(exc_type, exc, tb))
        sys.__excepthook__(exc_type, exc, tb)
    sys.excepthook = _excepthook

    def _end():
        for s in (sys.stdout, sys.stderr):
            try:
                s.flush()
            except Exception:
                pass
        logger.info("===== END    %.1fs", time.perf_counter() - t0)
    atexit.register(_end)

    _configured = True
    return logger
