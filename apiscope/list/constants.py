# apiscope/list/constants.py

from typing import Final

COMMAND_NAME: Final = "list"

MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "list.help.command": "list configured sources by document type",
    "list.help.argument.selector": ("the selector: all, filesystem, repo, openapi, rfc, or llmstxt"),
    "list.error.runtime_context_unavailable": "runtime context is unavailable",
    "list.error.invalid_selector": "invalid list selector {selector}; choose all or a supported document type",
}
