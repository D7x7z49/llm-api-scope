# apiscope/add/constants.py

from typing import Final

COMMAND_NAME: Final = "add"

MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "add.help.command": "add a source to the selected configuration",
    "add.help.argument.name": "the source name",
    "add.help.argument.source": "the source location",
    "add.help.option.type": "the source document type",
    "add.help.option.ttl": "the source cache TTL in days",
    "add.error.runtime_context_unavailable": "runtime context is unavailable",
    "add.error.invalid_options": ("source {name} has an invalid definition. check its type, location, and TTL"),
    "add.error.project_required": "a Git project is required unless --global is used",
    "add.error.duplicate_name": "source {name} already exists",
    "add.error.invalid_name": "source name {name} must be lowercase kebab case",
    "add.error.reserved_name": "source name {name} is reserved",
    "add.error.persistence.read_failed": "cannot read the configuration at {path}",
    "add.error.persistence.write_failed": "cannot update the configuration at {path}",
}
