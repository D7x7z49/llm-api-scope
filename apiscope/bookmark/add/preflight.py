# apiscope/bookmark/add/preflight.py

from apiscope.bookmark.add.context import AddCommandContext
from apiscope.bookmark.store import ensure_bookmarks


# prepare the bookmark store before the write
def run_preflight(command_context: AddCommandContext) -> None:
    ensure_bookmarks(command_context.runtime)
