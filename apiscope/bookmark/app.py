# apiscope/bookmark/app.py

import typer

from apiscope.bookmark.add.app import app as add_app
from apiscope.bookmark.add.constants import COMMAND_NAME as ADD_COMMAND_NAME
from apiscope.bookmark.constants import COMMAND_NAME, MESSAGE_TEMPLATES
from apiscope.bookmark.list.app import app as list_app
from apiscope.bookmark.list.constants import COMMAND_NAME as LIST_COMMAND_NAME
from apiscope.bookmark.prune.app import app as prune_app
from apiscope.bookmark.prune.constants import COMMAND_NAME as PRUNE_COMMAND_NAME
from apiscope.bookmark.remove.app import app as remove_app
from apiscope.bookmark.remove.constants import COMMAND_NAME as REMOVE_COMMAND_NAME
from apiscope.bookmark.use.app import app as use_app
from apiscope.bookmark.use.constants import COMMAND_NAME as USE_COMMAND_NAME

# ==============================================================================
# app
# ==============================================================================

app = typer.Typer(
    name=COMMAND_NAME,
    help=MESSAGE_TEMPLATES["bookmark.help.command"],
)

app.add_typer(add_app, name=ADD_COMMAND_NAME)
app.add_typer(remove_app, name=REMOVE_COMMAND_NAME)
app.add_typer(list_app, name=LIST_COMMAND_NAME)
app.add_typer(use_app, name=USE_COMMAND_NAME)
app.add_typer(prune_app, name=PRUNE_COMMAND_NAME)
