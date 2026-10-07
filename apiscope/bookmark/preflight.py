# apiscope/bookmark/preflight.py

from apiscope.bookmark.store import ensure_bookmarks
from apiscope.context import RuntimeContext


# prepare the bookmark layer before a write subcommand
def prepare_store(runtime: RuntimeContext) -> None:
    ensure_bookmarks(runtime)
