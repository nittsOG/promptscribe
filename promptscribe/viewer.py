# promptscribe/viewer.py
import os
import json
from rich.console import Console
from rich.table import Table
from promptscribe import db

console = Console()

def _load_logfile(path):
    if not os.path.exists(path):
        console.print(f"[red]Log file not found:[/red] {path}")
        return []
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def display_session(session_id, summary=False, tail=None):
    """Display or replay a recorded session from its ID."""
    session = None
    session_db = db.SessionLocal()
    try:
        session = session_db.query(db.SessionEntry).filter_by(id=session_id).first()
    finally:
        session_db.close()

    if not session:
        console.print(f"[red]No session found with ID:[/red] {session_id}")
        return

    events = _load_logfile(session.file)
    if not events:
        console.print(f"[yellow]No recorded data in:[/yellow] {session.file}")
        return

    if tail is not None:
        events = events[-tail:]

    console.rule(f"[bold cyan]Session Replay[/bold cyan] - {session.name or session_id}")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Timestamp", width=20)
    table.add_column("Type", width=10)
    table.add_column("Content", overflow="fold")

    for e in events:
        ts = f"{e.get('ts', 0):.3f}"
        kind = e.get("kind", "")
        data = e.get("data", "").strip()
        if summary and kind != "out":
            continue
        table.add_row(ts, kind, data)

    console.print(table)
    console.rule("[green]End of Session[/green]")
