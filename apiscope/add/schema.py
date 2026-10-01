# apiscope/add/schema.py

from pydantic import Field, PositiveInt

from apiscope.schema import DocumentType, StrictSchemaModel


class AddOptions(StrictSchemaModel):
    name: str = Field(min_length=1)
    doc_type: DocumentType
    doc_src: str = Field(min_length=1)
    doc_ttl: PositiveInt | None = None
