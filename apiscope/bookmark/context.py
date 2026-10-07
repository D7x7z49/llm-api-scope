# apiscope/bookmark/context.py

import typer

from apiscope.context import RuntimeContext
from apiscope.errors import MessageError


# resolve the runtime context every bookmark subcommand shares
def resolve_context(ctx: typer.Context) -> RuntimeContext:
    context = ctx.find_object(RuntimeContext)
    if context is None:
        raise MessageError("bookmark.error.runtime_context_unavailable")
    return context
