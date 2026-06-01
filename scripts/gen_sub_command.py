# scripts/gen_sub_command.py
#
# generate a subcommand directory skeleton under apiscope/.
#
# only creates new directories — never updates existing ones.
# registering the subcommand in its parent app.py is a manual step.
#
# Usage:
#   python scripts/gen_sub_command.py [<parent>...] <name>

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APISCOPE = ROOT / "apiscope"

INIT = """\
# {path}

from {modmodule}.app import app as {name}_app

__all__ = ["{name}_app"]
"""

SCHEMA = """\
# {path}

from pydantic import BaseModel


class {className}CommandContext(BaseModel):
    pass
"""

APP = """\
# {path}

import typer

from {modmodule}.schema import {className}CommandContext

app = typer.Typer()


@app.callback()
def {name}_callback(ctx: typer.Context) -> None:
    ctx.obj.{assignment} = {className}CommandContext()

"""


def _pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def _build_assignment(parents: list[str], name: str) -> str:
    chain = ".".join(f"{p}_command_context" for p in parents)
    if chain:
        return f"{chain}.{name}_command_context"
    return f"{name}_command_context"


def main(sub_commands: list[str]) -> None:
    if not sub_commands:
        print("Usage: python scripts/gen_sub_command.py <parent>... <name>", file=sys.stderr)
        sys.exit(1)

    name = sub_commands[-1]
    parents = sub_commands[:-1]

    parent_pkg = ".".join(["apiscope"] + parents)
    parent_dir = APISCOPE.joinpath(*parents)
    package = f"{parent_pkg}.{name}"
    target_dir = parent_dir / name
    modmodule = f"{parent_pkg}.{name}"

    if target_dir.exists():
        print(f"already exists: {target_dir}")
        sys.exit(1)

    target_dir.mkdir(parents=True)

    file_path = package.replace(".", "/")

    # __init__.py
    (target_dir / "__init__.py").write_text(
        INIT.format(path=f"{file_path}/__init__.py", modmodule=modmodule, name=name)
    )

    # schema.py
    (target_dir / "schema.py").write_text(
        SCHEMA.format(
            path=f"{file_path}/schema.py",
            className=_pascal_case(name),
        )
    )

    # app.py
    (target_dir / "app.py").write_text(
        APP.format(
            path=f"{file_path}/app.py",
            modmodule=modmodule,
            className=_pascal_case(name),
            name=name,
            assignment=_build_assignment(parents, name),
        )
    )

    print(f"created: {target_dir}")
    for f in sorted(target_dir.iterdir()):
        print(f"  {f.name}")


if __name__ == "__main__":
    main(sys.argv[1:])
