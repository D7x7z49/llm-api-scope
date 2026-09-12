# apiscope/config.py

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from pydantic import ValidationError

from apiscope.constants import (
    APISCOPE_HOME_ENV,
    APP_DIRECTORY,
    CACHE_DIRECTORY,
    CONFIG_FILENAME,
    CONFIG_VERSION,
    HOME_LAYOUT_VERSION,
    VERSION_FILENAME,
)
from apiscope.context import GlobalPaths, ProjectPaths
from apiscope.schema import ConfigSchema

# ==============================================================================
# errors
# ==============================================================================


class ConfigError(RuntimeError):
    """Raised when a configuration asset cannot be prepared safely."""


# ==============================================================================
# path resolution
# ==============================================================================


def resolve_home(environment: Mapping[str, str] | None = None) -> Path:
    """Resolve the base directory used for global apiscope data."""
    source = os.environ if environment is None else environment
    configured_home = source.get(APISCOPE_HOME_ENV)
    if configured_home is None or not configured_home.strip():
        return Path.home().resolve()
    return Path(configured_home).expanduser().resolve()


def build_global_paths(home: Path) -> GlobalPaths:
    root = home / APP_DIRECTORY
    return GlobalPaths(
        home=home,
        root=root,
        version=root / VERSION_FILENAME,
        config=root / CONFIG_FILENAME,
        cache=root / CACHE_DIRECTORY,
    )


def build_project_paths(root: Path) -> ProjectPaths:
    config_dir = root / APP_DIRECTORY
    return ProjectPaths(
        root=root,
        config_dir=config_dir,
        config=config_dir / CONFIG_FILENAME,
    )


# ==============================================================================
# configuration assets
# ==============================================================================


def ensure_version_file(path: Path) -> None:
    if not path.exists():
        _write_text(path, f"{HOME_LAYOUT_VERSION}\n")
        return

    try:
        version = path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise ConfigError(f"cannot read {path}; check the file and its permissions") from error

    if version != HOME_LAYOUT_VERSION:
        raise ConfigError(f"unsupported home layout in {path}; keep the file unchanged and migrate it before retrying")


def ensure_config_file(path: Path) -> ConfigSchema:
    if not path.exists():
        _write_text(path, _default_config().model_dump_json(indent=2) + "\n")

    try:
        content = path.read_text(encoding="utf-8")
        return ConfigSchema.model_validate_json(content)
    except OSError as error:
        raise ConfigError(f"cannot read {path}; check the file and its permissions") from error
    except (ValidationError, ValueError) as error:
        raise ConfigError(f"invalid configuration in {path}; fix or remove it before retrying") from error


def _default_config() -> ConfigSchema:
    return ConfigSchema(
        version=CONFIG_VERSION,
        sources={},
        settings={},
    )


def _write_text(path: Path, content: str) -> None:
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as error:
        raise ConfigError(f"cannot write {path}; check permissions and choose a writable location") from error
