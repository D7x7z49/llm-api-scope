# apiscope/list/schema.py

from typing import Literal

from pydantic import Field

from apiscope.schema import DocumentType, StrictSchemaModel

ListSelector = Literal["all"] | DocumentType


class ListOptions(StrictSchemaModel):
    selector: ListSelector
    limit: int | None = Field(default=None, ge=1)
    offset: int = Field(default=0, ge=0)
