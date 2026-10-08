# apiscope/bookmark/add/constants.py

from typing import Final

# ==============================================================================
# command
# ==============================================================================

COMMAND_NAME: Final = "add"

# ==============================================================================
# user-facing messages
# ==============================================================================

MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "bookmark.add.help.command": "save a new named reference",
    "bookmark.add.help.argument.id": "the bookmark id, a lower-case kebab-case name",
    "bookmark.add.help.argument.mode": "the target kind: file, view, read, or group",
    "bookmark.add.help.argument.target": "the target path, address, or the group member ids",
    "bookmark.add.help.option.description": "a short description of the reference",
    "bookmark.add.help.option.start": "the first line for a file bookmark",
    "bookmark.add.help.option.offset": "how many lines a file bookmark reads",
    "bookmark.add.help.option.force": "replace an existing bookmark with the same id",
    "bookmark.add.error.invalid_options": "the bookmark options are invalid, {detail}",
    "bookmark.add.error.duplicate_id": "a bookmark with the id {id} already exists",
    "bookmark.add.error.target_count": "the {mode} mode needs exactly one target, but got {count}",
    "bookmark.add.error.target_unresolved": "cannot resolve the {mode} target {target} because {detail}",
    "bookmark.add.error.group_needs_members": "a group needs five to nine members, but got {count}",
    "bookmark.add.error.member_not_found": "the group member {id} does not exist",
    "bookmark.add.error.duplicate_member": "a group cannot list the same member twice",
    "bookmark.add.error.self_member": "the group {id} cannot contain itself",
    "bookmark.add.error.range_not_allowed": "only a file bookmark accepts --start and --offset",
}

# the resolver reports a reason, and the add boundary renders it
TARGET_REASON_TEXTS: Final[dict[str, str]] = {
    "source_not_found": "the source is not registered",
    "source_invalid": "the source definition is invalid",
    "cache_missing": "the cache is missing or invalid. sync the source before retrying",
    "unsupported": "this source type has no reader",
    "projection_failed": "the source structure cannot be projected",
    "route_not_found": "the route does not exist. view the source to pick a route",
    "not_leaf": "the target is not a leaf. choose a leaf route",
}

FILE_MISSING_REASON: Final = "the file is missing"
