# apiscope/bookmark/list/schema.py

from pydantic import Field

from apiscope.bookmark.constants import ENTRY_ID_PATTERN
from apiscope.schema import StrictSchemaModel


class ListOptions(StrictSchemaModel):
    group: str | None = Field(default=None, pattern=ENTRY_ID_PATTERN)
