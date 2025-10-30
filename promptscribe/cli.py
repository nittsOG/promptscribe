# promptscribe/cli.py
import click
import traceback
from promptscribe import db, __version__
from promptscribe.session import start as start_session


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show current PromptScribe version and exit.")
@click.option("--debug", is_flag=True, help="Enable verbose debug mode for troubleshooting.")
@click.pass_context
def main(ctx, version, debug):
    """
    PromptScribe CLI - Record, manage, and analyze terminal sessions.

    Usage:
        promptscribe [COMMAND] [OPTIONS]

    Command Categories:
        Database Management
            initdb           Initialize or repair the local database.
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
        --debug             Enable verbose debug tracebacks.
        --version           Show current version and exit.
        -h, --help          Show this help message and exit.
    """
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug

    if version:
        click.echo(f"PromptScribe v{__version__}")
        return

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# --------------------- DATABASE COMMANDS --------------------- #
@main.command()
@click.pass_context
def initdb(ctx):
    """Initialize or repair the local database."""
    try:
        click.echo("Initializing database...")
        db.init_db()
        click.echo("Database initialized successfully.")
    except Exception as e:
        click.echo(f"Database initialization failed: {e}")
        if ctx.obj.get("DEBUG"):
            traceback.print_exc()


@main.command()
@click.argument("meta_path", type=click.Path(exists=True))
@click.pass_context
def insert(ctx, meta_path):
    """Insert session metadata into the database."""
    try:
        click.echo(f"Inserting session from: {meta_path}")
        db.insert_session(meta_path)
        click.echo("Session inserted successfully.")
    except Exception as e:
        click.echo(f"Insertion failed: {e}")
        if ctx.obj.get("DEBUG"):
            traceback.print_exc()


@main.command()
@click.option("--limit", default=50, help="Number of entries to list.")
@click.option("--show-missing", is_flag=True, help="Include missing/deleted entries.")
@click.pass_context
def list(ctx, limit, show_missing):
    """List recorded sessions stored in the database."""
    try:
        click.echo(f"Listing last {limit} sessions:")
        db.list_entries(limit=limit, show_missing=show_missing)
    except Exception as e:
        click.echo(f"Listing failed: {e}")
        if ctx.obj.get("DEBUG"):
            traceback.print_exc()


@main.command()
@click.option("--remove", is_flag=True, help="Remove orphaned database entries.")
@click.pass_context
def clean(ctx, remove):
    """Find and optionally remove database entries whose log files are missing."""
    try:
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
    except Exception as e:
        click.echo(f"Clean operation failed: {e}")
        if ctx.obj.get("DEBUG"):
            traceback.print_exc()


# --------------------- RECORDING COMMANDS --------------------- #
@main.command()
@click.option("--name", default=None, help="Short name for the session.")
@click.option("--desc", default=None, help="Short user description.")
@click.pass_context
def record(ctx, name, desc):
    """Start a new recording session."""
    try:
        click.echo("Starting recording session...")
        start_session(name=name, user_description=desc, register_db=True)
    except Exception as e:
        click.echo(f"Recording failed: {e}")
        if ctx.obj.get("DEBUG"):
            traceback.print_exc()


@main.command()
@click.argument("session_id")
@click.option("--summary", is_flag=True, help="Show only command outputs.")
@click.option("--tail", type=int, default=None, help="Show last N events.")
@click.pass_context
def view(ctx, session_id, summary, tail):
    """View or replay a recorded session."""
    try:
        from promptscribe import viewer
        viewer.display_session(session_id, summary=summary, tail=tail)
    except Exception as e:
        click.echo(f"View failed: {e}")
        if ctx.obj.get("DEBUG"):
            traceback.print_exc()


@main.command()
@click.argument("session_id")
@click.option("--update-db", is_flag=True, help="Store summary into the database.")
@click.pass_context
def preprocess(ctx, session_id, update_db):
    """Preprocess and summarize a session log."""
    import os
    from promptscribe import preprocess

    try:
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
    except Exception as e:
        click.echo(f"Preprocessing failed: {e}")
        if ctx.obj.get("DEBUG"):
            traceback.print_exc()


@main.command()
@click.argument("session_id", required=False)
@click.option("--name", default=None, help="Custom name for the exported file.")
@click.option("--desc", default=None, help="Add or override description in export header.")
@click.option("--out", "out_path", default=None, help="Custom output file path.")
@click.pass_context
def scrape(ctx, session_id, name, desc, out_path):
    """Export raw terminal transcript for a session."""
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
        click.echo(f"Scrape failed: {e}")
        if ctx.obj.get("DEBUG"):
            traceback.print_exc()


# --------------------- ANALYTICS COMMANDS --------------------- #
@main.command()
@click.option("--limit", default=200, help="Scan last N sessions (DB order).")
@click.option("--top", default=10, help="Show top N sessions by command count.")
@click.option("--csv", "csv_out", is_flag=True, help="Export full stats table to CSV.")
@click.option("--csv-path", default=None, help="Custom CSV destination path (optional).")
@click.pass_context
def stats(ctx, limit, top, csv_out, csv_path):
    """Show aggregate statistics and optionally export them to CSV."""
    try:
        from promptscribe import stats as stats_mod
        stats_mod.show_stats(limit=limit, top=top, csv_out=csv_out, csv_path=csv_path)
    except Exception as e:
        click.echo(f"Stats computation failed: {e}")
        if ctx.obj.get("DEBUG"):
            traceback.print_exc()


# --------------------- INTERFACE COMMAND --------------------- #
@main.command()
@click.pass_context
def gui(ctx):
    """Launch the PromptScribe graphical interface."""
    try:
        from promptscribe import gui
        gui.launch_gui()
    except Exception as e:
        click.echo(f"GUI launch failed: {e}")
        if ctx.obj.get("DEBUG"):
            traceback.print_exc()


# --------------------- ENTRY POINT --------------------- #
if __name__ == "__main__":
    main()
