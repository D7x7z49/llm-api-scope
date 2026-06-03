# apiscope/rfc/app.py

import json
import shutil

import typer

from apiscope.config import CACHE_ROOT
from apiscope.rfc.fetch import fetch_all_index_json, fetch_content_by_number
from apiscope.rfc.parse_xml import TocEntry
from apiscope.rfc.schema import ContentFormat, RfcCommandContext, RfcMetadata, RfcStatus
from apiscope.rfc.search import match_trigram, search_content

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
    # check required external tools
    err = check_deps()
    if err is not None:
        typer.echo(err, err=True)
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
# helpers
# ==============================================================================


def _print_toc_entry(entry: TocEntry, indent: int = 0) -> None:
    # root entry has no self line, skip directly to children
    if entry.id:
        prefix = "  " * indent
        typer.echo(f"{prefix}{entry.id}. {entry.title}")
    child_indent = indent + (1 if entry.id else 0)
    for child in entry.children:
        _print_toc_entry(child, child_indent)


def _show_page_info(content: str, number: int, rfc_ctx: RfcCommandContext) -> None:
    from apiscope.rfc.parse_txt import page_count

    total = page_count(content)
    path = rfc_ctx.get_content_txt_path(number)

    typer.echo(f"[TXT] rfc {number}  |  pages: 1-{total}")
    typer.echo("this document has no table of contents")
    typer.echo("use --page <number> to read a specific page")
    typer.echo(f"grep or ripgrep at <{path}>")


# ==============================================================================
# commands
# ==============================================================================


@app.command(name="sync", help="download RFC metadata index via rsync")
def sync_index(ctx: typer.Context) -> None:
    rfc_ctx = ctx.obj.rfc_command_context
    typer.echo("syncing via rsync...")
    err = fetch_all_index_json(rfc_ctx.index_json_dir)
    if err is not None:
        typer.echo(f"sync failed\n{err}", err=True)
        raise typer.Exit(code=1)
    typer.echo("done")


@app.command(name="info", help="show RFC metadata")
def show_info(
    ctx: typer.Context,
    number: int = typer.Argument(help="RFC number"),
    json_output: bool = typer.Option(False, "--json", help="output as JSON"),
) -> None:
    rfc_ctx = ctx.obj.rfc_command_context
    meta = rfc_ctx.get_index_json(number)
    if meta is None:
        typer.echo(f"rfc {number} not found", err=True)
        raise typer.Exit(code=1)

    # output raw JSON
    if json_output:
        typer.echo(meta.model_dump_json())
        return

    # human-readable entry
    typer.echo(f"[RFC-{number}]")
    for field_name, value in meta.to_info_data():
        # null/empty → (null)
        if value is None or (isinstance(value, str) and not value.strip()):
            formatted = "(null)"
        elif isinstance(value, list) and not value:
            formatted = "(null)"
        elif isinstance(value, list):
            formatted = "[" + ", ".join(str(v) for v in value) + "]"
        elif field_name == "abstract":
            formatted = str(value).replace("\r\n", " ").replace("\n", " ")
        else:
            formatted = str(value)
        typer.echo(f"{field_name}: {formatted}")


