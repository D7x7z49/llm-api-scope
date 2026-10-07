# apiscope/bookmark/prune/context.py

from dataclasses import dataclass

from apiscope.bookmark.prune.schema import PruneOptions
from apiscope.context import RuntimeContext


@dataclass(frozen=True, slots=True)
class PruneCommandContext:
    runtime: RuntimeContext
    options: PruneOptions
