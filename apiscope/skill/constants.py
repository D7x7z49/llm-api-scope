# apiscope/skill/constants.py

from typing import Final

# ==============================================================================
# command
# ==============================================================================

COMMAND_NAME: Final = "skill"

# ==============================================================================
# skill identity
# ==============================================================================

SKILL_NAME: Final = "apiscope"

# ==============================================================================
# user-facing messages
# ==============================================================================

MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "skill.help.command": "print or install the agent skill",
    "skill.error.runtime_context_unavailable": "runtime context is unavailable",
}
