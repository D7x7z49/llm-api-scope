# apiscope/bookmark/remove/schema.py

from pydantic import Field

from apiscope.bookmark.constants import ENTRY_ID_PATTERN
from apiscope.schema import StrictSchemaModel


class RemoveOptions(StrictSchemaModel):
    id: str = Field(pattern=ENTRY_ID_PATTERN)
