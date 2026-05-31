# apiscope/openapi/app.py

import typer

from apiscope.openapi.schema import OpenapiCommandContext
from apiscope.openapi.spec import spec_app

app = typer.Typer()

# ==============================================================================
# callback
# ==============================================================================


@app.callback()
def openapi_callback(ctx: typer.Context) -> None:
    ctx.obj.openapi_command_context = OpenapiCommandContext()


# ==============================================================================
# subcommands
# ==============================================================================

app.add_typer(spec_app, name="spec")
