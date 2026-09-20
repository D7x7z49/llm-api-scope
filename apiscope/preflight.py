# apiscope/preflight.py

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel

from apiscope.config import (
    ConfigError,
    assemble_runtime_config,
    build_home_paths,
    build_paths,
    ensure_config_file,
    ensure_schema_file,
    ensure_version_file,
    resolve_home,
)
from apiscope.constants import CONFIG_SCHEMA_REF, LOCAL_CONFIG_SCHEMA_REF
from apiscope.context import RootOptions, RuntimeContext
from apiscope.errors import MessageError
from apiscope.gitignore import GitIgnoreError, ensure_project_gitignore
from apiscope.schema import GlobalConfigFile, LocalConfigFile, ProjectConfigFile

# ==============================================================================
# errors
# ==============================================================================


class PreflightError(MessageError):
    pass


# ==============================================================================
# project discovery
# ==============================================================================


# find the nearest ancestor containing a Git directory or worktree file
def find_project_root(start: Path | None = None) -> Path | None:
    candidate = (Path.cwd() if start is None else start).expanduser().resolve()
    if candidate.is_file():
        candidate = candidate.parent

    while True:
        git_marker = candidate / ".git"
        if git_marker.is_dir() or git_marker.is_file():
            return candidate
        if candidate.parent == candidate:
            return None
        candidate = candidate.parent


# ==============================================================================
# execution preflight
# ==============================================================================


# prepare local assets and build the runtime context
def run_preflight(
    *,
    cwd: Path | None = None,
    environment: Mapping[str, str] | None = None,
    options: RootOptions | None = None,
) -> RuntimeContext:
    root_options = RootOptions() if options is None else options
    try:
        home = resolve_home(environment)
    except ConfigError as error:
        raise PreflightError(error.code, error.values) from error
    home_paths = build_home_paths(home)
    _ensure_directory(home_paths.root)
    _prepare_version(home_paths.version)

    try:
        project_root = None if root_options.global_only else find_project_root(cwd)
    except OSError as error:
        location = str(cwd) if cwd is not None else "<current directory>"
        raise PreflightError(
            "root.error.preflight.project_inspection_failed",
            {"location": location},
        ) from error
    # paths.project and paths.local stay absent outside a project.
    paths = build_paths(home_paths, project_root)
    project_paths = paths.project
    local_paths = paths.local
    if project_paths is not None:
        _prepare_gitignore(project_paths.gitignore)

    _ensure_directory(home_paths.schema.parent)
    _prepare_schema(home_paths.schema, GlobalConfigFile)
    _ensure_directory(home_paths.cache)
    global_config = _prepare_config(home_paths.config, GlobalConfigFile, CONFIG_SCHEMA_REF)

    project_config = None
    local_config = None
    if project_paths is not None and local_paths is not None:
        _ensure_directory(project_paths.config.parent)
        _ensure_directory(project_paths.schema.parent)
        _prepare_schema(project_paths.schema, ProjectConfigFile)
        _prepare_schema(local_paths.schema, LocalConfigFile)
        project_config = _prepare_config(project_paths.config, ProjectConfigFile, CONFIG_SCHEMA_REF)
        if local_paths.config.exists():
            local_config = _prepare_config(local_paths.config, LocalConfigFile, LOCAL_CONFIG_SCHEMA_REF)

    return RuntimeContext(
        paths=paths,
        config=assemble_runtime_config(global_config, project_config, local_config),
        options=root_options,
    )


# ==============================================================================
# preflight helpers
# ==============================================================================


def _prepare_config(path: Path, model: type[BaseModel], schema_ref: str) -> BaseModel:
    try:
        return ensure_config_file(path, model, schema_ref=schema_ref)
    except ConfigError as error:
        raise PreflightError(error.code, error.values) from error


def _prepare_schema(path: Path, model: type[BaseModel]) -> None:
    try:
        ensure_schema_file(path, model)
    except ConfigError as error:
        raise PreflightError(error.code, error.values) from error


def _prepare_gitignore(path: Path) -> None:
    try:
        ensure_project_gitignore(path)
    except GitIgnoreError as error:
        raise PreflightError(error.code, error.values) from error


def _prepare_version(path: Path) -> None:
    try:
        ensure_version_file(path)
    except ConfigError as error:
        raise PreflightError(error.code, error.values) from error


def _ensure_directory(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise PreflightError(
            "root.error.preflight.directory_prepare_failed",
            {"path": str(path)},
        ) from error
