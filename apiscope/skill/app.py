# apiscope/skill/app.py

import typer

from apiscope.skill.constants import COMMAND_NAME, MESSAGE_TEMPLATES
from apiscope.skill.install.app import app as install_app
from apiscope.skill.install.constants import COMMAND_NAME as INSTALL_COMMAND_NAME
from apiscope.skill.show.app import app as show_app
from apiscope.skill.show.constants import COMMAND_NAME as SHOW_COMMAND_NAME

# ==============================================================================
# app
# ==============================================================================

app = typer.Typer(
    name=COMMAND_NAME,
    help=MESSAGE_TEMPLATES["skill.help.command"],
)

app.add_typer(show_app, name=SHOW_COMMAND_NAME)
app.add_typer(install_app, name=INSTALL_COMMAND_NAME)
