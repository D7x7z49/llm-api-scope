# apiscope/bookmark/add/context.py

from dataclasses import dataclass

from apiscope.bookmark.add.schema import AddOptions
from apiscope.context import RuntimeContext


@dataclass(frozen=True, slots=True)
class AddCommandContext:
    runtime: RuntimeContext
    options: AddOptions
