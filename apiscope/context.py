# apiscope/context.py

from dataclasses import dataclass, field
from pathlib import Path

from apiscope.schema import RuntimeConfig

# ==============================================================================
# path structures
# ==============================================================================


@dataclass(frozen=True, slots=True)
class GlobalPaths:
    home: Path
    root: Path
    version: Path
    config: Path
    schema: Path
    cache: Path


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    root: Path
    gitignore: Path
    config_dir: Path
    config: Path
    schema: Path
    local_config: Path
    local_schema: Path


# ==============================================================================
# command context
# ==============================================================================


@dataclass(slots=True)
class CommandContext:
    global_paths: GlobalPaths
    project_paths: ProjectPaths | None
    config: RuntimeConfig
    command_name: str | None = None
    parameters: dict[str, object] = field(default_factory=dict)
    extras: dict[str, object] = field(default_factory=dict)
