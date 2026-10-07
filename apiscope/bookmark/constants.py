# apiscope/bookmark/constants.py

from typing import Final

# ==============================================================================
# command
# ==============================================================================

COMMAND_NAME: Final = "bookmark"

# ==============================================================================
# storage
# ==============================================================================

BOOKMARK_FILENAME: Final = "bookmarks.json"
BOOKMARK_SCHEMA_FILENAME: Final = "bookmarks.schema.json"
BOOKMARK_SCHEMA_REF: Final = f"./schema/{BOOKMARK_SCHEMA_FILENAME}"
BOOKMARK_FORMAT_VERSION: Final = "1"

# ==============================================================================
# entry contract
# ==============================================================================

# a bookmark id is a lower-case kebab-case identifier of one to three words
ENTRY_ID_PATTERN: Final = r"^[a-z][a-z0-9]*(-[a-z0-9]+){0,2}$"
DESCRIPTION_MIN_LENGTH: Final = 32
DESCRIPTION_MAX_LENGTH: Final = 72
GROUP_MIN_MEMBERS: Final = 5
GROUP_MAX_MEMBERS: Final = 9

# ==============================================================================
# user-facing messages
# ==============================================================================

MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "bookmark.help.command": "manage saved references to cached sources",
    "bookmark.error.store.directory_prepare_failed": (
        "cannot prepare the bookmark directory at {path} because it cannot be created or written"
    ),
    "bookmark.error.store.reference_cycle": "the reference graph would contain a cycle through {id}",
}
