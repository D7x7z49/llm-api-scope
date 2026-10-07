# apiscope/bookmark/use/schema.py

from pydantic import Field

from apiscope.bookmark.constants import ENTRY_ID_PATTERN
from apiscope.schema import StrictSchemaModel


class UseOptions(StrictSchemaModel):
    id: str = Field(pattern=ENTRY_ID_PATTERN)
