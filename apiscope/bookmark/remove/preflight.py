# apiscope/bookmark/remove/preflight.py

from apiscope.bookmark.preflight import prepare_store
from apiscope.bookmark.remove.context import RemoveCommandContext


# prepare the bookmark layer before the write
def run_preflight(command_context: RemoveCommandContext) -> None:
    prepare_store(command_context.runtime)
