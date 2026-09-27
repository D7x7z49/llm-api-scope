# apiscope/read/schema.py
from pydantic import Field

from apiscope.schema import StrictSchemaModel


class ReadOptions(StrictSchemaModel):
    address: str = Field(min_length=1)
    index: str | None = Field(default=None, pattern=r"^[0-9]+(?:\.[0-9]+)*$")
