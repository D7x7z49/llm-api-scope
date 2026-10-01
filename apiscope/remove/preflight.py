# apiscope/remove/preflight.py

from apiscope.errors import MessageError
from apiscope.remove.context import RemoveCommandContext


def run_preflight(command_context: RemoveCommandContext) -> None:
    runtime = command_context.runtime
    if not runtime.options.global_only and runtime.paths.project is None:
        raise MessageError("remove.error.project_required")
