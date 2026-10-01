# apiscope/skill/show/preflight.py

from apiscope.skill.show.context import ShowCommandContext


# show reads no cached asset and writes nothing.
def run_preflight(command_context: ShowCommandContext) -> None:
    del command_context
