# apiscope/skill/show/context.py

from dataclasses import dataclass

from apiscope.context import RuntimeContext
from apiscope.skill.show.schema import ShowOptions


@dataclass(frozen=True, slots=True)
class ShowCommandContext:
    runtime: RuntimeContext
    options: ShowOptions
