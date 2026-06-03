# apiscope/config.py

import json
import time
from contextlib import contextmanager
from os import environ
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# load .env file at module load time
load_dotenv()

# brand identity
# ==============
APP_NAME = "apiscope"
DEFAULT_HOME = Path(environ.get("APISCOPE_HOME", str(Path.home())))
DEFAULT_ROOT = DEFAULT_HOME / ".apiscope"
DEFAULT_CONFIG_PATH = DEFAULT_ROOT / "config.json"
DEFAULT_CONFIG_SCHEMA_PATH = DEFAULT_ROOT / "config.schema.json"

CACHE_ROOT = DEFAULT_ROOT / "cache"

TMP_ROOT = DEFAULT_ROOT / "tmp"

# ==============================================================================
# config model
# ==============================================================================


class BaseConfig(BaseModel):
    cache_ttl: int  # seconds

    def is_stale_since(self, timestamp: float) -> bool:
        return time.time() - timestamp > self.cache_ttl

    def is_stale_path(self, path: Path) -> bool:
        if not path.exists():
            return True
        stat = path.stat()
        latest = max(stat.st_mtime, stat.st_ctime)
        return self.is_stale_since(latest)


class OpenapiConfig(BaseConfig):
    proxy: str | None = Field(default=None)
    alias: dict[str, str] = Field(default_factory=dict)

    # override
    cache_ttl: int = Field(default=60 * 60 * 24)  # 1 day


class RfcConfig(BaseConfig):
    # override
    cache_ttl: int = Field(default=60 * 60 * 24 * 30)  # 1 month


class RepoConfig(BaseConfig):
    entries: list[dict] = Field(default_factory=list)

    # override
    cache_ttl: int = Field(default=60 * 60 * 24 * 7)  # 1 week


class Config(BaseModel):
    openapi: OpenapiConfig = Field(default_factory=OpenapiConfig)
    rfc: RfcConfig = Field(default_factory=RfcConfig)
    repo: RepoConfig = Field(default_factory=RepoConfig)

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

    def merge(self, other: "Config") -> "Config":
        merged = self.model_copy(deep=True)
        merged.openapi.alias |= other.openapi.alias
        if other.openapi.proxy is not None:
            merged.openapi.proxy = other.openapi.proxy
        all_entries = self.repo.entries + other.repo.entries
        merged.repo.entries = list({e["url"]: e for e in all_entries}.values())
        return merged


# ==============================================================================
# helpers
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
# public API
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

    # load and merge the project config
    project_config_path = get_project_config_path()
    if project_config_path is not None and project_config_path.exists():
        project_config = Config.model_validate_json(project_config_path.read_text())
        return global_config.merge(project_config)

    return global_config
