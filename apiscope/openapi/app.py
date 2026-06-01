# apiscope/openapi/app.py

import json
from pathlib import Path
from typing import Any

import typer

from apiscope.config import CACHE_ROOT, Config
from apiscope.openapi.fetch import fetch_openapi_spec
from apiscope.openapi.reader import HttpMethod, OpenapiReader
from apiscope.openapi.schema import OpenapiCommandContext
from apiscope.openapi.spec import spec_app

app = typer.Typer(help="browse OpenAPI specifications")


# ==============================================================================
# helpers
# ==============================================================================


def _resolve_source(alias_or_source: str, config: Config) -> str:
    if alias_or_source in config.openapi.alias:
        return config.openapi.alias[alias_or_source]
    return alias_or_source


def _load_reader(source: str, cache_dir: Path, proxy: str | None = None) -> OpenapiReader:
    cached = fetch_openapi_spec(source, cache_dir, proxy)
    return OpenapiReader.load(cached)


def _get_reader(source: str, ctx: typer.Context) -> OpenapiReader:
    resolved = _resolve_source(source, ctx.obj.config)
    cache_dir = ctx.obj.openapi_command_context.cache_dir
    proxy = ctx.obj.config.openapi.proxy
    return _load_reader(resolved, cache_dir, proxy)


# ==============================================================================
# callback
# ==============================================================================


@app.callback()
def openapi_callback(ctx: typer.Context) -> None:
    cache_dir = CACHE_ROOT / "openapi"
    cache_dir.mkdir(parents=True, exist_ok=True)
    ctx.obj.openapi_command_context = OpenapiCommandContext(cache_dir=cache_dir)


# ==============================================================================
# operation commands
# ==============================================================================


@app.command(name="list", help="list operations from an OpenAPI spec")
def list_operations(
    ctx: typer.Context,
    source: str = typer.Argument(help="alias or path to the OpenAPI spec"),
    tag: str | None = typer.Option(default=None, help="filter by tag"),
    method: str | None = typer.Option(default=None, help="filter by HTTP method"),
) -> None:
    # load and resolve the spec
    reader = _get_reader(source, ctx)

    # collect all operations (path + method + identity fields)
    operations: list[dict[str, Any]] = []
    methods = set(m.value for m in HttpMethod)
    for path_name, path_item in reader.paths.items():
        for mthd in path_item:
            if mthd not in methods:
                continue
            # summary comes from the operation, not the path-item
            op = path_item[mthd]
            summary = op.get("summary", "")
            operation_id = op.get("operationId", "")
            tags = op.get("tags", [])

            # apply filters
            if tag is not None and tag not in tags:
                continue
            if method is not None and mthd != method:
                continue

            operations.append(
                {
                    "path": path_name,
                    "method": mthd,
                    "summary": summary,
                    "operationId": operation_id,
                    "tags": tags,
                }
            )

    typer.echo(json.dumps(operations, ensure_ascii=False))


@app.command(name="describe", help="describe a single operation")
def describe_operation(
    ctx: typer.Context,
    source: str = typer.Argument(help="alias or path to the OpenAPI spec"),
    path: str = typer.Argument(help="operation path"),
    method: str = typer.Argument(help="HTTP method"),
    request: bool = typer.Option(
        default=False, show_default=False, help="show only request fields, omit responses"
    ),
) -> None:
    # load and resolve the spec
    reader = _get_reader(source, ctx)

    # merge path-item parameters with operation parameters
    path_item = reader.paths.get(path, {})
    path_params = path_item.get("parameters", [])
    op = reader.get_operation(path, HttpMethod(method))
    op_params = op.get("parameters", [])

    # build resolved operation dict
    merged = {**op, "parameters": path_params + op_params}
    resolved = reader.resolve_ref(merged)

    # strip response fields when --request is set
    if request:
        resolved.pop("responses", None)
        # also drop any $ref key that resolved to a response-like structure

    typer.echo(json.dumps(resolved, ensure_ascii=False))


@app.command(name="info", help="show OpenAPI spec metadata")
def show_info(
    ctx: typer.Context,
    source: str = typer.Argument(help="alias or path to the OpenAPI spec"),
) -> None:
    reader = _get_reader(source, ctx)

    META_KEYS = ("openapi", "info", "servers", "tags", "security", "externalDocs")
    meta = {k: v for k, v in reader.raw.items() if k in META_KEYS}
    typer.echo(json.dumps(meta, ensure_ascii=False))


# ==============================================================================
# subcommands
# ==============================================================================

app.add_typer(spec_app, name="spec")
