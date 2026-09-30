# apiscope/skill/install/schema.py

from pydantic import Field

from apiscope.schema import StrictSchemaModel


class InstallOptions(StrictSchemaModel):
    target: str | None = Field(default=None, min_length=1)
