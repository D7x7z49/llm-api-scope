# apiscope/view/schema.py
from pydantic import Field

from apiscope.schema import StrictSchemaModel


class ViewOptions(StrictSchemaModel):
    name: str = Field(min_length=1)
    path: str | None = None
    depth: int | None = Field(default=None, ge=0)
