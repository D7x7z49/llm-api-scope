# apiscope/config.py

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError
from pydantic_core import MISSING

from apiscope.constants import (
    APISCOPE_HOME_ENV,
    APP_DIRECTORY,
    CACHE_DIRECTORY,
    CONFIG_FILENAME,
    CONFIG_SCHEMA_REF,
    GITIGNORE_FILENAME,
    HOME_LAYOUT_VERSION,
    LOCAL_CONFIG_FILENAME,
    LOCAL_CONFIG_SCHEMA_FILENAME,
    SCHEMA_DIRECTORY,
    SCHEMA_FILENAME,
    VERSION_FILENAME,
)
from apiscope.context import HomePaths, LocalPaths, Paths, ProjectPaths
from apiscope.schema import (
    LocalSetting,
    PublicSetting,
    RuntimeConfig,
    RuntimeSetting,
    RuntimeSource,
)

# ==============================================================================
# errors
# ==============================================================================


class ConfigError(RuntimeError):
    pass


# ==============================================================================
# path resolution
# ==============================================================================


# resolve the base directory used for apiscope home data
def resolve_home(environment: Mapping[str, str] | None = None) -> Path:
    source = os.environ if environment is None else environment
    configured_home = source.get(APISCOPE_HOME_ENV)
    if configured_home is None or not configured_home.strip():
        return Path.home().resolve()
    return Path(configured_home).expanduser().resolve()


def build_home_paths(home: Path) -> HomePaths:
    root = home / APP_DIRECTORY
    schema_dir = root / SCHEMA_DIRECTORY
    return HomePaths(
        base=home,
        root=root,
        version=root / VERSION_FILENAME,
        config=root / CONFIG_FILENAME,
        schema=schema_dir / SCHEMA_FILENAME,
        cache=root / CACHE_DIRECTORY,
    )


# derive project and local paths only after project discovery succeeds.
def build_paths(home: HomePaths, project_root: Path | None) -> Paths:
    if project_root is None:
        return Paths(home=home, project=None, local=None)

    config_dir = project_root / APP_DIRECTORY
    schema_dir = config_dir / SCHEMA_DIRECTORY
    return Paths(
        home=home,
        project=ProjectPaths(
            root=project_root,
            gitignore=project_root / GITIGNORE_FILENAME,
            config=config_dir / CONFIG_FILENAME,
            schema=schema_dir / SCHEMA_FILENAME,
        ),
        local=LocalPaths(
            config=config_dir / LOCAL_CONFIG_FILENAME,
            schema=schema_dir / LOCAL_CONFIG_SCHEMA_FILENAME,
        ),
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


def ensure_schema_file(path: Path, model: type[BaseModel]) -> None:
    try:
        content = json.dumps(model.model_json_schema(by_alias=True), indent=2, sort_keys=True) + "\n"
    except (TypeError, ValueError) as error:
        raise ConfigError(f"cannot generate schema for {path}") from error

    if path.exists():
        try:
            if path.read_text(encoding="utf-8") == content:
                return
        except OSError as error:
            raise ConfigError(f"cannot read {path}; check the file and its permissions") from error

    _write_text(path, content)


def ensure_config_file(
    path: Path,
    model: type[BaseModel],
    *,
    schema_ref: str = CONFIG_SCHEMA_REF,
) -> BaseModel:
    if not path.exists():
        _write_text(
            path, _default_config(model, schema_ref).model_dump_json(by_alias=True, exclude_unset=True, indent=2) + "\n"
        )

    try:
        content = path.read_text(encoding="utf-8")
        return model.model_validate_json(content)
    except OSError as error:
        raise ConfigError(f"cannot read {path}; check the file and its permissions") from error
    except (ValidationError, ValueError) as error:
        raise ConfigError(f"invalid configuration in {path}; fix or remove it before retrying") from error


def _default_config(model: type[BaseModel], schema_ref: str) -> BaseModel:
    return model.model_validate({"$schema": schema_ref})


def assemble_runtime_config(
    global_file: BaseModel,
    project_file: BaseModel | None = None,
    local_file: BaseModel | None = None,
) -> RuntimeConfig:
    source: dict[str, RuntimeSource] = {}
    setting = RuntimeSetting(public=PublicSetting(), local=LocalSetting())

    for config_file in (global_file, project_file, local_file):
        if config_file is None:
            continue
        source_value = _explicit_field(config_file, "source")
        if source_value is not MISSING:
            source.update(source_value)

    global_setting = _explicit_field(global_file, "setting")
    if global_setting is not MISSING:
        setting = RuntimeSetting.model_validate(global_setting.model_dump(), strict=True)

    if project_file is not None:
        project_setting = _explicit_field(project_file, "setting")
        if project_setting is not MISSING:
            setting = RuntimeSetting(
                public=PublicSetting.model_validate(project_setting.model_dump(), strict=True),
                local=setting.local,
            )

    if local_file is not None:
        local_setting = _explicit_field(local_file, "setting")
        if local_setting is not MISSING:
            setting = RuntimeSetting(
                public=setting.public,
                local=LocalSetting.model_validate(local_setting.model_dump(), strict=True),
            )

    return RuntimeConfig.model_validate(
        {
            "source": {name: value.model_dump() for name, value in source.items()},
            "setting": setting.model_dump(),
        },
        strict=True,
    )


def _explicit_field(model: BaseModel, field_name: str) -> Any:
    if field_name not in model.model_fields_set:
        return MISSING
    return getattr(model, field_name)


def _write_text(path: Path, content: str) -> None:
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as error:
        raise ConfigError(f"cannot write {path}; check permissions and choose a writable location") from error
