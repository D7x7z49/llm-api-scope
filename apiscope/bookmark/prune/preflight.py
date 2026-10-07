# apiscope/bookmark/prune/preflight.py

from apiscope.bookmark.preflight import prepare_store
from apiscope.bookmark.prune.context import PruneCommandContext


# prepare the bookmark layer before the write
def run_preflight(command_context: PruneCommandContext) -> None:
    prepare_store(command_context.runtime)
