# apiscope/skill/install/constants.py

from typing import Final

# ==============================================================================
# command
# ==============================================================================

COMMAND_NAME: Final = "install"

# ==============================================================================
# skill markdown
# ==============================================================================

SKILL_FILENAME: Final = "SKILL.md"
DEFAULT_INSTALL_TARGET: Final = "~/.agents/skills/apiscope"

MARKDOWN_TEMPLATE: Final = """\
---
name: {name}
description: {description}
---

{content}
"""

# ==============================================================================
# user-facing messages
# ==============================================================================

MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "skill.install.help.command": "install the skill directory",
    "skill.install.help.argument.target": "install directory, defaulting to ~/.agents/skills/apiscope",
    "skill.install.error.invalid_options": "invalid install options",
    "skill.install.error.install_failed": "cannot install the skill at {path}",
}
