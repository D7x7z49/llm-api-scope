# apiscope/bookmark/use/context.py

from dataclasses import dataclass

from apiscope.bookmark.use.schema import UseOptions
from apiscope.context import RuntimeContext


@dataclass(frozen=True, slots=True)
class UseCommandContext:
    runtime: RuntimeContext
    options: UseOptions
