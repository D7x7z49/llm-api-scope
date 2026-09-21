# apiscope/sync/schema.py
from pydantic import Field

from apiscope.schema import DocumentType, StrictSchemaModel


class SyncOptions(StrictSchemaModel):
    name: str | None = Field(default=None, min_length=1)
    source_type: DocumentType | None = None
    force: bool = False
