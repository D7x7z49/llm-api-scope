# apiscope/usage.py

from __future__ import annotations

from typer._click.core import Command
from typer.core import TyperArgument, TyperGroup, TyperOption
from typer.main import get_install_completion_arguments

from apiscope.constants import APP_NAME

# ==============================================================================
# constants
# ==============================================================================

INDENT = "  "

# typer injects the completion options into every command; the reference excludes them
_COMPLETION_PARAM_NAMES = frozenset(
    param.name for param in get_install_completion_arguments() if param.name is not None
)

# ==============================================================================
# renderer
# ==============================================================================


# render the usage DSL from a command tree without importing the root app
def render_usage(root: Command) -> str:
    lines = [f"- {APP_NAME} # {_describe(root.help)}"]
    _render_params(root, 1, lines)
    if isinstance(root, TyperGroup):
        for child in root.commands.values():
            _render_command(child, 1, lines)
    return "\n".join(lines) + "\n"


def _render_command(command: Command, level: int, lines: list[str]) -> None:
    lines.append(f"{INDENT * level}- {command.name} # {_describe(command.help)}")
    _render_params(command, level + 1, lines)
    if isinstance(command, TyperGroup):
        for child in command.commands.values():
            _render_command(child, level + 1, lines)


def _render_params(command: Command, level: int, lines: list[str]) -> None:
    for param in command.params:
        if param.name in _COMPLETION_PARAM_NAMES:
            continue
        line = _render_param(param)
        if line is not None:
            lines.append(f"{INDENT * level}{line}")


def _render_param(param: object) -> str | None:
    if isinstance(param, TyperArgument):
        return _render_entry((param.name or "").upper(), param.required, param.multiple, param.help)
    if isinstance(param, TyperOption):
        options = list(param.opts)
        if not options:
            return None
        key = next((opt for opt in options if opt.startswith("--")), options[0])
        return _render_entry(key, param.required, param.multiple, param.help)
    return None


def _render_entry(key: str, required: bool, multiple: bool, help_text: str | None) -> str:
    repeat = "..." if multiple else ""
    optional = "" if required else "?"
    return f"+ [{key}]{repeat}{optional} # {_describe(help_text)}"


def _describe(text: str | None) -> str:
    if text is None:
        return ""
    return " ".join(text.split())
