# apiscope/remove/constants.py

from typing import Final

COMMAND_NAME: Final = "remove"

MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "remove.help.command": "remove a source from the selected configuration",
    "remove.help.argument.name": "the source name",
    "remove.error.runtime_context_unavailable": "runtime context is unavailable",
    "remove.error.invalid_options": "source name {name} is invalid",
    "remove.error.project_required": "a Git project is required unless --global is used",
    "remove.error.name_not_found": "source {name} was not found",
    "remove.error.persistence.read_failed": "cannot read the configuration at {path}",
    "remove.error.persistence.write_failed": "cannot update the configuration at {path}",
}
