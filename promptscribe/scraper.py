# promptscribe/scraper.py
import os
import json
import time
from datetime import datetime
from typing import Optional
from promptscribe import db


EXPORT_DIR = None


def _ensure_export_dir():
    """Create and return the export directory path."""
    global EXPORT_DIR
    if EXPORT_DIR:
        return EXPORT_DIR
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "data", "exports")
    EXPORT_DIR = os.path.abspath(cfg_path)
    os.makedirs(EXPORT_DIR, exist_ok=True)
    return EXPORT_DIR


def _load_events(log_path):
    """Read and parse all JSONL events from a log file."""
    events = []
    if not os.path.exists(log_path):
        raise FileNotFoundError(log_path)
    with open(log_path, "r", encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                events.append(json.loads(ln))
            except Exception:
                # skip malformed lines
                continue
    return events


def _build_raw_text(events):
    """
    Reconstruct raw terminal transcript preserving input/output order and spacing.
    """
    out_lines = []
    buffer_out = []
    for evt in events:
        kind = evt.get("kind")
        data = evt.get("data", "")
        if kind == "in":
            # flush previous outputs
            if buffer_out:
                out_lines.extend(buffer_out)
                buffer_out = []
            for line in str(data).splitlines():
                out_lines.append(f"$ {line}")
        elif kind == "out":
            for line in str(data).splitlines():
                buffer_out.append(line)
    if buffer_out:
        out_lines.extend(buffer_out)
    return "\n".join(out_lines) + "\n"


def export_raw(
    session_id: Optional[str] = None,
    name: Optional[str] = None,
    out_path: Optional[str] = None,
    override_desc: Optional[str] = None,
):
    """
    Export raw terminal transcript for a given session.

    - If session_id is None → exports the most recent session.
    - `name` → optional user label used in output filename.
    - `override_desc` → optional header description override.
    - Returns absolute path to exported file.
    """
    # fetch session
    DB = db.SessionLocal()
    try:
        if session_id:
            entry = DB.query(db.SessionEntry).filter(db.SessionEntry.id == session_id).first()
        else:
            entry = DB.query(db.SessionEntry).order_by(db.SessionEntry.start_ts.desc()).first()
    finally:
        DB.close()

    if not entry:
        raise ValueError("No session found." if not session_id else f"No session with ID {session_id}")

    log_path = entry.file
    events = _load_events(log_path)
    raw_text = _build_raw_text(events)

    # load metadata if available
    stored_desc = ""
    try:
        meta_file = os.path.splitext(log_path)[0] + ".meta.json"
        if os.path.exists(meta_file):
            with open(meta_file, "r", encoding="utf-8") as mf:
                meta = json.load(mf)
                stored_desc = meta.get("user_description") or meta.get("description") or meta.get("name") or ""
    except Exception:
        pass

    # build description and header
    description = override_desc if override_desc is not None else stored_desc
    header = (
        "# PromptScribe Raw Terminal Log\n"
        f"# Session ID: {entry.id}\n"
        f"# Session Name: {entry.name or ''}\n"
        f"# Description: {description}\n"
        f"# Exported: {datetime.utcnow().isoformat()}Z\n\n"
    )

    # prepare output file path
    dest_dir = _ensure_export_dir()
    if out_path:
        out_full = os.path.abspath(out_path)
        os.makedirs(os.path.dirname(out_full), exist_ok=True)
    else:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_label = name or entry.name or "session"
        safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in safe_label)
        out_full = os.path.join(dest_dir, f"{safe_label}__{entry.id}__{ts}.txt")

    # atomic write
    tmp_path = out_full + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        fh.write(header)
        fh.write(raw_text)
    os.replace(tmp_path, out_full)

    return out_full
