# apiscope/repo/app.py

import shutil
from pathlib import Path

import typer

from apiscope.config import (
    CACHE_ROOT,
    DEFAULT_CONFIG_PATH,
    TMP_ROOT,
    Config,
    RepoEntryConfig,
    get_project_config_path,
)
from apiscope.repo.fetch import sync_entry
from apiscope.repo.schema import RepoCommandContext, RepoEntry

app = typer.Typer(help="sync documentation from git repositories")


# ==============================================================================
# public helpers
# ==============================================================================


def check_deps() -> str | None:
    if shutil.which("git") is None:
        return "git is required but not found in PATH"
    return None


# ==============================================================================
# helpers
# ==============================================================================


def _resolve_target(global_flag: bool) -> Path:
    if global_flag:
        return DEFAULT_CONFIG_PATH
    project = get_project_config_path()
    if project is not None and project.exists():
        return project
    return DEFAULT_CONFIG_PATH


# ==============================================================================
# callback
# ==============================================================================


@app.callback()
def repo_callback(
    ctx: typer.Context,
    global_flag: bool = typer.Option(
        False, "--global", "-g", help="edit global config instead of project config"
    ),
) -> None:
    # check required external tools
    err = check_deps()
    if err is not None:
        typer.echo(err, err=True)
        raise typer.Exit(code=1)

    # prepare cache directories
    repo_cache_dir = CACHE_ROOT / "repo"
    repo_tmp_dir = TMP_ROOT
    repo_cache_dir.mkdir(parents=True, exist_ok=True)
    repo_tmp_dir.mkdir(parents=True, exist_ok=True)

    # inject context for subcommands
    ctx.obj.repo_command_context = RepoCommandContext(
        cache_dir=repo_cache_dir,
        tmp_dir=repo_tmp_dir,
        global_flag=global_flag,
    )


# ==============================================================================
# commands
# ==============================================================================


@app.command(name="add", help="register a repo for syncing")
def add_repo(
    ctx: typer.Context,
    url: str = typer.Argument(help="git clone URL"),
    dir: str = typer.Argument(help="directory within repo to extract"),
    target: str = typer.Option(
        "branch:main", "--target", help="ref target (branch:, tag:, commit:)"
    ),
) -> None:
    # duplicate check against merged entries
    if url in ctx.obj.config.repo.entries:
        typer.echo(f"<{url}> already registered", err=True)
        raise typer.Exit(code=1)

    target_path = _resolve_target(ctx.obj.repo_command_context.global_flag)
    with Config.edit(target_path) as cfg:
        cfg.repo.entries[url] = RepoEntryConfig(dir=dir, target=target)

    typer.echo(f"registered <{url}>")


@app.command(name="remove", help="remove a registered repo")
def remove_repo(
    ctx: typer.Context,
    url: str = typer.Argument(help="git clone URL"),
) -> None:
    target_path = _resolve_target(ctx.obj.repo_command_context.global_flag)
    with Config.edit(target_path) as cfg:
        if url not in cfg.repo.entries:
            typer.echo(f"<{url}> not registered", err=True)
            raise typer.Exit(code=1)
        del cfg.repo.entries[url]

    typer.echo(f"removed <{url}>")


@app.command(name="list", help="list registered repos")
def list_repos(ctx: typer.Context) -> None:
    entries = RepoEntry.from_config(ctx.obj.config.repo)
    if not entries:
        typer.echo("no repos registered")
        return

    cache_dir = ctx.obj.repo_command_context.cache_dir

    for entry in entries:
        doc_path = cache_dir / entry.sha256_id
        typer.echo(f"- [{entry.url}] [{entry.target}@{entry.dir}] <{doc_path}>")


@app.command(name="sync", help="sync all registered repos to cache")
def sync_repos(
    ctx: typer.Context,
    force: bool = typer.Option(False, "--force", help="force re-sync ignoring cache TTL"),
) -> None:
    entries = RepoEntry.from_config(ctx.obj.config.repo)
    if not entries:
        typer.echo("no repos registered")
        return

    rc = ctx.obj.repo_command_context
    ttl = ctx.obj.config.repo.cache_ttl

    for entry in entries:
        err = sync_entry(entry, rc.tmp_dir, rc.cache_dir, force=force, ttl=ttl)
        if err is not None:
            typer.echo(f"sync failed for <{entry.url}>: {err}", err=True)
        else:
            typer.echo(f"synced <{entry.url}>")
