# apiscope/openapi/app.py

import typer

from apiscope.openapi.doc import doc_app
from apiscope.openapi.schema import OpenapiCommandContext

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

app.add_typer(doc_app, name="doc")
