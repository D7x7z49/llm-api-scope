# apiscope/list/preflight.py

from apiscope.list.context import ListCommandContext


# list reads the runtime config and needs no command-specific assets.
def run_preflight(command_context: ListCommandContext) -> None:
    del command_context
