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
    "bookmark.add.error.invalid_options": "the bookmark options are invalid",
    "bookmark.add.error.duplicate_id": "a bookmark with the id {id} already exists",
    "bookmark.add.error.target_count": "the {mode} mode needs exactly one target, but got {count}",
    "bookmark.add.error.target_unresolved": (
        "cannot resolve the {mode} target {target}; the file or cached source is missing"
    ),
    "bookmark.add.error.group_needs_members": "a group needs five to nine members, but got {count}",
    "bookmark.add.error.member_not_found": "the group member {id} does not exist",
    "bookmark.add.error.duplicate_member": "a group cannot list the same member twice",
    "bookmark.add.error.self_member": "the group {id} cannot contain itself",
    "bookmark.add.error.range_not_allowed": "only a file bookmark accepts --start and --offset",
}
