# apiscope/view/context.py

from dataclasses import dataclass

from apiscope.context import RuntimeContext
from apiscope.view.schema import ViewOptions


@dataclass(frozen=True, slots=True)
class ViewCommandContext:
    runtime: RuntimeContext
    options: ViewOptions
