# apiscope/bookmark/add/schema.py

from pydantic import Field

from apiscope.bookmark.constants import (
    DESCRIPTION_MAX_LENGTH,
    DESCRIPTION_MIN_LENGTH,
    ENTRY_ID_PATTERN,
)
from apiscope.bookmark.schema import BookmarkMode
from apiscope.schema import StrictSchemaModel


class AddOptions(StrictSchemaModel):
    id: str = Field(pattern=ENTRY_ID_PATTERN)
    mode: BookmarkMode
    targets: tuple[str, ...] = ()
    description: str = Field(min_length=DESCRIPTION_MIN_LENGTH, max_length=DESCRIPTION_MAX_LENGTH)
    start: int | None = Field(default=None, ge=0)
    offset: int | None = Field(default=None, ge=1)
    force: bool = False
