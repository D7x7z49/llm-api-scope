# apiscope/view/preflight.py

from apiscope.view.context import ViewCommandContext


# view reads the cache and needs no command-specific assets.
def run_preflight(command_context: ViewCommandContext) -> None:
    del command_context
