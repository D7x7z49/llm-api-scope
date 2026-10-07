# apiscope/bookmark/prune/constants.py

from typing import Final

# ==============================================================================
# command
# ==============================================================================

COMMAND_NAME: Final = "prune"

# ==============================================================================
# user-facing messages
# ==============================================================================

MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "bookmark.prune.help.command": "delete removed and isolated references",
    "bookmark.prune.help.option.invalid": "also delete invalid and isolated references",
    "bookmark.prune.error.invalid_options": "invalid prune options",
}
