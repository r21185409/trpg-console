"""Session-id persistence for Claude Code CLI continuity.

Claude Code CLI semantics:
  --session-id <uuid>  → CREATES a new session with that id. Errors if id exists.
  --resume <uuid>      → RESUMES an existing session.

So we track whether each session id has been initialized yet, and pick the
right flag on each call.
"""
import json
import uuid
from pathlib import Path
from typing import Tuple

from config import CAMPAIGNS_DIR

_FILE = "_session.json"


def _f() -> Path:
    return CAMPAIGNS_DIR / _FILE


def get_session() -> Tuple[str, bool]:
    """Return (session_id, is_new). is_new=True means the next CLI call should
    use --session-id (create). False means use --resume (continue)."""
    f = _f()
    if f.exists():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sid = data.get("id")
            if sid:
                return sid, not bool(data.get("initialized"))
        except Exception:
            pass
    CAMPAIGNS_DIR.mkdir(parents=True, exist_ok=True)
    sid = str(uuid.uuid4())
    f.write_text(json.dumps({"id": sid, "initialized": False}), encoding="utf-8")
    return sid, True


def mark_initialized() -> None:
    """Call once the CLI has successfully created the session with --session-id."""
    f = _f()
    if not f.exists():
        return
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return
    data["initialized"] = True
    f.write_text(json.dumps(data), encoding="utf-8")


def reset_session() -> Tuple[str, bool]:
    f = _f()
    if f.exists():
        f.unlink()
    # Also nuke any legacy file from the previous schema
    legacy = CAMPAIGNS_DIR / "_session.id"
    if legacy.exists():
        legacy.unlink()
    return get_session()
