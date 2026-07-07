"""Lightweight persistent tally of backstory-API usage.

Records how often visitors exercise the "use API" backstory feature and whether each request was
served by Ollama (local/cloud) or fell back to the deterministic template. Persists to a small JSON
file so the count survives process restarts within a container's life. On an ephemeral host (Render)
the file resets on each redeploy -- fine for rough traffic sampling. Best-effort: recording never
raises, so a read-only disk or bad file can't break backstory generation.

Thread-safe via a module-level lock. Production (render.yaml) serves under waitress, a SINGLE-process
multi-threaded server, so that lock serializes every read-modify-write and the tally is fully accurate
there. The lock does NOT span separate processes, so the local Docker/gunicorn setup (workers = 2) can
occasionally drop an increment when two workers write at once -- but that's dev-only and irrelevant for
a rough traffic gauge. Redis INCR would only buy cross-process atomicity we don't need here.
"""
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

_LOCK = threading.Lock()
_PATH = Path(os.getenv("USAGE_STATS_PATH",
                       Path(__file__).resolve().parent.parent / "usage_stats.json"))

_DEFAULT = {"total": 0, "ollama": 0, "template": 0, "first_seen": None, "last_seen": None}


def _load():
    try:
        return {**_DEFAULT, **json.loads(_PATH.read_text(encoding="utf-8"))}
    except (FileNotFoundError, ValueError, OSError):
        return dict(_DEFAULT)


def record_backstory(source):
    """Increment the tally for one backstory-API request.

    `source` is "ollama" (a model generated the prose) or "template" (fell back). Any other value
    still counts toward `total` but not the per-source breakdown. Never raises."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        with _LOCK:
            stats = _load()
            stats["total"] += 1
            if source in ("ollama", "template"):
                stats[source] += 1
            stats["first_seen"] = stats["first_seen"] or now
            stats["last_seen"] = now
            _PATH.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    except OSError:
        pass  # read-only FS / disk full -> silently skip; usage tally is non-critical


def snapshot():
    """Return the current tally as a dict (for a stats endpoint)."""
    with _LOCK:
        return _load()
