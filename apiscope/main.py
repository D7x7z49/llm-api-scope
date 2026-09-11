# apiscope/main.py

import typer

app = typer.Typer(
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
    help="read and cache structured documents from remote for LLM agents",
)


@app.callback()
def callback() -> None:
    pass
