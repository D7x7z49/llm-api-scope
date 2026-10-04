# apiscope/sync/app.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast, get_args

import typer
from pydantic import ValidationError

from apiscope.cache import (
    CACHE_CONTENT_DIRECTORY,
    CACHE_FORMAT_VERSION,
    CacheInspection,
    CacheMetadata,
    build_manifest,
    cache_path,
    inspect_cache,
    source_digest,
    staging_cache,
    write_manifest,
    write_metadata,
)
from apiscope.constants import MESSAGE_TEMPLATES as ROOT_MESSAGE_TEMPLATES
from apiscope.context import RuntimeContext
from apiscope.errors import MessageError
from apiscope.output import Report, emit_report
from apiscope.schema import SOURCE_SELECTOR_ALL, DocumentType, RuntimeSource, SourceSelector
from apiscope.sync._lib.errors import SourceError, SourceParseError
from apiscope.sync._lib.registry import fetch_source, parse_source
from apiscope.sync._lib.schema import ParsedSource
from apiscope.sync.constants import COMMAND_NAME, MESSAGE_TEMPLATES
from apiscope.sync.context import SyncCommandContext
from apiscope.sync.preflight import run_preflight
from apiscope.sync.schema import SyncOptions

# ==============================================================================
# constants
# ==============================================================================


_MESSAGE_TEMPLATES = {**ROOT_MESSAGE_TEMPLATES, **MESSAGE_TEMPLATES}

_SELECTORS = frozenset({SOURCE_SELECTOR_ALL, *get_args(DocumentType)})

# ==============================================================================
# app
# ==============================================================================


app = typer.Typer(
    name=COMMAND_NAME,
    help=MESSAGE_TEMPLATES["sync.help.command"],
    subcommand_metavar="",
    context_settings={"allow_interspersed_args": True},
)


# ==============================================================================
# types
# ==============================================================================


@dataclass(frozen=True, slots=True)
class SyncFailure:
    name: str
    error: MessageError


@dataclass(frozen=True, slots=True)
class SyncSummary:
    total: int
    synced: int
    skipped: int
    expired: tuple[str, ...]
    failures: tuple[SyncFailure, ...]


@dataclass(frozen=True, slots=True)
class SyncTarget:
    name: str
    source: RuntimeSource
    parsed: ParsedSource
    inspection: CacheInspection


# ==============================================================================
# callback
# ==============================================================================


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    selector: str = typer.Argument(..., help=MESSAGE_TEMPLATES["sync.help.argument.selector"]),
    name: str | None = typer.Argument(None, help=MESSAGE_TEMPLATES["sync.help.argument.name"]),
    force: bool = typer.Option(False, "--force", help=MESSAGE_TEMPLATES["sync.help.option.force"]),
) -> None:
    runtime_context = ctx.find_object(RuntimeContext)
    if runtime_context is None:
        raise MessageError("sync.error.runtime_context_unavailable")

    try:
        if selector not in _SELECTORS:
            raise MessageError("sync.error.invalid_selector", {"selector": selector})
        options = SyncOptions(selector=cast(SourceSelector, selector), name=name, force=force)
        command_context = SyncCommandContext(runtime=runtime_context, options=options)
        summary = _run_sync(command_context)
    except ValidationError as error:
        message = MessageError("sync.error.invalid_options")
        _emit_error(runtime_context, message)
        raise typer.Exit(code=1) from error
    except MessageError as error:
        _emit_error(runtime_context, error)
        raise typer.Exit(code=1) from error

    if summary.failures:
        if options.name is not None:
            failure_error = summary.failures[0].error
        else:
            failure_error = MessageError(
                "sync.error.partial_failed",
                {"failed": len(summary.failures), "total": summary.total},
            )
        _emit_error(runtime_context, failure_error)
        raise typer.Exit(code=1)

    meta = {
        "target": _target(options),
        "count": summary.total,
        "synced": summary.synced,
        "skipped": summary.skipped,
    }
    if summary.expired:
        # a bulk sync keeps the expired cache and leaves the refresh to the user
        meta["expired"] = ",".join(summary.expired)
    emit_report(
        Report(
            status="ok",
            scope=runtime_context.scope,
            action=COMMAND_NAME,
            meta=meta,
        ),
        output_format=runtime_context.options.output_format,
    )


# ==============================================================================
# sync orchestration
# ==============================================================================


def _run_sync(command_context: SyncCommandContext) -> SyncSummary:
    runtime = command_context.runtime
    options = command_context.options
    selected = _select_sources(runtime.config.source, options)
    if options.name is not None and not selected:
        raise MessageError("sync.error.name_not_found", {"name": options.name})

    targets: list[SyncTarget] = []
    failures: list[SyncFailure] = []
    for name, source in selected:
        try:
            targets.append(_prepare_sync_target(runtime, name, source))
        except MessageError as error:
            failures.append(SyncFailure(name=name, error=error))

    pending = [(target.name, target.source) for target in targets if not _should_skip(target.inspection, options)]
    run_preflight(command_context, pending)

    synced = 0
    skipped = 0
    expired: list[str] = []
    for target in targets:
        if _should_skip(target.inspection, options):
            skipped += 1
            if target.inspection.state == "expired":
                expired.append(target.name)
            continue
        try:
            _sync_target(runtime, target)
        except MessageError as error:
            failures.append(SyncFailure(name=target.name, error=error))
            continue
        synced += 1
    return SyncSummary(
        total=len(selected),
        synced=synced,
        skipped=skipped,
        expired=tuple(expired),
        failures=tuple(failures),
    )


