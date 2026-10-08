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
    "bookmark.error.runtime_context_unavailable": "runtime context is unavailable",
    "bookmark.error.store.directory_prepare_failed": (
        "cannot prepare the bookmark directory at {path} because it cannot be created or written"
    ),
    "bookmark.error.store.reference_cycle": "the reference graph would contain a cycle through {id}",
    "bookmark.error.target.source_not_found": (
        "cannot resolve the target {target} because the source {name} is not registered"
    ),
    "bookmark.error.target.source_invalid": (
        "cannot resolve the target {target} because its source definition is invalid"
    ),
    "bookmark.error.target.cache_missing": (
        "cannot resolve the target {target} because its cache is missing. sync the source before retrying"
    ),
    "bookmark.error.target.unsupported": ("cannot use the target {target} because this source type has no reader"),
    "bookmark.error.target.projection_failed": (
        "cannot resolve the target {target} because its structure cannot be projected"
    ),
    "bookmark.error.target.route_not_found": (
        "cannot resolve the target {target} because the route does not exist. view the source to pick a route"
    ),
    "bookmark.error.target_not_leaf": ("cannot use the target {target} because it is not a leaf. choose a leaf route"),
}
