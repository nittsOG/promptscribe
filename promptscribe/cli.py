# promptscribe/cli.py
import click
from promptscribe import db

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
