# promptscribe/preprocess.py
import os
from typing import Dict, Any
from promptscribe import parser


def compute_basic_stats(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Compute core metrics from parsed session."""
    commands = parsed.get("commands", [])
    total_cmds = len(commands)

    total_output_chars = sum(len(c["output"]) for c in commands)
    avg_output_size = total_output_chars / total_cmds if total_cmds else 0

    stats = {
        "total_commands": total_cmds,
        "total_output_chars": total_output_chars,
        "avg_output_chars": round(avg_output_size, 2),
        "top_longest_outputs": sorted(
            commands, key=lambda x: len(x["output"]), reverse=True
        )[:3],
    }
    return stats


def preprocess_session(session_path: str, update_db: bool = False) -> Dict[str, Any]:
    """
    Parse + summarize a single session log.
    Optionally update metadata in DB.
    """
    if not os.path.exists(session_path):
        raise FileNotFoundError(f"Missing session log: {session_path}")

    parsed = parser.parse_session(session_path)
    stats = compute_basic_stats(parsed)

    result = {
        "log_path": session_path,
        "summary": parsed["summary"],
        "stats": stats,
    }

    print("\n=== Session Preprocessing Summary ===")
    print(f"File: {session_path}")
    print(f"Total Commands: {stats['total_commands']}")
    print(f"Avg Output Size: {stats['avg_output_chars']}")
    print(f"Total Output Chars: {stats['total_output_chars']}")
    print("\nTop Longest Command Outputs:")
    for cmd in stats["top_longest_outputs"]:
        preview = cmd['input'].strip().split("\n")[0][:60]
        print(f"  > {preview}  ({len(cmd['output'])} chars)")

    if update_db:
        print("\nUpdating database with summary...")
        update_session_summary(session_path, stats)
        print("Database updated.")

    return result


def update_session_summary(session_path: str, stats: Dict[str, Any]):
    """Push summarized stats into database (if record exists)."""
    from sqlalchemy.orm import Session
    from promptscribe.db import SessionLocal, SessionEntry

    db_session: Session = SessionLocal()
    entry = db_session.query(SessionEntry).filter(SessionEntry.file == session_path).first()
    if entry:
        entry.name = entry.name or os.path.basename(session_path)
        entry.end_ts = entry.end_ts or entry.start_ts
        db_session.merge(entry)
        db_session.commit()
        db_session.close()
    else:
        print("⚠️  No DB entry found for this session. Skipping update.")
