# promptscribe/stats.py
import os
import csv
import datetime
from collections import Counter
from typing import Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from promptscribe import db
from promptscribe import parser

console = Console()


def _get_all_sessions(limit: int = 1000):
    s = db.SessionLocal()
    try:
        q = s.query(db.SessionEntry).order_by(db.SessionEntry.start_ts.desc()).limit(limit)
        return q.all()
    finally:
        s.close()


def session_command_count(session_entry) -> int:
    try:
        parsed = parser.parse_session(session_entry.file)
        return parsed["summary"]["total_commands"]
    except Exception:
        return 0


def aggregate_stats(limit: int = 500) -> Dict[str, Any]:
    sessions = _get_all_sessions(limit=limit)
    total_sessions = len(sessions)
    counts = []
    per_day = Counter()
    by_session = []

    for s in sessions:
        cnt = session_command_count(s)
        counts.append(cnt)
        ts = int(s.start_ts) if getattr(s, "start_ts", None) else None
        if ts:
            day = datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
            per_day[day] += 1
        by_session.append((s.id, s.name or "", cnt, s.file))

    avg_cmds = (sum(counts) / total_sessions) if total_sessions else 0
    return {
        "total_sessions": total_sessions,
        "total_commands": sum(counts),
        "avg_commands_per_session": round(avg_cmds, 2),
        "by_day": dict(per_day),
        "by_session": by_session,
    }


def _sparkline(values):
    """Convert list[int] -> simple unicode bar graph"""
    if not values:
        return ""
    chars = "▁▂▃▄▅▆▇█"
    lo, hi = min(values), max(values)
    span = hi - lo or 1
    return "".join(chars[int((v - lo) / span * (len(chars) - 1))] for v in values)


def export_csv(stats: Dict[str, Any], path: Optional[str] = None) -> str:
    """
    Export CSV to given path. If path is None, use default exports folder.
    Returns absolute path to saved CSV.
    """
    if path:
        out_path = os.path.abspath(path)
        out_dir = os.path.dirname(out_path)
        os.makedirs(out_dir, exist_ok=True)
    else:
        export_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "exports"))
        os.makedirs(export_dir, exist_ok=True)
        out_path = os.path.join(export_dir, f"stats_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv")

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["session_id", "name", "commands", "file"])
        for sid, name, cnt, path_ in stats["by_session"]:
            writer.writerow([sid, name, cnt, path_])
    return out_path


def show_stats(limit: int = 200, top: int = 10, csv_out: bool = False, csv_path: Optional[str] = None):
    stats = aggregate_stats(limit=limit)
    console.print(f"[bold]PromptScribe Activity (last {limit} sessions)[/bold]\n")

    # Summary
    t = Table()
    t.add_column("Metric", style="cyan")
    t.add_column("Value", style="magenta")
    t.add_row("Total sessions", str(stats["total_sessions"]))
    t.add_row("Total commands", str(stats["total_commands"]))
    t.add_row("Avg commands / session", str(stats["avg_commands_per_session"]))
    console.print(t)

    # Top sessions
    by_session = sorted(stats["by_session"], key=lambda x: x[2], reverse=True)
    top_table = Table(title=f"Top {top} sessions by command count")
    top_table.add_column("Session ID", style="cyan")
    top_table.add_column("Name")
    top_table.add_column("Commands", justify="right")
    top_table.add_column("Log file", overflow="fold")
    for sid, name, cnt, path in by_session[:top]:
        top_table.add_row(sid, name or "-", str(cnt), path)
    console.print(top_table)

    # Timeline + sparkline
    t2 = Table(title="Sessions per day (UTC)")
    t2.add_column("Date")
    t2.add_column("Sessions", justify="right")
    t2.add_column("Sparkline", justify="left")
    by_day_sorted = sorted(stats["by_day"].items(), reverse=True)
    counts = [cnt for _, cnt in by_day_sorted]
    spark = _sparkline(counts)
    # zip may be shorter, map spark chars to rows
    for i, (day, cnt) in enumerate(by_day_sorted):
        bar = spark[i] if i < len(spark) else ""
        t2.add_row(day, str(cnt), bar)
    console.print(t2)

    # CSV export (optional)
    if csv_out:
        path = export_csv(stats, path=csv_path)
        console.print(f"[green]✅ CSV exported to:[/green] {path}")
