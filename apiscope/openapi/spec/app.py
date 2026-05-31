# apiscope/openapi/spec/app.py

from pathlib import Path

import typer

from apiscope.config import (
    DEFAULT_CONFIG_PATH,
    Config,
    get_project_config_path,
)
from apiscope.openapi.spec.schema import SpecCommandContext

app = typer.Typer()


def _resolve_target(use_global: bool) -> Path:
    if use_global:
        return DEFAULT_CONFIG_PATH
    project_path = get_project_config_path()
    if project_path is not None and project_path.exists():
        return project_path
    return DEFAULT_CONFIG_PATH


# ==============================================================================
# commands
# ==============================================================================


@app.callback()
def spec_callback(
    ctx: typer.Context,
    global_flag: bool = typer.Option(
        False, "--global", "-g", help="edit global config instead of project config"
    ),
) -> None:
    ctx.obj.openapi_command_context.spec_command_context = SpecCommandContext(
        global_flag=global_flag
    )


@app.command(name="list")
def list_aliases(ctx: typer.Context) -> None:
    aliases: dict[str, str] = {}

    # global config
    if DEFAULT_CONFIG_PATH.exists():
        cfg = Config.model_validate_json(DEFAULT_CONFIG_PATH.read_text())
        aliases |= cfg.openapi.alias

    # project config (overrides global)
    project_path = get_project_config_path()
    if project_path is not None and project_path.exists():
        cfg = Config.model_validate_json(project_path.read_text())
        aliases |= cfg.openapi.alias

    if not aliases:
        typer.echo("(no aliases)")
        return
    for name, source in aliases.items():
        typer.echo(f"{name} = {source}")


@app.command(name="add")
def add_alias(ctx: typer.Context, alias: str, source: str) -> None:
    context = ctx.obj.openapi_command_context.spec_command_context
    target = _resolve_target(context.global_flag)

    with Config.edit(target) as cfg:
        if alias in cfg.openapi.alias:
            typer.echo(f"alias [{alias}] already exists", err=True)
            raise typer.Exit(code=1)
        cfg.openapi.alias[alias] = source
    typer.echo(f"added [{alias}]")


@app.command(name="remove")
def remove_alias(ctx: typer.Context, alias: str) -> None:
    context = ctx.obj.openapi_command_context.spec_command_context
    target = _resolve_target(context.global_flag)

    with Config.edit(target) as cfg:
        if alias not in cfg.openapi.alias:
            typer.echo(f"alias [{alias}] not found", err=True)
            raise typer.Exit(code=1)
        del cfg.openapi.alias[alias]
    typer.echo(f"removed [{alias}]")
