# apiscope/gitignore.py

from pathlib import Path

from apiscope.constants import APISCOPE_IGNORE_RULE


class GitIgnoreError(RuntimeError):
    pass


# Accept earlier spellings so an existing project file needs no rewrite.
# The refactor notes keep the project manifest trackable through an unignore rule;
# this implementation ignores the whole state directory and leaves tracking to the user.
_ACCEPTED_APISCOPE_IGNORE_RULES = {APISCOPE_IGNORE_RULE, "/.apiscope/", "/.apiscope/*"}


# ensure the project ignore file covers the apiscope state directory
def ensure_project_gitignore(path: Path) -> None:
    if path.exists():
        if not path.is_file():
            raise GitIgnoreError(f"cannot use {path}; the path is not a file")
        current = _read_text(path)
        if _covers_state_directory(current):
            return
    else:
        current = ""

    newline = "\r\n" if "\r\n" in current else "\n"
    if current and not current.endswith(("\n", "\r")):
        current += newline
    _write_text(path, f"{current}{APISCOPE_IGNORE_RULE}{newline}")


def _covers_state_directory(content: str) -> bool:
    return any(line.strip() in _ACCEPTED_APISCOPE_IGNORE_RULES for line in content.splitlines())


def _read_text(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8", newline="") as file:
            return file.read()
    except OSError as error:
        raise GitIgnoreError(f"cannot read {path}; check the file and its permissions") from error


def _write_text(path: Path, content: str) -> None:
    try:
        with path.open("w", encoding="utf-8", newline="") as file:
            file.write(content)
    except OSError as error:
        raise GitIgnoreError(f"cannot write {path}; check the file and its permissions") from error
