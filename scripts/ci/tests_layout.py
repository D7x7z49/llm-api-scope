# scripts/ci/tests_layout.py
#
# check that the tests tree keeps the test scope shape.
#
# a test path mirrors the package path. a test file names its topic and its
# kind. fixtures live in a conftest; data lives under fixtures. e2e is its own
# scope and mirrors nothing.
#
# findings go to stdout, because they are the normal result of the check.
# stderr is left for a crash or a usage error.
#
# usage:
#   pdm run python scripts/ci/tests_layout.py

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_ROOT = "tests"
DEFAULT_MIRROR = "apiscope"
KINDS = ("unit", "component", "integration", "e2e")
ROOT_DOCS = ("README.md", "AGENTS.md", "layout.txt")
IGNORED = frozenset({"__pycache__"})
FIXTURE_ROOT = "fixtures"
FIXTURE_DIRS = ("documents", "golden")
E2E = "e2e"
CONFTEST = "conftest.py"
TEST_SUFFIX = ".test.py"
FIXTURE_DECORATOR = "@pytest.fixture"
TOPIC_RE = re.compile(r"^[a-z][a-z0-9_]*(?:-[a-z0-9_]+)*$")


def kind_of(name: str) -> str | None:
    if not name.endswith(TEST_SUFFIX):
        return None
    topic, _, kind = name[: -len(TEST_SUFFIX)].rpartition(".")
    if kind in KINDS and TOPIC_RE.match(topic):
        return kind
    return None


def walk(root: Path) -> tuple[set[Path], list[Path]]:
    directories: set[Path] = set()
    files: list[Path] = []
    for path in root.rglob("*"):
        if IGNORED.intersection(path.parts):
            continue
        relative = path.relative_to(root)
        if path.is_dir():
            directories.add(relative)
        elif path.is_file():
            files.append(relative)
    return directories, sorted(files)


def check_file(root: Path, relative: Path, mirror_dirs: set[Path]) -> list[str]:
    path = root / relative
    first = relative.parts[0]
    name = relative.name

    if first == FIXTURE_ROOT:
        return check_fixture(root, relative)

    if len(relative.parts) == 1 and name in ROOT_DOCS:
        return []

    if name == CONFTEST:
        if len(relative.parts) == 1 or first == E2E or relative.parent in mirror_dirs:
            return []
        return [f"{path}: conftest sits outside a mirror scope"]

    if not name.endswith(".py"):
        return [f"{path}: a data file must live under fixtures"]

    kind = kind_of(name)
    if kind is None:
        return [f"{path}: a test file must be topic.kind.test.py"]
    if first == E2E and kind != E2E:
        return [f"{path}: e2e holds only e2e tests"]
    if first != E2E and kind == E2E:
        return [f"{path}: an e2e test must live under tests/e2e"]
    if FIXTURE_DECORATOR in path.read_text(encoding="utf-8"):
        return [f"{path}: a test module defines a fixture"]
    return []


def check_fixture(root: Path, relative: Path) -> list[str]:
    path = root / relative
    problems = []
    if len(relative.parts) >= 2 and relative.parts[1] not in FIXTURE_DIRS:
        problems.append(f"{path}: fixtures holds only documents and golden")
    if relative.suffix == ".py":
        problems.append(f"{path}: fixtures holds data, not python")
    return problems


def check(root: Path, mirror: Path) -> list[str]:
    problems: list[str] = []
    mirror_dirs, _ = walk(mirror)
    test_dirs, test_files = walk(root)

    for directory in sorted(test_dirs):
        if directory.parts[0] in {FIXTURE_ROOT, E2E}:
            continue
        if directory not in mirror_dirs:
            problems.append(f"{root / directory}: directory has no apiscope match")

    for relative in test_files:
        problems.extend(check_file(root, relative, mirror_dirs))
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the tests scope shape.")
    parser.add_argument("--root", default=DEFAULT_ROOT, help="the scope root to check")
    parser.add_argument("--mirror", default=DEFAULT_MIRROR, help="the package root to mirror")
    args = parser.parse_args()

    problems = check(Path(args.root), Path(args.mirror))
    for problem in sorted(problems):
        print(f"[!] {problem}")
    if problems:
        return 1
    print("[+] tests layout ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
