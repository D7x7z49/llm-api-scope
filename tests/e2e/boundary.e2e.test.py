# tests/e2e/boundary.e2e.test.py

from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e


def test_help_exits_zero(e2e_project: Path, run_cli) -> None:
    result = run_cli(["--help"], e2e_project)

    assert result.returncode == 0
    assert "Usage" in result.stdout


def test_unknown_command_exits_two(e2e_project: Path, run_cli) -> None:
    result = run_cli(["nope"], e2e_project)

    assert result.returncode == 2
    assert "No such command" in result.stderr


def test_missing_source_reports_without_a_traceback(e2e_project: Path, run_cli) -> None:
    result = run_cli(["read", "missing"], e2e_project)

    assert result.returncode == 1
    assert "read.error.name_not_found" in result.stderr
    assert "Traceback" not in result.stderr
