# apiscope/skill/app.py

import typer

from apiscope.skill._usage import USAGE_TEXT
from apiscope.skill.docs import STRATEGY_GUIDE

app = typer.Typer(help="output usage guide for ai agents")


@app.callback(invoke_without_command=True)
def skill_callback() -> None:
    typer.echo("=== COMMAND REFERENCE ===")
    typer.echo()
    typer.echo(USAGE_TEXT)
    typer.echo()
    typer.echo("=== STRATEGY GUIDE ===")
    typer.echo()
    typer.echo(STRATEGY_GUIDE)
