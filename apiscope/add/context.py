# apiscope/add/context.py

from dataclasses import dataclass

from apiscope.add.schema import AddOptions
from apiscope.context import RuntimeContext


@dataclass(frozen=True, slots=True)
class AddCommandContext:
    runtime: RuntimeContext
    options: AddOptions
