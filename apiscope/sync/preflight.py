# apiscope/sync/preflight.py
from __future__ import annotations

import shutil
from collections.abc import Sequence

from apiscope.errors import MessageError
from apiscope.schema import SOURCE_SELECTOR_ALL, RuntimeSource
from apiscope.sync._lib.repo.constants import GIT_COMMAND
from apiscope.sync.context import SyncCommandContext


def run_preflight(
    command_context: SyncCommandContext,
    selected: Sequence[tuple[str, RuntimeSource]],
) -> None:
    if not any(source.doc_type == "repo" for _, source in selected):
        return
    if shutil.which(GIT_COMMAND) is None:
        raise MessageError(
            "sync.error.preflight.git_missing",
            {"target": _target(command_context)},
        )


def _target(command_context: SyncCommandContext) -> str:
    options = command_context.options
    if options.name is not None:
        return options.name
    if options.selector != SOURCE_SELECTOR_ALL:
        return f"{options.selector} sources"
    return "selected sources"
