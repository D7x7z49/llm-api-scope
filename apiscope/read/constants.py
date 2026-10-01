# apiscope/read/constants.py
from typing import Final

# ==============================================================================
# command
# ==============================================================================


COMMAND_NAME: Final = "read"

# ==============================================================================
# user-facing messages
# ==============================================================================


MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "read.help.command": "read selected content from a source",
    "read.help.argument.address": "the registered source name and route",
    "read.help.argument.index": "the numeric tree index shown by view; omit it to read a leaf address directly",
    "read.error.runtime_context_unavailable": "runtime context is unavailable",
    "read.error.invalid_options": "invalid read options",
    "read.error.name_not_found": "source {name} does not exist",
    "read.error.source_invalid": "cannot read source {name} because its definition is invalid",
    "read.error.cache_missing": "cannot read source {name} because its cache is missing. sync it before retrying",
    "read.error.cache_invalid": "cannot read source {name} because its cache is invalid. sync it before retrying",
    "read.error.target_invalid": "cannot read target {target} because it is invalid",
    "read.error.target_not_leaf": "{target} is an ordinary node, not a leaf",
    "read.error.content_invalid": "cannot read source {name} because its cached content is invalid",
}
