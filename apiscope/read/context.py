# apiscope/read/context.py

from dataclasses import dataclass

from apiscope.context import RuntimeContext
from apiscope.read.schema import ReadOptions


@dataclass(frozen=True, slots=True)
class ReadCommandContext:
    runtime: RuntimeContext
    options: ReadOptions
