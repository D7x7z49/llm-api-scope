# apiscope/bookmark/list/constants.py

from typing import Final

# ==============================================================================
# command
# ==============================================================================

COMMAND_NAME: Final = "list"

# ==============================================================================
# user-facing messages
# ==============================================================================

MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "bookmark.list.help.command": "list saved references, or the members of one group",
    "bookmark.list.help.argument.group": "an optional group id whose members are listed",
    "bookmark.list.body.empty": "no saved references",
    "bookmark.list.error.group_not_found": "no group has the id {id}",
}
