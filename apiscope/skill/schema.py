# apiscope/skill/schema.py

from dataclasses import dataclass


# the rendered skill document that show prints and install writes
@dataclass(frozen=True, slots=True)
class SkillDocument:
    name: str
    description: str
    content: str
