# apiscope/list/context.py

from dataclasses import dataclass

from apiscope.context import RuntimeContext
from apiscope.list.schema import ListOptions


@dataclass(frozen=True, slots=True)
class ListCommandContext:
    runtime: RuntimeContext
    options: ListOptions
