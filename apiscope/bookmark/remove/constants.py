# apiscope/bookmark/remove/constants.py

from typing import Final

# ==============================================================================
# command
# ==============================================================================

COMMAND_NAME: Final = "remove"

# ==============================================================================
# user-facing messages
# ==============================================================================

MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "bookmark.remove.help.command": "mark a saved reference as removed",
    "bookmark.remove.help.argument.id": "the bookmark id to mark removed",
    "bookmark.remove.error.id_not_found": "no bookmark has the id {id}",
    "bookmark.remove.error.already_removed": "the bookmark {id} is already marked as removed",
}
