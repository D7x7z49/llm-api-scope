# apiscope/schema.py

from typing import Literal

from pydantic import BaseModel, ConfigDict

# ==============================================================================
# configuration schema
# ==============================================================================


class ConfigSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: Literal[1]
    sources: dict[str, object]
    settings: dict[str, object]
