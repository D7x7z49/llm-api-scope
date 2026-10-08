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

SKILL_DESCRIPTION: Final = (
    "browse cached sources with add, remove, list, sync, view, and read; "
    "use when reading api specs, rfc standards, arXiv papers, or synced repo docs"
)

# ==============================================================================
# skill content
# ==============================================================================

CONTENT_TEMPLATE: Final = """\
```text
{usage}
```

MANAGEMENT COMMANDS
- `add` registers a source
- `sync` downloads a source into the cache
- `list` shows registered sources
- `remove` deletes a source

MATERIAL COMMANDS
- `view` shows the route tree of a cached source
- `read` prints the content at an address

PREREQUISITES
- run `add` before `sync`
- run `sync` before `view` or `read`

WORKFLOWS
- browse a source: `add`, `sync`, `view`, `read`
- narrow a tree: `view <address> --depth 1`
- filter a source list: `list <type> --limit 10`
"""

# ==============================================================================
# user-facing messages
# ==============================================================================

MESSAGE_TEMPLATES: Final[dict[str, str]] = {
    "skill.help.command": "print or install the agent skill",
    "skill.error.runtime_context_unavailable": "runtime context is unavailable",
}
