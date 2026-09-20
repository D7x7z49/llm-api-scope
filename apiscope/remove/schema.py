# apiscope/remove/schema.py

from pydantic import Field

from apiscope.schema import StrictSchemaModel


class RemoveOptions(StrictSchemaModel):
    name: str = Field(min_length=1)
