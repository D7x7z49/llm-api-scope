# apiscope/schema.py

from pydantic import BaseModel

from apiscope.config import Config
from apiscope.openapi.schema import OpenapiCommandContext
from apiscope.repo.schema import RepoCommandContext
from apiscope.rfc.schema import RfcCommandContext


class CommandContext(BaseModel):
    config: Config
    openapi_command_context: OpenapiCommandContext | None = None
    rfc_command_context: RfcCommandContext | None = None
    repo_command_context: RepoCommandContext | None = None
