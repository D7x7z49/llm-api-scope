# apiscope/bookmark/remove/context.py

from dataclasses import dataclass

from apiscope.bookmark.remove.schema import RemoveOptions
from apiscope.context import RuntimeContext


@dataclass(frozen=True, slots=True)
class RemoveCommandContext:
    runtime: RuntimeContext
    options: RemoveOptions
