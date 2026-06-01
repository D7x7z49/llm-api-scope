# apiscope/openapi/schema.py

from pathlib import Path

from pydantic import BaseModel

from apiscope.openapi.spec.schema import SpecCommandContext


class OpenapiCommandContext(BaseModel):
    # openapi settings
    cache_dir: Path

    # sub command contexts
    spec_command_context: SpecCommandContext | None = None
