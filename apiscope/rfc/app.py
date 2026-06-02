# apiscope/rfc/app.py

import shutil

import typer

from apiscope.rfc.schema import RfcCommandContext

app = typer.Typer(help="browse IETF RFC documents")


# ==============================================================================
# public helpers
# ==============================================================================


def check_deps() -> str | None:
    if shutil.which("rsync") is None:
        return "rsync is required but not found in PATH"
    return None


# ==============================================================================
# callback
# ==============================================================================


@app.callback()
def rfc_callback(ctx: typer.Context) -> None:
    err = check_deps()
    if err is not None:
        typer.echo(f"[!] {err}", err=True)
        raise typer.Exit(code=1)
    ctx.obj.rfc_command_context = RfcCommandContext()
