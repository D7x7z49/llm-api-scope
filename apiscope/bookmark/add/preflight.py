# apiscope/bookmark/add/preflight.py

from apiscope.bookmark.add.context import AddCommandContext
from apiscope.bookmark.preflight import prepare_store


# prepare the bookmark layer before the write
def run_preflight(command_context: AddCommandContext) -> None:
    prepare_store(command_context.runtime)
