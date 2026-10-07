# apiscope/skill/context.py

import typer

from apiscope.context import RuntimeContext
from apiscope.errors import MessageError


# resolve the runtime context both skill subcommands share
def resolve_context(ctx: typer.Context) -> RuntimeContext:
    context = ctx.find_object(RuntimeContext)
    if context is None:
        raise MessageError("skill.error.runtime_context_unavailable")
    return context
