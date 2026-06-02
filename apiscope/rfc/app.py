# apiscope/rfc/app.py

import json
import shutil
import subprocess

import typer

from apiscope.config import CACHE_ROOT
from apiscope.rfc.schema import RfcCommandContext

# rsync module sources
RFC_RSYNC_HOST = "rsync.rfc-editor.org"
RFC_INDEX_MODULE = "rfcs-json-only"
RFC_CONTENT_MODULE = "rfcs"

# info output fields in display order
INFO_FIELDS = [
    "title",
    "authors",
    "pub_status",
    "pub_date",
    "abstract",
    "page_count",
    "doi",
    "obsoletes",
    "obsoleted_by",
    "updates",
    "updated_by",
]

app = typer.Typer(help="browse IETF RFC documents")


# ==============================================================================
# public helpers
# ==============================================================================


def check_deps() -> str | None:
    if shutil.which("rsync") is None:
        return "rsync is required but not found in PATH"
    return None


# ==============================================================================
# private helpers
# ==============================================================================


def _do_rsync(src: str, dst: str) -> str | None:
    """run rsync, return stderr on failure, None on success."""
    result = subprocess.run(
        ["rsync", "-az", "--delete", src, f"{dst}/"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return result.stderr.strip()
    return None


def _format_info_line(key: str, value: object) -> str:
    """format a single info field for human-readable output."""
    if isinstance(value, list):
        if not value:
            formatted = "(null)"
        else:
            formatted = "[" + ", ".join(str(v) for v in value) + "]"
    elif value is None or (isinstance(value, str) and not value.strip()):
        formatted = "(null)"
    elif key == "abstract":
        formatted = str(value).replace("\r\n", " ").replace("\n", " ")
    else:
        formatted = str(value)
    return f"{key}: {formatted}"


# ==============================================================================
# callback
# ==============================================================================


@app.callback()
def rfc_callback(ctx: typer.Context) -> None:
    # check required external tools
    err = check_deps()
    if err is not None:
        typer.echo(f"[!] {err}", err=True)
        raise typer.Exit(code=1)

    # prepare cache directories
    rfc_cache_dir = CACHE_ROOT / "rfc"
    index_json_dir = rfc_cache_dir / "index"
    content_xml_dir = rfc_cache_dir / "content" / "xml"
    content_txt_dir = rfc_cache_dir / "content" / "txt"
    index_json_dir.mkdir(parents=True, exist_ok=True)
    content_xml_dir.mkdir(parents=True, exist_ok=True)
    content_txt_dir.mkdir(parents=True, exist_ok=True)

    # inject context for subcommands
    ctx.obj.rfc_command_context = RfcCommandContext(
        index_json_dir=index_json_dir,
        content_xml_dir=content_xml_dir,
        content_txt_dir=content_txt_dir,
    )


# ==============================================================================
# commands
# ==============================================================================


@app.command(name="info", help="show RFC metadata")
def show_info(
    ctx: typer.Context,
    number: int = typer.Argument(help="RFC number"),
    json_output: bool = typer.Option(False, "--json", help="output as JSON"),
) -> None:
    rfc = ctx.obj.rfc_command_context
    path = rfc.get_index_json_path(number)
    # validate the cached index exists for this RFC
    if not path.exists():
        typer.echo(f"[!] rfc {number} not found", err=True)
        raise typer.Exit(code=1)
    data = json.loads(path.read_text())
    # output raw JSON
    if json_output:
        result = {k: data.get(k) for k in INFO_FIELDS}
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    # human-readable entry with fixed field order
    typer.echo(f"[RFC-{number}]")
    for key in INFO_FIELDS:
        typer.echo(_format_info_line(key, data.get(key)))


@app.command(name="sync", help="download RFC metadata index via rsync")
def sync_index(ctx: typer.Context) -> None:
    rfc = ctx.obj.rfc_command_context
    typer.echo("[*] downloading RFC metadata index via rsync...")
    # rsync rfcs-json-only module into local index cache
    err = _do_rsync(f"{RFC_RSYNC_HOST}::{RFC_INDEX_MODULE}", rfc.index_json_dir)
    if err is not None:
        typer.echo(f"[!] sync failed\n{err}", err=True)
        raise typer.Exit(code=1)
    typer.echo("[=] sync complete")