# ==============================================================================
# source selection
# ==============================================================================


def _select_sources(
    sources: dict[str, RuntimeSource],
    options: SyncOptions,
) -> list[tuple[str, RuntimeSource]]:
    if options.name is not None:
        source = sources.get(options.name)
        if source is None:
            return []
        if options.selector != SOURCE_SELECTOR_ALL and source.doc_type != options.selector:
            raise MessageError(
                "sync.error.selector_conflict",
                {"name": options.name, "selector": options.selector},
            )
        return [(options.name, source)]
    selected = [
        (name, source)
        for name, source in sources.items()
        if options.selector == SOURCE_SELECTOR_ALL or source.doc_type == options.selector
    ]
    return sorted(selected, key=lambda item: (item[1].doc_type, item[0]))


# ==============================================================================
# cache synchronization
# ==============================================================================


def _prepare_sync_target(
    runtime: RuntimeContext,
    name: str,
    source: RuntimeSource,
) -> SyncTarget:
    try:
        base_dir = runtime.paths.project.root if runtime.paths.project is not None else Path.cwd()
        parsed = parse_source(source.doc_type, source.doc_src, base_dir=base_dir)
        cache_entry = cache_path(runtime.paths.home.cache, parsed.canonical)
        ttl_days = source.doc_ttl or runtime.config.setting.public.doc_ttl
        inspection = inspect_cache(
            cache_entry,
            ttl_days=ttl_days,
            expected_source=parsed.canonical,
            expected_doc_type=parsed.doc_type,
            expected_digest=source_digest(parsed.canonical),
        )
    except SourceError as error:
        raise _source_error_message(error) from error
    except MessageError:
        raise
    except (OSError, TypeError, ValueError, ValidationError) as error:
        raise MessageError("sync.error.cache_failed", {"name": name}) from error
    return SyncTarget(name=name, source=source, parsed=parsed, inspection=inspection)


def _sync_target(runtime: RuntimeContext, target: SyncTarget) -> None:
    try:
        with staging_cache(runtime.paths.home.cache, target.parsed.canonical) as staging:
            result = fetch_source(
                target.parsed,
                destination=staging,
                proxy=runtime.config.setting.local.proxy,
                no_proxy=runtime.config.setting.local.no_proxy,
            )
            if result.content_kind == "directory":
                write_manifest(staging, build_manifest(staging / CACHE_CONTENT_DIRECTORY))
            write_metadata(
                staging,
                CacheMetadata(
                    format_version=CACHE_FORMAT_VERSION,
                    doc_type=target.parsed.doc_type,
                    source=target.parsed.canonical,
                    source_digest=source_digest(target.parsed.canonical),
                    fetched_at=result.fetched_at,
                    content_kind=result.content_kind,
                    content_name=result.content_name,
                    content_digest=result.content_digest,
                ),
            )
    except SourceError as error:
        raise _source_error_message(error) from error
    except MessageError:
        raise
    except (OSError, TypeError, ValueError, ValidationError) as error:
        raise MessageError("sync.error.cache_failed", {"name": target.name}) from error


# ==============================================================================
# error translation
# ==============================================================================


def _source_error_message(error: SourceError) -> MessageError:
    code = f"sync.error.{error.reason_code}"
    values = dict(error.values)
    values["source"] = error.source
    if code not in MESSAGE_TEMPLATES:
        code = "sync.error.parse_failed" if isinstance(error, SourceParseError) else "sync.error.fetch_failed"
        if not isinstance(error, SourceParseError):
            values["reason"] = error.reason_code
    return MessageError(code, values)


# ==============================================================================
# report helpers
# ==============================================================================


def _should_skip(inspection: CacheInspection, options: SyncOptions) -> bool:
    if options.force:
        return False
    if inspection.state == "fresh":
        return True
    return inspection.state == "expired" and options.name is None


def _target(options: SyncOptions) -> str:
    if options.name is not None:
        return options.name
    if options.selector != SOURCE_SELECTOR_ALL:
        return f"type:{options.selector}"
    return SOURCE_SELECTOR_ALL


def _emit_error(runtime: RuntimeContext, error: MessageError) -> None:
    emit_report(
        Report(
            status="error",
            scope=runtime.scope,
            action=COMMAND_NAME,
            code=error.code,
            meta=error.values,
        ),
        output_format=runtime.options.output_format,
        message_templates=_MESSAGE_TEMPLATES,
    )
