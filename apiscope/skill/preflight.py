# apiscope/skill/preflight.py

import typer

from apiscope.skill.constants import CONTENT_TEMPLATE, SKILL_DESCRIPTION, SKILL_NAME
from apiscope.skill.schema import SkillDocument
from apiscope.usage import render_usage


# build the skill document before show prints it or install writes it
def render_document(ctx: typer.Context) -> SkillDocument:
    usage = render_usage(ctx.find_root().command).rstrip("\n")
    content = CONTENT_TEMPLATE.format(usage=usage).rstrip("\n")
    return SkillDocument(name=SKILL_NAME, description=SKILL_DESCRIPTION, content=content)
