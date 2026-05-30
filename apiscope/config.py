# apiscope/config.py

import json
from os import environ
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# load .env file at module load time
load_dotenv()

# Brand identity
# ==============
APP_NAME = "apiscope"
APP_DESCRIPTION = "A reader for network resources"
DEFAULT_HOME = Path(environ.get("APISCOPE_HOME", str(Path.home())))
DEFAULT_ROOT = DEFAULT_HOME / ".apiscope"
DEFAULT_CONFIG_PATH = DEFAULT_ROOT / "config.json"
DEFAULT_CONFIG_SCHEMA_PATH = DEFAULT_ROOT / "config.schema.json"

# ==============================================================================
# Config model
# ==============================================================================


class OpenapiConfig(BaseModel):
    alias: dict[str, str] = Field(default_factory=dict)


class Config(BaseModel):
    openapi: OpenapiConfig = Field(default_factory=OpenapiConfig)


# ==============================================================================
# Helpers
# ==============================================================================


def _get_project_root() -> Path | None:
    workpath = Path.cwd()
    while True:
        if (workpath / ".git").exists():
            return workpath
        parent = workpath.parent
        if parent == workpath:
            return None
        workpath = parent


# ==============================================================================
# Public API
# ==============================================================================


DEFAULT_CONFIG = Config()


def get_config() -> Config:
    # ensure the default config exists
    if not DEFAULT_CONFIG_PATH.exists():
        DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_CONFIG_PATH.write_text(DEFAULT_CONFIG.model_dump_json())

    # ensure the default config schema exists
    DEFAULT_CONFIG_SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_CONFIG_SCHEMA_PATH.write_text(json.dumps(Config.model_json_schema(), indent=2))

    # load the global config
    global_config = Config.model_validate_json(DEFAULT_CONFIG_PATH.read_text())

    # load the project config
    project_root = _get_project_root()
    project_config: Config | None = None
    if project_root:
        project_config_path = project_root / f".{APP_NAME}.config.json"
        if not project_config_path.exists():
            project_config_path.write_text(DEFAULT_CONFIG.model_dump_json())
        project_config = Config.model_validate_json(project_config_path.read_text())

    # merge the configs: default -> global -> project
    merged = DEFAULT_CONFIG.model_dump() | global_config.model_dump()
    if project_config:
        merged |= project_config.model_dump()

    return Config.model_validate(merged)
