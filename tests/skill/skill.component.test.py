# tests/skill/skill.component.test.py
# ruff: noqa: N999

import json
from pathlib import Path

from typer.testing import CliRunner

from apiscope.lock import acquire_write_lock
from apiscope.main import app


def test_skill_show_prints_the_content_in_the_report_envelope(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["skill", "show"], catch_exceptions=False)

    assert result.exit_code == 0
    assert result.output.startswith("[ok] [scope=project] [action=show] [name=apiscope]\n")
    assert "\n---\n\n" in result.output
    assert "```text\n- apiscope #" in result.output
    assert "MANAGEMENT COMMANDS" in result.output
    assert "description:" not in result.output


def test_skill_without_a_subcommand_does_not_run(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["skill"], catch_exceptions=False)

    assert "MANAGEMENT COMMANDS" not in result.output


def test_skill_show_json_holds_the_content_lines(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["--json", "skill", "show"], catch_exceptions=False)

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "ok"
    assert payload["action"] == "show"
    assert payload["data"][0] == "```text"
    assert payload["extra"]["count"] == len(payload["data"])


def test_skill_install_writes_the_skill_directory(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    target = tmp_path / "skills" / "apiscope"

    result = runner.invoke(app, ["skill", "install", str(target)], catch_exceptions=False)

    assert result.exit_code == 0
    written = target / "SKILL.md"
    assert written.is_file()
    assert written.read_text(encoding="utf-8").startswith("---\nname: apiscope\n")


def test_skill_install_reports_a_held_lock(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    held = acquire_write_lock(isolated_home / ".apiscope")
    try:
        result = CliRunner().invoke(app, ["skill", "install", str(tmp_path / "skills")], catch_exceptions=False)
    finally:
        held.release()

    assert result.exit_code == 1
    assert "root.error.write_lock.busy" in result.output
    assert not (tmp_path / "skills").exists()


def test_skill_show_does_not_take_the_write_lock(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    held = acquire_write_lock(isolated_home / ".apiscope")
    try:
        result = CliRunner().invoke(app, ["skill", "show"], catch_exceptions=False)
    finally:
        held.release()

    assert result.exit_code == 0
