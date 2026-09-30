# apiscope/skill/install/preflight.py

from apiscope.skill.install.context import InstallCommandContext


# install writes only its own target and reads no cached asset.
def run_preflight(command_context: InstallCommandContext) -> None:
    del command_context
