# apiscope/bookmark/remove/preflight.py

from apiscope.bookmark.remove.context import RemoveCommandContext
from apiscope.bookmark.store import ensure_bookmarks


# prepare the bookmark store before the write
def run_preflight(command_context: RemoveCommandContext) -> None:
    ensure_bookmarks(command_context.runtime)
