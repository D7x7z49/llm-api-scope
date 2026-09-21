# apiscope/sync/context.py
from dataclasses import dataclass

from apiscope.context import RuntimeContext
from apiscope.sync.schema import SyncOptions


@dataclass(frozen=True, slots=True)
class SyncCommandContext:
    runtime: RuntimeContext
    options: SyncOptions
