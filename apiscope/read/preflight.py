# apiscope/read/preflight.py

from apiscope.read.context import ReadCommandContext


# read reads the cache and needs no command-specific assets.
def run_preflight(command_context: ReadCommandContext) -> None:
    del command_context
