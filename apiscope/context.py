# apiscope/context.py

from dataclasses import dataclass, field
from pathlib import Path

from apiscope.schema import ConfigSchema

# ==============================================================================
# path structures
# ==============================================================================


@dataclass(frozen=True, slots=True)
class GlobalPaths:
    home: Path
    root: Path
    version: Path
    config: Path
    cache: Path


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    root: Path
    config_dir: Path
    config: Path


# ==============================================================================
# command context
# ==============================================================================


@dataclass(slots=True)
class CommandContext:
    global_paths: GlobalPaths
    project_paths: ProjectPaths | None
    global_config: ConfigSchema
    project_config: ConfigSchema | None
    command_name: str | None = None
    parameters: dict[str, object] = field(default_factory=dict)
    extras: dict[str, object] = field(default_factory=dict)
