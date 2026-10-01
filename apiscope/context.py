# apiscope/context.py

from dataclasses import dataclass
from pathlib import Path

from apiscope.output import OutputFormat
from apiscope.schema import ConfigScope, RuntimeConfig

# ==============================================================================
# path values
# ==============================================================================


@dataclass(frozen=True, slots=True)
class BasePaths:
    config: Path
    schema: Path


@dataclass(frozen=True, slots=True)
class HomePaths(BasePaths):
    base: Path
    root: Path
    version: Path
    cache: Path


@dataclass(frozen=True, slots=True)
class ProjectPaths(BasePaths):
    root: Path
    gitignore: Path


@dataclass(frozen=True, slots=True)
class LocalPaths(BasePaths):
    pass


# project and local paths are absent when no project root is found.
@dataclass(frozen=True, slots=True)
class Paths:
    home: HomePaths
    project: ProjectPaths | None
    local: LocalPaths | None


# ==============================================================================
# root options
# ==============================================================================


@dataclass(frozen=True, slots=True)
class RootOptions:
    global_only: bool = False
    output_format: OutputFormat = OutputFormat.TEXT


# ==============================================================================
# runtime context
# ==============================================================================


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    paths: Paths
    config: RuntimeConfig
    options: RootOptions

    @property
    def scope(self) -> ConfigScope:
        if self.options.global_only or self.paths.project is None:
            return ConfigScope.HOME
        return ConfigScope.PROJECT
