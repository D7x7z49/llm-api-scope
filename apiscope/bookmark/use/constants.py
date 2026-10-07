# apiscope/bookmark/use/constants.py

from typing import Final

# ==============================================================================
# command
# ==============================================================================

COMMAND_NAME: Final = "use"

# ==============================================================================
# user-facing messages
# ==============================================================================

MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "bookmark.use.help.command": "run a saved reference",
    "bookmark.use.help.argument.id": "the bookmark id to run",
    "bookmark.use.body.empty": "the reference points at no content",
    "bookmark.use.error.runtime_context_unavailable": "runtime context is unavailable",
    "bookmark.use.error.id_not_found": "no bookmark has the id {id}",
    "bookmark.use.error.removed": "the bookmark {id} is marked as removed",
    "bookmark.use.error.invalid": "the bookmark {id} is invalid because its target changed or disappeared",
    "bookmark.use.error.source_not_found": "the address {target} names an unknown source",
    "bookmark.use.error.cache_missing": "the source {name} has no cached content; run sync first",
    "bookmark.use.error.projection_failed": "cannot project the target {target}",
    "bookmark.use.error.read_failed": "cannot read the target {target}",
}