@app.command(name="read", help="show RFC content or table of contents")
def read_content(
    ctx: typer.Context,
    number: int = typer.Argument(help="RFC number"),
    section: str | None = typer.Option(None, "--section", help="extract by section id (XML only)"),
    page: int | None = typer.Option(None, "--page", help="extract by page number (TXT only)"),
    json_output: bool = typer.Option(False, "--json", help="output as JSON"),
) -> None:
    rfc_ctx = ctx.obj.rfc_command_context
    meta = rfc_ctx.get_index_json(number)
    if meta is None:
        typer.echo(f"rfc {number} not found", err=True)
        raise typer.Exit(code=1)

    # determine content format
    if meta.is_xml_format:
        fmt: ContentFormat = "xml"
        content_path = rfc_ctx.get_content_xml_path(number)
    elif meta.is_txt_format:
        fmt = "txt"
        content_path = rfc_ctx.get_content_txt_path(number)
    else:
        typer.echo(f"rfc {number} has no readable content format", err=True)
        raise typer.Exit(code=1)

    # ensure content is available locally
    if not content_path.exists():
        typer.echo(f"fetching <{content_path.name}> via rsync...")
        err = fetch_content_by_number(number, content_path.parent, fmt)
        if err is not None:
            typer.echo(f"failed to fetch content\n{err}", err=True)
            raise typer.Exit(code=1)

    content = content_path.read_text()

    # dispatch by format
    if section is not None and page is not None:
        typer.echo("--section and --page are mutually exclusive", err=True)
        raise typer.Exit(code=1)

    if fmt == "xml":
        if page is not None:
            typer.echo("--page is not available for XML format", err=True)
            raise typer.Exit(code=1)

        from apiscope.rfc.parse_xml import parse_xml_section, parse_xml_toc

        if section is not None:
            entry = parse_xml_section(content, section)
            if json_output:
                typer.echo(entry.model_dump_json(indent=2))
            elif entry.content is not None:
                typer.echo(entry.content)
            else:
                _print_toc_entry(entry)
        else:
            tree = parse_xml_toc(content)
            if json_output:
                typer.echo(tree.model_dump_json(indent=2))
            else:
                _print_toc_entry(tree)
        return

    if fmt == "txt":
        if section is not None:
            typer.echo("--section is not available for TXT format", err=True)
            typer.echo("use --page <number> to read a specific page", err=True)
            raise typer.Exit(code=1)

        from apiscope.rfc.parse_txt import extract_page

        if page is not None:
            try:
                page_content = extract_page(content, page)
            except ValueError:
                typer.echo(f"page {page} not found in rfc {number}", err=True)
                raise typer.Exit(code=1)
            if json_output:
                typer.echo(json.dumps({"page": page, "content": page_content}))
            else:
                typer.echo(page_content)
        else:
            _show_page_info(content, number, rfc_ctx)
        return


