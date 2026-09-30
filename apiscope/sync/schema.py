# apiscope/sync/schema.py
from pydantic import Field

from apiscope.schema import SourceSelector, StrictSchemaModel


class SyncOptions(StrictSchemaModel):
    selector: SourceSelector
    name: str | None = Field(default=None, min_length=1)
    force: bool = False
