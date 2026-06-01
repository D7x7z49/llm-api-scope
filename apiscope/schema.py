# apiscope/schema.py

from pydantic import BaseModel

from apiscope.config import Config
from apiscope.openapi.schema import OpenapiCommandContext


class CommandContext(BaseModel):
    config: Config
    openapi_command_context: OpenapiCommandContext | None = None