@app.command(name="search", help="search RFC index or fulltext")
def search_rfc(
    ctx: typer.Context,
    number: int | None = typer.Argument(None, help="RFC number for fulltext search"),
    term: str | None = typer.Argument(None, help="search term for fulltext search"),
    status: list[str] | None = typer.Option(None, "--status", "-s", help="filter by RFC status"),
    since: int | None = typer.Option(None, "--since", help="filter by start year"),
    until: int | None = typer.Option(None, "--until", help="filter by end year"),
    author: str | None = typer.Option(None, "--author", "-a", help="filter by author name"),
    title: str | None = typer.Option(None, "--title", "-t", help="filter by title keyword"),
    abstract: str | None = typer.Option(None, "--abstract", help="filter by abstract keyword"),
    keywords_field: str | None = typer.Option(None, "--keywords", help="filter by keywords field"),
    source: str | None = typer.Option(None, "--source", help="filter by source / working group"),
    context: int = typer.Option(1, "--context", "-C", help="lines of context around match"),
    no_snippet: bool = typer.Option(False, "--no-snippet", help="hide content snippet"),
    limit: int = typer.Option(20, "--limit", help="max results shown"),
    offset: int = typer.Option(0, "--offset", help="skip first N results"),
) -> None:
    rfc_ctx = ctx.obj.rfc_command_context
    # step 1: dispatch mode
    index_filters = [status, since, until, author, title, abstract, keywords_field, source]
    fulltext_mode = number is not None and term is not None
    index_mode = number is None and term is None

    if not fulltext_mode and not index_mode:
        typer.echo(
            "provide both NUMBER and TERM for fulltext search, or neither for index search",
            err=True,
        )
        raise typer.Exit(code=1)

    if fulltext_mode and any(index_filters):
        typer.echo(
            "filter flags only valid in index mode (search without a number)",
            err=True,
        )
        raise typer.Exit(code=1)

    if index_mode and (context != 1 or no_snippet):
        typer.echo(
            "--context and --no-snippet only valid in fulltext mode (search with a number)",
            err=True,
        )
        raise typer.Exit(code=1)

    # step 2: fulltext search
    if fulltext_mode:
        assert number is not None and term is not None
        meta = rfc_ctx.get_index_json(number)
        if meta is None:
            typer.echo(f"rfc {number} not found", err=True)
            raise typer.Exit(code=1)

        content_path = rfc_ctx.get_content_txt_path(number)
        if not content_path.exists():
            typer.echo(f"fetching <{content_path.name}> via rsync...")
            err = fetch_content_by_number(number, content_path.parent, "txt")
            if err is not None:
                typer.echo(f"failed to fetch content\n{err}", err=True)
                raise typer.Exit(code=1)

        if not content_path.exists():
            typer.echo(
                f"rfc {number} has no TXT content, fulltext search unavailable",
                err=True,
            )
            typer.echo("try reading with --section instead", err=True)
            raise typer.Exit(code=1)

        content = content_path.read_text()
        page_matches = search_content(content, term, context)

        if not page_matches:
            typer.echo(f"no matches for '{term}' in rfc {number}")
            return

        total_ft = len(page_matches)
        sliced_ft = page_matches[offset : offset + limit]

        for page, snippet in sliced_ft:
            if no_snippet:
                typer.echo(f"[RFC-{number}] page {page}")
            else:
                typer.echo(f"[RFC-{number}] page {page}")
                typer.echo(snippet)
                typer.echo()

        if total_ft > offset + limit:
            shown = offset + limit
            typer.echo(f"... ({shown} of {total_ft} matches shown, use --offset {shown} for more)")
        return

    # step 3: index search — scan all RFC metadata
    rfc_matches = []

    # validate status flags
    wanted_status: set[RfcStatus] = set()
    if status:
        for raw in status:
            s = RfcStatus.from_string(raw)
            if s is None:
                valid = ", ".join(f"{m.name.lower()}({m.value})" for m in RfcStatus)
                typer.echo(f"unknown status '{raw}'. available: {valid}", err=True)
                raise typer.Exit(code=1)
            wanted_status.add(s)

    for f in sorted(rfc_ctx.index_json_dir.glob("rfc*.json"), reverse=True):
        meta = RfcMetadata.from_json_file(f)

        # status filter
        if wanted_status and meta.status not in wanted_status:
            continue

        # date range filter
        if since is not None or until is not None:
            pub_date = meta.pub_date or ""
            year_str = pub_date.split()[-1] if pub_date else ""
            try:
                year = int(year_str)
            except (ValueError, IndexError):
                year = 0
            if since is not None and year < since:
                continue
            if until is not None and year > until:
                continue

        # string filters via trigram
        if author and not any(match_trigram(a, author) for a in meta.authors if a):
            continue
        if title and not match_trigram(meta.title or "", title):
            continue
        if abstract and not match_trigram(meta.abstract or "", abstract):
            continue
        if keywords_field and not any(match_trigram(k, keywords_field) for k in meta.keywords if k):
            continue
        if source and not match_trigram(meta.source or "", source):
            continue

        rfc_matches.append(meta)

    # step 4: print index results
    if not rfc_matches:
        typer.echo("no matching RFCs found")
        return

    total = len(rfc_matches)
    sliced = rfc_matches[offset : offset + limit]

    for meta in sliced:
        doc_id = (meta.doc_id or "").replace("RFC", "RFC-")
        authors = meta.authors[:3]
        authors_str = ", ".join(authors)
        if len(meta.authors) > 3:
            authors_str += ", et al."

        abstract_text = (meta.abstract or "").replace("\r\n", " ").replace("\n", " ")
        abstract_line = abstract_text.split(". ")[0] if abstract_text else ""
        if abstract_line and not abstract_line.endswith("."):
            abstract_line += "."

        typer.echo(f"[{doc_id}] {meta.title or ''}")
        typer.echo(f"  {meta.status or ''} | {meta.pub_date or ''} | {authors_str}")
        if abstract_line:
            typer.echo(f"  {abstract_line}")
        typer.echo()

    if total > offset + limit:
        shown = offset + limit
        typer.echo(f"... ({shown} of {total} results shown, use --offset {shown} for more)")
