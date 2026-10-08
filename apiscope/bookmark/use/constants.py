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
    "bookmark.use.error.id_not_found": "no bookmark has the id {id}",
    "bookmark.use.error.removed": "the bookmark {id} is marked as removed",
    "bookmark.use.error.invalid": "the bookmark {id} is invalid because its target changed or disappeared",
}
