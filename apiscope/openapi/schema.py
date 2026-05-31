# apiscope/openapi/schema.py

from pydantic import BaseModel

from apiscope.openapi.doc.schema import DocCommandContext


class OpenapiCommandContext(BaseModel):
    doc_command_context: DocCommandContext | None = None
