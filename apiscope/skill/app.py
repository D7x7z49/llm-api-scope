# apiscope/skill/app.py

from pathlib import Path

import typer

from apiscope.skill._usage import USAGE_TEXT
from apiscope.skill.docs import INSTALL_MD, STRATEGY_GUIDE

app = typer.Typer(help="output usage guide for ai agents")


# ==============================================================================
# callback
# ==============================================================================


@app.callback(invoke_without_command=True)
def skill_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is not None:
        return

    typer.echo("=== COMMAND REFERENCE ===")
    typer.echo()
    typer.echo(USAGE_TEXT)
    typer.echo()
    typer.echo("=== STRATEGY GUIDE ===")
    typer.echo()
    typer.echo(STRATEGY_GUIDE)


# ==============================================================================
# commands
# ==============================================================================


@app.command(name="install", help="install SKILL.md for code agent")
def install(
    target: str | None = typer.Argument(None, help="install directory (default: ~/.agents/skills)"),
) -> None:
    if target is None:
        target = str(Path.home() / ".agents" / "skills")

    target_path = Path(target).expanduser().resolve()
    skill_path = target_path / "apiscope" / "SKILL.md"

    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(INSTALL_MD)

    typer.echo(f"installed: {skill_path}")
