# apiscope/bookmark/use/preflight.py

from apiscope.bookmark.use.context import UseCommandContext


# use only reads the store and the cache, so it prepares nothing
def run_preflight(command_context: UseCommandContext) -> None:
    del command_context
