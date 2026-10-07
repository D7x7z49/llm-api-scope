# scripts/ci/layout.py
#
# check that the apiscope tree keeps the command scope shape.
#
# the path list is a snapshot, not a delta, so the caller supplies the full tree.
#
# every directory is a command scope named by one word. only two names are
# exceptions: [_lib], the private module, and [<command>_lib], the public module
# whose prefix names a sibling command. both exceptions are leaves. every command
# scope carries the fixed modules.
#
# findings go to stdout, because they are the normal result of the check.
# stderr is left for a crash or a usage error.
#
# usage:
#   git ls-tree -r --name-only HEAD apiscope | python scripts/ci/layout.py

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from pathlib import PurePosixPath

DEFAULT_ROOT = "apiscope"
PRIVATE_MODULE = "_lib"
PUBLIC_SUFFIX = "_lib"
WORD_RE = re.compile(r"^[a-z][a-z0-9]*$")
FIXED_MODULES = ("app.py", "constants.py", "context.py", "preflight.py", "schema.py")

Names = dict[PurePosixPath, set[str]]


def read_paths(lines: Iterable[str]) -> list[PurePosixPath]:
    return [PurePosixPath(text.strip()) for text in lines if text.strip()]


def build_tree(paths: Iterable[PurePosixPath], root: str) -> tuple[Names, Names]:
    children: Names = {}
    files: Names = {}
    for path in paths:
        if path.parts[:1] != (root,) or len(path.parts) < 2:
            continue
        files.setdefault(PurePosixPath(*path.parts[:-1]), set()).add(path.name)
        for depth in range(2, len(path.parts)):
            parent = PurePosixPath(*path.parts[: depth - 1])
            children.setdefault(parent, set()).add(path.parts[depth - 1])
    return children, files


def check(children: Names, files: Names, root: str) -> list[str]:
    problems: list[str] = []
    pending = [PurePosixPath(root)]
    while pending:
        scope = pending.pop()
        present = files.get(scope, set())
        missing = [module for module in FIXED_MODULES if module not in present]
        if missing:
            problems.append(f"{scope}: command scope is missing {', '.join(missing)}")
        names = children.get(scope, set())
        for name in sorted(names):
            child = scope / name
            if name == PRIVATE_MODULE:
                continue
            if name.endswith(PUBLIC_SUFFIX):
                prefix = name[: -len(PUBLIC_SUFFIX)]
                if prefix not in names:
                    problems.append(f"{child}: public module has no sibling command {prefix}")
                continue
            if WORD_RE.match(name) is None:
                problems.append(f"{child}: directory name must be a single word")
                continue
            pending.append(child)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the apiscope scope shape.")
    parser.add_argument("--root", default=DEFAULT_ROOT, help="the scope root to check")
    args = parser.parse_args()

    children, files = build_tree(read_paths(sys.stdin), args.root)
    problems = check(children, files, args.root)
    for problem in sorted(problems):
        print(f"[!] {problem}")
    if problems:
        return 1
    print("[+] apiscope layout ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
