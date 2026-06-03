# apiscope/main.py
#
# structure convention:
#
#   subcommands live under apiscope/<group>/ as subdirectory packages.
#   each subdirectory contains:
#
#     app.py    — command definitions (typer.Typer app)
#     schema.py — context object for this command group (read-only contract)
#
#   parent callbacks inject ctx.obj with CommandContext(config=...).
#   subcommand callbacks extend ctx.obj.extras with group-specific keys.
#   schema.py exists solely to document the context shape — no runtime logic.

import json

import typer

from apiscope.config import (
    APP_NAME,
    CACHE_ROOT,
    DEFAULT_CONFIG_PATH,
    DEFAULT_ROOT,
    get_config,
    get_project_config_path,
)
from apiscope.openapi import openapi_app
from apiscope.repo import check_repo_deps, repo_app
from apiscope.rfc import check_rfc_deps, rfc_app
from apiscope.schema import CommandContext

# ==============================================================================
# app
# ==============================================================================

app = typer.Typer(
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
    help="a reader for network resources",
)

# ==============================================================================
# callback
# ==============================================================================


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        return
    ctx.obj = CommandContext(config=get_config())


# ==============================================================================
# subcommands
# ==============================================================================

app.add_typer(openapi_app, name="openapi")
app.add_typer(rfc_app, name="rfc")
app.add_typer(repo_app, name="repo")

# ==============================================================================
# commands
# ==============================================================================


@app.command(help="check that apiscope is installed and working")
def health(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="output as JSON"),
) -> None:
    # ensure directories exist
    DEFAULT_ROOT.mkdir(parents=True, exist_ok=True)
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)

    # gather issues from all modules
    issues: list[str] = []
    for label, check in [("rfc", check_rfc_deps), ("repo", check_repo_deps)]:
        err = check()
        if err is not None:
            issues.append(f"[{label}] {err}")

    # config paths
    global_cfg = str(DEFAULT_CONFIG_PATH) if DEFAULT_CONFIG_PATH.exists() else None
    project_path = get_project_config_path()
    project_cfg = str(project_path) if project_path and project_path.exists() else None

    if json_output:
        result: dict = {
            "home": str(DEFAULT_ROOT),
            "config": {"global": global_cfg, "project": project_cfg},
            "cache": str(CACHE_ROOT),
            "issues": issues,
        }
        typer.echo(json.dumps(result, ensure_ascii=False))
    else:
        typer.echo(f"[home] <{DEFAULT_ROOT}>")
        typer.echo(f"[config] global <{global_cfg or 'none'}>")
        typer.echo(f"[config] project <{project_cfg or 'none'}>")
        typer.echo(f"[cache] <{CACHE_ROOT}>")
        typer.echo("---")
        if issues:
            for msg in issues:
                typer.echo(f"[!] {msg}", err=True)
            raise typer.Exit(code=1)
        typer.echo(f"[+] {APP_NAME} is healthy")


# ==============================================================================
# entry point
# ==============================================================================

if __name__ == "__main__":
    app()
