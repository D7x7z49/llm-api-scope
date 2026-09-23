# apiscope/view/constants.py
from typing import Final

# ==============================================================================
# command
# ==============================================================================


COMMAND_NAME: Final = "view"

# ==============================================================================
# user-facing messages
# ==============================================================================


MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "view.help.command": "show the structure of a cached source",
    "view.help.argument.name": "the registered source name",
    "view.help.argument.path": "the source path to display; omit it for the complete tree",
    "view.error.runtime_context_unavailable": "runtime context is unavailable",
    "view.error.invalid_options": "invalid view options",
    "view.error.name_not_found": "source {name} does not exist",
    "view.error.source_invalid": "cannot view source {name} because its definition is invalid",
    "view.error.cache_missing": "cannot view source {name} because its cache is missing. sync it before retrying",
    "view.error.cache_invalid": "cannot view source {name} because its cache is invalid. sync it before retrying",
    "view.error.projection_failed": "cannot view source {name} because its structure cannot be projected",
}
