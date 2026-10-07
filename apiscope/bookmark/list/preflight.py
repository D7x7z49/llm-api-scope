# apiscope/bookmark/list/preflight.py

from apiscope.bookmark.list.context import ListCommandContext


# list only reads the store, so it prepares nothing
def run_preflight(command_context: ListCommandContext) -> None:
    del command_context
