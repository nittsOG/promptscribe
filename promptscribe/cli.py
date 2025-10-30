# promptscribe/cli.py
import click
from promptscribe import db
from promptscribe.session import start as start_session

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show current PromptScribe version and exit.")
@click.pass_context
def main(ctx, version):
    """
    PromptScribe CLI - Record, manage, and analyze terminal sessions.

    Usage:
        promptscribe [COMMAND] [OPTIONS]

    Command Categories:
        Database Management
            initdb           Initialize the local database.
            insert           Insert session metadata into the database.
            list             List recorded sessions.
            clean            Remove or view orphan database entries.

        Recording and Session Handling
            record           Start a new recording session.
            view             View or replay a recorded session.
            preprocess       Generate summaries and process logs.
            scrape           Export a raw terminal transcript.

        Analytics and Reporting
            stats            Show session statistics or export them to CSV.

        Interface
            gui              Launch the graphical interface.

    Global Options:
        --version           Show current version and exit.
        -h, --help          Show this help message and exit.

    Examples:
        promptscribe record --name "demo" --desc "System setup log"
        promptscribe list --limit 20
        promptscribe scrape <SESSION_ID> --name "exported_log"
        promptscribe stats --csv
        promptscribe gui
    """
    if version:
        click.echo("PromptScribe v1.0.0")
        return

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# --------------------- DATABASE COMMANDS --------------------- #
@main.command()
def initdb():
    """Initialize the local database."""
    click.echo("Initializing database...")
    db.init_db()
    click.echo("Database initialized successfully.")


@main.command()
@click.argument("meta_path", type=click.Path(exists=True))
def insert(meta_path):
    """Insert session metadata into the database."""
    click.echo(f"Inserting session from: {meta_path}")
    db.insert_session(meta_path)
    click.echo("Session inserted successfully.")


@main.command()
@click.option("--limit", default=50, help="Number of entries to list.")
@click.option("--show-missing", is_flag=True, help="Include missing/deleted entries.")
def list(limit, show_missing):
    """List recorded sessions stored in the database."""
    click.echo(f"Listing last {limit} sessions:")
    db.list_entries(limit=limit, show_missing=show_missing)


@main.command()
@click.option("--remove", is_flag=True, help="Remove orphaned database entries.")
def clean(remove):
    """Find and optionally remove database entries whose log files are missing."""
    from promptscribe import db as dbmod
    orphans = dbmod.clean_orphans(remove=remove)
    if not orphans:
        click.echo("No orphaned entries found.")
        return
    click.echo(f"Found {len(orphans)} orphaned entries:")
    for o in orphans:
        click.echo(f"  {o['id']}\t{o['name']}\t{o['file']}")
    if remove:
        click.echo("Orphaned entries removed.")


# --------------------- RECORDING COMMANDS --------------------- #
@main.command()
@click.option("--name", default=None, help="Short name for the session.")
@click.option("--desc", default=None, help="Short user description.")
def record(name, desc):
    """Start a new recording session."""
    click.echo("Starting recording session...")
    start_session(name=name, user_description=desc, register_db=True)


@main.command()
@click.argument("session_id")
@click.option("--summary", is_flag=True, help="Show only command outputs.")
@click.option("--tail", type=int, default=None, help="Show last N events.")
def view(session_id, summary, tail):
    """View or replay a recorded session."""
    from promptscribe import viewer
    viewer.display_session(session_id, summary=summary, tail=tail)


@main.command()
@click.argument("session_id")
@click.option("--update-db", is_flag=True, help="Store summary into the database.")
def preprocess(session_id, update_db):
    """Preprocess and summarize a session log."""
    import os
    from promptscribe import preprocess

    db_session = db.SessionLocal()
    entry = db_session.query(db.SessionEntry).filter(db.SessionEntry.id == session_id).first()
    db_session.close()

    if not entry:
        click.echo(f"No session found with ID: {session_id}")
        return

    path = entry.file
    if not os.path.exists(path):
        click.echo(f"Log file missing: {path}")
        return

    click.echo(f"Preprocessing session: {session_id}")
    preprocess.preprocess_session(path, update_db=update_db)
    click.echo("Preprocessing complete.")


@main.command()
@click.argument("session_id", required=False)
@click.option("--name", default=None, help="Custom name for the exported file.")
@click.option("--desc", default=None, help="Add or override description in export header.")
@click.option("--out", "out_path", default=None, help="Custom output file path.")
def scrape(session_id, name, desc, out_path):
    """
    Export raw terminal transcript for a session.

    Usage:
        promptscribe scrape [SESSION_ID] [OPTIONS]

    Options:
        --name TEXT        Custom name for the exported file.
        --desc TEXT        Add or override session description.
        --out PATH         Specify custom output file path.

    Examples:
        promptscribe scrape
        promptscribe scrape <SESSION_ID> --name mylog
        promptscribe scrape --desc "Exported from automation run"
    """
    from promptscribe import scraper
    try:
        out = scraper.export_raw(
            session_id=session_id,
            name=name,
            out_path=out_path,
            override_desc=desc
        )
        click.echo(f"Exported raw log to: {out}")
    except Exception as e:
        click.echo(f"Error: {e}")


# --------------------- ANALYTICS COMMANDS --------------------- #
@main.command()
@click.option("--limit", default=200, help="Scan last N sessions (DB order).")
@click.option("--top", default=10, help="Show top N sessions by command count.")
@click.option("--csv", "csv_out", is_flag=True, help="Export full stats table to CSV.")
@click.option("--csv-path", default=None, help="Custom CSV destination path (optional).")
def stats(limit, top, csv_out, csv_path):
    """Show aggregate statistics and optionally export them to CSV."""
    from promptscribe import stats as stats_mod
    stats_mod.show_stats(limit=limit, top=top, csv_out=csv_out, csv_path=csv_path)


# --------------------- INTERFACE COMMAND --------------------- #
@main.command()
def gui():
    """Launch the PromptScribe graphical interface."""
    from promptscribe import gui
    gui.launch_gui()


# --------------------- ENTRY POINT --------------------- #
if __name__ == "__main__":
    main()
