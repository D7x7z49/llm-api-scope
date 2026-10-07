# apiscope/bookmark/list/context.py

from dataclasses import dataclass

from apiscope.bookmark.list.schema import ListOptions
from apiscope.context import RuntimeContext


@dataclass(frozen=True, slots=True)
class ListCommandContext:
    runtime: RuntimeContext
    options: ListOptions
