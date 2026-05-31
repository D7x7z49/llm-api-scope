# apiscope/openapi/app.py

import typer

from apiscope.config import CACHE_ROOT
from apiscope.openapi.schema import OpenapiCommandContext
from apiscope.openapi.spec import spec_app

app = typer.Typer()

# ==============================================================================
# callback
# ==============================================================================


@app.callback()
def openapi_callback(
    ctx: typer.Context,
    source: str | None = typer.Argument(None, help="Alias for the OpenAPI spec"),
) -> None:
    cache_dir = CACHE_ROOT / "openapi"
    cache_dir.mkdir(parents=True, exist_ok=True)
    ctx.obj.openapi_command_context = OpenapiCommandContext(
        cache_dir=cache_dir,
        source_arg=source,
    )


# ==============================================================================
# subcommands
# ==============================================================================

app.add_typer(spec_app, name="spec")
