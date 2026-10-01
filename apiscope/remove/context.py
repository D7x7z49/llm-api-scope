# apiscope/remove/context.py

from dataclasses import dataclass

from apiscope.context import RuntimeContext
from apiscope.remove.schema import RemoveOptions


@dataclass(frozen=True, slots=True)
class RemoveCommandContext:
    runtime: RuntimeContext
    options: RemoveOptions
