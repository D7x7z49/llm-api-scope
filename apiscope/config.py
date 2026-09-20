# apiscope/config.py

from __future__ import annotations

import json
import os
import stat
import tempfile
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
from apiscope.errors import MessageError
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


class ConfigError(MessageError):
    pass


# ==============================================================================
# path resolution
# ==============================================================================


# resolve the base directory used for apiscope home data
def resolve_home(environment: Mapping[str, str] | None = None) -> Path:
    source = os.environ if environment is None else environment
    configured_home = source.get(APISCOPE_HOME_ENV)
    use_configured_home = configured_home is not None and bool(configured_home.strip())
    display_path = configured_home if use_configured_home else "<home>"
    try:
        if use_configured_home:
            assert configured_home is not None
            configured_path = Path(configured_home)
        else:
            configured_path = Path.home()
        return configured_path.expanduser().resolve()
    except (OSError, RuntimeError, ValueError) as error:
        raise ConfigError(
            "root.error.config.home_resolve_failed",
            {"path": display_path},
        ) from error


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
# configuration file lifecycle
# ==============================================================================


def ensure_version_file(path: Path) -> None:
    if not path.exists():
        _atomic_write_text(path, f"{HOME_LAYOUT_VERSION}\n")
        return

    try:
        version = path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise ConfigError("root.error.config.read_failed", {"path": str(path)}) from error

    if version != HOME_LAYOUT_VERSION:
        raise ConfigError("root.error.config.unsupported_home_layout", {"path": str(path)})


def ensure_schema_file(path: Path, model: type[BaseModel]) -> None:
    try:
        content = json.dumps(model.model_json_schema(by_alias=True), indent=2, sort_keys=True) + "\n"
    except (TypeError, ValueError) as error:
        raise ConfigError("root.error.config.schema_generation_failed", {"path": str(path)}) from error

    if path.exists():
        try:
            if path.read_text(encoding="utf-8") == content:
                return
        except OSError as error:
            raise ConfigError("root.error.config.read_failed", {"path": str(path)}) from error

    _atomic_write_text(path, content)


def ensure_config_file(
    path: Path,
    model: type[BaseModel],
    *,
    schema_ref: str = CONFIG_SCHEMA_REF,
) -> BaseModel:
    if not path.exists():
        _atomic_write_text(
            path, _default_config(model, schema_ref).model_dump_json(by_alias=True, exclude_unset=True, indent=2) + "\n"
        )

    try:
        content = path.read_text(encoding="utf-8")
        return model.model_validate_json(content)
    except OSError as error:
        raise ConfigError("root.error.config.read_failed", {"path": str(path)}) from error
    except (ValidationError, ValueError) as error:
        raise ConfigError("root.error.config.invalid", {"path": str(path)}) from error


# ==============================================================================
# configuration persistence
# ==============================================================================


def save_config_file(path: Path, config_file: BaseModel) -> None:
    try:
        data = config_file.model_dump(mode="json", by_alias=True, exclude_unset=True)
        if "$schema" in data:
            schema_ref = data.pop("$schema")
            data = {"$schema": schema_ref, **data}
        content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    except (TypeError, ValueError) as error:
        raise ConfigError("root.error.config.write_failed", {"path": str(path)}) from error
    _atomic_write_text(path, content)


# ==============================================================================
# source record transforms
# ==============================================================================


def extract_config_sources(config_file: BaseModel) -> dict[str, RuntimeSource]:
    source = _explicit_field(config_file, "source")
    if source is MISSING:
        return {}
    return dict(source)


def with_config_sources(
    config_file: BaseModel,
    sources: Mapping[str, RuntimeSource],
) -> BaseModel:
    normalized_sources = {name: RuntimeSource.model_validate(source, strict=True) for name, source in sources.items()}
    data = config_file.model_dump(by_alias=True, exclude_unset=True)
    data["source"] = {name: source.model_dump() for name, source in normalized_sources.items()}
    return type(config_file).model_validate(data, strict=True)


# ==============================================================================
# model construction
# ==============================================================================


def _default_config(model: type[BaseModel], schema_ref: str) -> BaseModel:
    return model.model_validate({"$schema": schema_ref})


# ==============================================================================
# runtime configuration merge
# ==============================================================================


def _merge_public_setting(base: PublicSetting, override: PublicSetting) -> PublicSetting:
    if "doc_ttl" not in override.model_fields_set:
        return base
    return PublicSetting(doc_ttl=override.doc_ttl)


def _merge_local_setting(base: LocalSetting, override: LocalSetting) -> LocalSetting:
    if "proxy" not in override.model_fields_set:
        return base
    return LocalSetting(proxy=override.proxy)


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
        setting = RuntimeSetting(
            public=_merge_public_setting(setting.public, global_setting.public),
            local=_merge_local_setting(setting.local, global_setting.local),
        )

    if project_file is not None:
        project_setting = _explicit_field(project_file, "setting")
        if project_setting is not MISSING:
            setting = RuntimeSetting(
                public=_merge_public_setting(setting.public, project_setting),
                local=setting.local,
            )

    if local_file is not None:
        local_setting = _explicit_field(local_file, "setting")
        if local_setting is not MISSING:
            setting = RuntimeSetting(
                public=setting.public,
                local=_merge_local_setting(setting.local, local_setting),
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


def _atomic_write_text(path: Path, content: str) -> None:
    temporary_path: Path | None = None
    existing_mode: int | None = None
    try:
        if path.exists():
            existing_mode = stat.S_IMODE(path.stat().st_mode)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        if existing_mode is not None:
            os.chmod(temporary_path, existing_mode)
        os.replace(temporary_path, path)
    except (OSError, ValueError) as error:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                pass
        raise ConfigError("root.error.config.write_failed", {"path": str(path)}) from error
