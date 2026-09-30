# apiscope/view/schema.py
from pydantic import Field

from apiscope.schema import StrictSchemaModel


class ViewOptions(StrictSchemaModel):
    address: str = Field(min_length=1)
    depth: int | None = Field(default=None, ge=0)
