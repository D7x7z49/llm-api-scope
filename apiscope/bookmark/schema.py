# apiscope/bookmark/schema.py

from typing import Literal

from pydantic import Field, model_validator

from apiscope.bookmark.constants import (
    BOOKMARK_FORMAT_VERSION,
    DESCRIPTION_MAX_LENGTH,
    DESCRIPTION_MIN_LENGTH,
    ENTRY_ID_PATTERN,
    GROUP_MAX_MEMBERS,
    GROUP_MIN_MEMBERS,
)
from apiscope.schema import StrictSchemaModel

# a mode names the kind of target a bookmark points at
BookmarkMode = Literal["file", "view", "read", "group"]


class BookmarkEntry(StrictSchemaModel):
    id: str = Field(pattern=ENTRY_ID_PATTERN)
    description: str = Field(min_length=DESCRIPTION_MIN_LENGTH, max_length=DESCRIPTION_MAX_LENGTH)
    mode: BookmarkMode
    target: str = ""
    members: tuple[str, ...] = ()
    start: int | None = Field(default=None, ge=0)
    offset: int | None = Field(default=None, ge=1)
    expected_digest: str = ""
    removed: bool = False

    # a group carries members, every other mode carries a target and a digest
    @model_validator(mode="after")
    def _check_mode_fields(self) -> "BookmarkEntry":
        if self.mode == "group":
            if self.target or self.expected_digest:
                raise ValueError("a group carries members, not a target")
            if not GROUP_MIN_MEMBERS <= len(self.members) <= GROUP_MAX_MEMBERS:
                raise ValueError(f"a group needs {GROUP_MIN_MEMBERS} to {GROUP_MAX_MEMBERS} members")
            if len(set(self.members)) != len(self.members):
                raise ValueError("a group carries distinct members")
            if self.id in self.members:
                raise ValueError("a group cannot contain itself")
            if self.start is not None or self.offset is not None:
                raise ValueError("a group carries no line range")
            return self

        if not self.target or not self.expected_digest:
            raise ValueError(f"the {self.mode} mode needs a target and a digest")
        if self.members:
            raise ValueError(f"the {self.mode} mode carries no members")
        if self.mode != "file" and (self.start is not None or self.offset is not None):
            raise ValueError("only a file bookmark carries a line range")
        return self


class BookmarkFile(StrictSchemaModel):
    schema_ref: str = Field(validation_alias="$schema", serialization_alias="$schema", min_length=1)
    version: str = Field(default=BOOKMARK_FORMAT_VERSION, min_length=1)
    bookmarks: dict[str, BookmarkEntry] = Field(default_factory=dict)

    # keep the map key and the entry id in sync
    @model_validator(mode="after")
    def _keys_match_ids(self) -> "BookmarkFile":
        for key, entry in self.bookmarks.items():
            if key != entry.id:
                raise ValueError(f"bookmark key {key!r} does not match entry id {entry.id!r}")
        return self


__all__ = ["BookmarkEntry", "BookmarkFile", "BookmarkMode"]
