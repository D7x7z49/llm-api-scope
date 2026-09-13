# apiscope/gitignore.py
from pathlib import Path

from apiscope.constants import APISCOPE_CONFIG_UNIGNORE_RULE, APISCOPE_IGNORE_RULE


class GitIgnoreError(RuntimeError):
    """Raised when the project ignore file cannot be prepared safely."""


_LEGACY_APISCOPE_IGNORE_RULES = {".apiscope/", "/.apiscope/"}
_REQUIRED_RULES = (APISCOPE_IGNORE_RULE, APISCOPE_CONFIG_UNIGNORE_RULE)
_RULES_TO_REPLACE = _LEGACY_APISCOPE_IGNORE_RULES | set(_REQUIRED_RULES)


def ensure_project_gitignore(path: Path) -> None:
    """Create or repair the root project ignore rules."""
    if path.exists():
        if not path.is_file():
            raise GitIgnoreError(f"cannot use {path}; the path is not a file")
        try:
            with path.open("r", encoding="utf-8", newline="") as file:
                current = file.read()
        except OSError as error:
            raise GitIgnoreError(f"cannot read {path}; check the file and its permissions") from error
    else:
        current = ""

    newline = "\r\n" if "\r\n" in current else "\n"
    lines = current.splitlines()
    retained = [line for line in lines if line.strip() not in _RULES_TO_REPLACE]
    updated = newline.join([*retained, *_REQUIRED_RULES]) + newline

    if updated == current:
        return

    try:
        with path.open("w", encoding="utf-8", newline="") as file:
            file.write(updated)
    except OSError as error:
        raise GitIgnoreError(f"cannot write {path}; check the file and its permissions") from error
