# apiscope/list/schema.py

from pydantic import Field

from apiscope.schema import SourceSelector, StrictSchemaModel


class ListOptions(StrictSchemaModel):
    selector: SourceSelector
    limit: int | None = Field(default=None, ge=1)
    offset: int = Field(default=0, ge=0)
