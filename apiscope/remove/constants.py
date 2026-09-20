# apiscope/remove/constants.py

from typing import Final

COMMAND_NAME: Final = "remove"

MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "remove.help.command": "remove a source from the selected configuration",
    "remove.help.argument.name": "the source name",
    "remove.error.runtime_context_unavailable": "runtime context is unavailable",
    "remove.error.invalid_options": "invalid source name {name}",
    "remove.error.project_required": "a Git project is required unless --global is used",
    "remove.error.name_not_found": "source {name} was not found",
    "remove.error.persistence.read_failed": "cannot read configuration {path}",
    "remove.error.persistence.write_failed": "cannot update configuration {path}",
}
