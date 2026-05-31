# apiscope/config.py

import json
from contextlib import contextmanager
from os import environ
from pathlib import Path
from typing import Generator

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

CACHE_ROOT = DEFAULT_ROOT / "cache"

# ==============================================================================
# Config model
# ==============================================================================


class OpenapiConfig(BaseModel):
    alias: dict[str, str] = Field(default_factory=dict)


class Config(BaseModel):
    openapi: OpenapiConfig = Field(default_factory=OpenapiConfig)

    @classmethod
    def read(cls, path: Path) -> "Config":
        if not path.exists():
            raise FileNotFoundError(f"[{path}] not found.")
        return cls.model_validate_json(path.read_text())

    @classmethod
    @contextmanager
    def edit(cls, path: Path) -> Generator["Config", None, None]:
        if not path.exists():
            raise FileNotFoundError(f"[{path}] not found.")
        config = cls.model_validate_json(path.read_text())
        yield config
        if isinstance(config, Config):
            config.write(path)

    def write(self, path: Path) -> None:
        data = {"$schema": DEFAULT_CONFIG_SCHEMA_PATH.as_uri()} | self.model_dump()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n")


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


def get_project_config_path() -> Path | None:
    project_root = _get_project_root()
    if project_root is None:
        return None
    return project_root / f".{APP_NAME}.config.json"


def get_config() -> Config:
    # ensure the default config exists
    if not DEFAULT_CONFIG_PATH.exists():
        DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_CONFIG.write(DEFAULT_CONFIG_PATH)

    # ensure the default config schema exists
    DEFAULT_CONFIG_SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_CONFIG_SCHEMA_PATH.write_text(json.dumps(Config.model_json_schema(), indent=2))

    # load the global config
    global_config = Config.model_validate_json(DEFAULT_CONFIG_PATH.read_text())

    # load the project config
    project_config_path = get_project_config_path()
    project_config: Config | None = None
    if project_config_path is not None:
        if not project_config_path.exists():
            DEFAULT_CONFIG.write(project_config_path)
        project_config = Config.model_validate_json(project_config_path.read_text())

    # merge the configs: default -> global -> project
    merged = DEFAULT_CONFIG.model_dump() | global_config.model_dump()
    if project_config:
        merged |= project_config.model_dump()

    return Config.model_validate(merged)
