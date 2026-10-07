# apiscope/bookmark/prune/preflight.py

from apiscope.bookmark.prune.context import PruneCommandContext
from apiscope.bookmark.store import ensure_bookmarks


# prepare the bookmark store before the write
def run_preflight(command_context: PruneCommandContext) -> None:
    ensure_bookmarks(command_context.runtime)
