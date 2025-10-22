import click

@click.group()
def main():
    """PromptScribe CLI."""
    pass

@main.command()
def record():
    print("Record session called")

@main.command()
def analyze():
    print("Analyze session called")

@main.command()
def list():
    print("List sessions called")

if __name__ == "__main__":
    main()
