# promptscribe/cli.py
import click
from promptscribe import db
from promptscribe.session import start as start_session

@click.group()
def main():
    """PromptScribe CLI."""
    pass


@main.command()
def initdb():
    """Initialize the local database."""
    click.echo("Initializing database...")
    db.init_db()
    click.echo("Database initialized.")


@main.command()
@click.option("--name", default=None, help="Short name for the session.")
@click.option("--desc", default=None, help="Short user description.")
def record(name, desc):
    """Start a recording session."""
    click.echo("Starting recording session...")
    start_session(name=name, user_description=desc, register_db=True)


@main.command()
@click.argument("meta_path", type=click.Path(exists=True))
def insert(meta_path):
    """Insert session metadata into DB."""
    click.echo(f"Inserting session from {meta_path}")
    db.insert_session(meta_path)
    click.echo("Session inserted.")


@main.command()
@click.option("--limit", default=50, help="Number of entries to list.")
def list(limit):
    """List recorded sessions."""
    click.echo(f"Listing last {limit} sessions:")
    db.list_entries(limit=limit)


@main.command()
@click.argument("session_id")
@click.option("--summary", is_flag=True, help="Show only command outputs.")
@click.option("--tail", type=int, default=None, help="Show last N events.")
def view(session_id, summary, tail):
    """View or replay a recorded session."""
    from promptscribe import viewer
    viewer.display_session(session_id, summary=summary, tail=tail)


if __name__ == "__main__":
    main()
