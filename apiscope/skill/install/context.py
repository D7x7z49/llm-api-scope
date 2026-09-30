# apiscope/skill/install/context.py

from dataclasses import dataclass

from apiscope.context import RuntimeContext
from apiscope.skill.install.schema import InstallOptions


@dataclass(frozen=True, slots=True)
class InstallCommandContext:
    runtime: RuntimeContext
    options: InstallOptions
