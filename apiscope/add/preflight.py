# apiscope/add/preflight.py

from apiscope.add.context import AddCommandContext
from apiscope.errors import MessageError


def run_preflight(command_context: AddCommandContext) -> None:
    runtime = command_context.runtime
    if not runtime.options.global_only and runtime.paths.project is None:
        raise MessageError("add.error.project_required")
