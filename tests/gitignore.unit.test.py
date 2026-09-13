# tests/gitignore.unit.test.py
from pathlib import Path

from apiscope.constants import APISCOPE_CONFIG_UNIGNORE_RULE, APISCOPE_IGNORE_RULE
from apiscope.gitignore import ensure_project_gitignore


def test_ensure_project_gitignore_creates_required_rules(tmp_path: Path) -> None:
    path = tmp_path / ".gitignore"

    ensure_project_gitignore(path)

    assert path.read_text(encoding="utf-8") == f"{APISCOPE_IGNORE_RULE}\n{APISCOPE_CONFIG_UNIGNORE_RULE}\n"


def test_ensure_project_gitignore_replaces_old_rule_and_preserves_other_rules(tmp_path: Path) -> None:
    path = tmp_path / ".gitignore"
    path.write_text("*.log\n.apiscope/\n.env\n", encoding="utf-8")

    ensure_project_gitignore(path)

    assert path.read_text(encoding="utf-8") == (
        f"*.log\n.env\n{APISCOPE_IGNORE_RULE}\n{APISCOPE_CONFIG_UNIGNORE_RULE}\n"
    )


def test_ensure_project_gitignore_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / ".gitignore"
    expected = f"# project rules\n{APISCOPE_IGNORE_RULE}\n{APISCOPE_CONFIG_UNIGNORE_RULE}\n"
    path.write_text(expected, encoding="utf-8")

    ensure_project_gitignore(path)

    assert path.read_text(encoding="utf-8") == expected


def test_ensure_project_gitignore_preserves_crlf_line_endings(tmp_path: Path) -> None:
    path = tmp_path / ".gitignore"
    path.write_bytes(b"# project rules\r\n.apiscope/\r\n")

    ensure_project_gitignore(path)

    assert path.read_bytes() == (
        f"# project rules\r\n{APISCOPE_IGNORE_RULE}\r\n{APISCOPE_CONFIG_UNIGNORE_RULE}\r\n".encode()
    )
