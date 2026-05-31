# apiscope/openapi/schema.py

from pydantic import BaseModel

from apiscope.openapi.spec.schema import SpecCommandContext


class OpenapiCommandContext(BaseModel):
    spec_command_context: SpecCommandContext | None = None
