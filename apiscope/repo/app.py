# apiscope/repo/app.py

import shutil

import typer

from apiscope.config import CACHE_ROOT, TMP_ROOT
from apiscope.repo.schema import RepoCommandContext

app = typer.Typer(help="sync documentation from git repositories")


# ==============================================================================
# public helpers
# ==============================================================================


def check_deps() -> str | None:
    if shutil.which("git") is None:
        return "git is required but not found in PATH"
    return None


# ==============================================================================
# callback
# ==============================================================================


@app.callback()
def repo_callback(ctx: typer.Context) -> None:
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
    pass


@app.command(name="remove", help="remove a registered repo")
def remove_repo(
    ctx: typer.Context,
    url: str = typer.Argument(help="git clone URL"),
) -> None:
    pass


@app.command(name="list", help="list registered repos")
def list_repos(ctx: typer.Context) -> None:
    pass


@app.command(name="sync", help="sync all registered repos to cache")
def sync_repos(
    ctx: typer.Context,
    force: bool = typer.Option(False, "--force", help="force re-sync ignoring cache TTL"),
) -> None:
    pass
