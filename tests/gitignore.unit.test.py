# tests/gitignore.unit.test.py

from pathlib import Path

import pytest

from apiscope.constants import APISCOPE_IGNORE_RULE
from apiscope.gitignore import GitIgnoreError, ensure_project_gitignore


def test_ensure_project_gitignore_creates_the_state_rule(tmp_path: Path) -> None:
    path = tmp_path / ".gitignore"

    ensure_project_gitignore(path)

    assert path.read_text(encoding="utf-8") == f"{APISCOPE_IGNORE_RULE}\n"


@pytest.mark.parametrize("rule", [f"{APISCOPE_IGNORE_RULE}", "/.apiscope/", "/.apiscope/*"])
def test_ensure_project_gitignore_accepts_covering_rules(tmp_path: Path, rule: str) -> None:
    path = tmp_path / ".gitignore"
    content = f"# project rules\n{rule}\n"
    path.write_text(content, encoding="utf-8")

    ensure_project_gitignore(path)

    assert path.read_text(encoding="utf-8") == content


def test_ensure_project_gitignore_keeps_a_legacy_unignore_pair(tmp_path: Path) -> None:
    path = tmp_path / ".gitignore"
    content = "/.apiscope/*\n!/.apiscope/config.json\n"
    path.write_text(content, encoding="utf-8")

    ensure_project_gitignore(path)

    assert path.read_text(encoding="utf-8") == content


def test_ensure_project_gitignore_appends_after_existing_rules(tmp_path: Path) -> None:
    path = tmp_path / ".gitignore"
    path.write_text("*.log\n.env\n", encoding="utf-8")

    ensure_project_gitignore(path)

    assert path.read_text(encoding="utf-8") == f"*.log\n.env\n{APISCOPE_IGNORE_RULE}\n"


def test_ensure_project_gitignore_separates_a_missing_final_newline(tmp_path: Path) -> None:
    path = tmp_path / ".gitignore"
    path.write_text("*.log", encoding="utf-8")

    ensure_project_gitignore(path)

    assert path.read_text(encoding="utf-8") == f"*.log\n{APISCOPE_IGNORE_RULE}\n"


def test_ensure_project_gitignore_preserves_crlf_line_endings(tmp_path: Path) -> None:
    path = tmp_path / ".gitignore"
    path.write_bytes(b"# project rules\r\n.env\r\n")

    ensure_project_gitignore(path)

    assert path.read_bytes() == f"# project rules\r\n.env\r\n{APISCOPE_IGNORE_RULE}\r\n".encode()


def test_ensure_project_gitignore_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / ".gitignore"
    expected = f"# project rules\n{APISCOPE_IGNORE_RULE}\n"
    path.write_text(expected, encoding="utf-8")

    ensure_project_gitignore(path)

    assert path.read_text(encoding="utf-8") == expected


def test_ensure_project_gitignore_rejects_a_directory(tmp_path: Path) -> None:
    path = tmp_path / ".gitignore"
    path.mkdir()

    with pytest.raises(GitIgnoreError, match="not a file"):
        ensure_project_gitignore(path)
