# scripts/ci/usage.py

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from typer.core import TyperArgument, TyperGroup, TyperOption
from typer.main import get_command

from apiscope.app import app

ROOT_NAME = "apiscope"
INDENT = "  "
SKIP_OPTIONS = {"--install-completion", "--show-completion"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the apiscope usage reference.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", metavar="PATH", help="write the usage reference to PATH")
    group.add_argument("--check", metavar="PATH", help="fail when PATH differs from the generated usage")
    args = parser.parse_args()

    text = render_app()

    if args.write is not None:
        Path(args.write).write_text(text, encoding="utf-8")
        return 0
    if args.check is not None:
        path = Path(args.check)
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        if current != text:
            sys.stderr.write(f"{args.check} is out of date; run scripts/ci/usage.py --write {args.check}\n")
            return 1
        return 0
    sys.stdout.write(text)
    return 0


def render_app() -> str:
    root = get_command(app)
    lines = [f"- {ROOT_NAME} # {_describe(root.help)}"]
    _render_params(root, 1, lines)
    if isinstance(root, TyperGroup):
        for child in root.commands.values():
            _render_command(child, 1, lines)
    return "\n".join(lines) + "\n"


def _render_command(command, level: int, lines: list[str]) -> None:
    lines.append(f"{INDENT * level}- {command.name} # {_describe(command.help)}")
    _render_params(command, level + 1, lines)
    if isinstance(command, TyperGroup):
        for child in command.commands.values():
            _render_command(child, level + 1, lines)


def _render_params(command, level: int, lines: list[str]) -> None:
    for param in command.params:
        line = _render_param(param)
        if line is not None:
            lines.append(f"{INDENT * level}{line}")


def _render_param(param) -> str | None:
    if isinstance(param, TyperArgument):
        return _render_entry(param.name.upper(), param.required, param.multiple, param.help)
    if isinstance(param, TyperOption):
        options = [opt for opt in param.opts if opt not in SKIP_OPTIONS]
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


if __name__ == "__main__":
    raise SystemExit(main())
