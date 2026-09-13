# apiscope/preflight.py

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel

from apiscope.config import (
    ConfigError,
    assemble_runtime_config,
    build_global_paths,
    build_project_paths,
    ensure_config_file,
    ensure_schema_file,
    ensure_version_file,
    resolve_home,
)
from apiscope.constants import CONFIG_SCHEMA_REF, LOCAL_CONFIG_SCHEMA_REF
from apiscope.context import CommandContext
from apiscope.gitignore import GitIgnoreError, ensure_project_gitignore
from apiscope.schema import GlobalConfigFile, LocalConfigFile, ProjectConfigFile

# ==============================================================================
# errors
# ==============================================================================


class PreflightError(RuntimeError):
    """Raised when the execution context cannot be prepared safely."""


# ==============================================================================
# project discovery
# ==============================================================================


def find_project_root(start: Path | None = None) -> Path | None:
    """Find the nearest ancestor containing a Git directory or worktree file."""
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


def run_preflight(
    *,
    cwd: Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> CommandContext:
    """Prepare local assets and return the command context."""
    global_paths = build_global_paths(resolve_home(environment))
    _ensure_directory(global_paths.root)
    _prepare_version(global_paths.version)

    try:
        project_root = find_project_root(cwd)
    except OSError as error:
        location = str(cwd) if cwd is not None else "<current directory>"
        raise PreflightError(f"cannot inspect project path {location}; check the path and its permissions") from error
    project_paths = build_project_paths(project_root) if project_root is not None else None
    if project_paths is not None:
        _prepare_gitignore(project_paths.gitignore)

    _ensure_directory(global_paths.schema.parent)
    _prepare_schema(global_paths.schema, GlobalConfigFile)
    _ensure_directory(global_paths.cache)
    global_config = _prepare_config(global_paths.config, GlobalConfigFile, CONFIG_SCHEMA_REF)

    project_config = None
    local_config = None
    if project_paths is not None:
        _ensure_directory(project_paths.config_dir)
        _ensure_directory(project_paths.schema.parent)
        _prepare_schema(project_paths.schema, ProjectConfigFile)
        _prepare_schema(project_paths.local_schema, LocalConfigFile)
        project_config = _prepare_config(project_paths.config, ProjectConfigFile, CONFIG_SCHEMA_REF)
        if project_paths.local_config.exists():
            local_config = _prepare_config(project_paths.local_config, LocalConfigFile, LOCAL_CONFIG_SCHEMA_REF)

    return CommandContext(
        global_paths=global_paths,
        project_paths=project_paths,
        config=assemble_runtime_config(global_config, project_config, local_config),
    )


def _prepare_config(path: Path, model: type[BaseModel], schema_ref: str) -> BaseModel:
    try:
        return ensure_config_file(path, model, schema_ref=schema_ref)
    except ConfigError as error:
        raise PreflightError(str(error)) from error


def _prepare_schema(path: Path, model: type[BaseModel]) -> None:
    try:
        ensure_schema_file(path, model)
    except ConfigError as error:
        raise PreflightError(str(error)) from error


def _prepare_gitignore(path: Path) -> None:
    try:
        ensure_project_gitignore(path)
    except GitIgnoreError as error:
        raise PreflightError(str(error)) from error


def _prepare_version(path: Path) -> None:
    try:
        ensure_version_file(path)
    except ConfigError as error:
        raise PreflightError(str(error)) from error


def _ensure_directory(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise PreflightError(
            f"cannot prepare directory {path}; check permissions and choose a writable location"
        ) from error
