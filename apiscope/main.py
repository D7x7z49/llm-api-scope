# apiscope/main.py

import typer

from apiscope.config import APP_NAME, get_config

app = typer.Typer(rich_markup_mode=None, pretty_exceptions_enable=False)


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    """A reader for network resources."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        return
    ctx.obj = get_config()


@app.command()
def health(ctx: typer.Context) -> None:
    """Check that apiscope is installed and working."""
    typer.echo(f"{APP_NAME} is healthy")


if __name__ == "__main__":
    app()
