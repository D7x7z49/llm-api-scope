# tests/gitignore.integration.test.py
import subprocess
from pathlib import Path

from apiscope.preflight import run_preflight


def _is_ignored(project: Path, path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", "--", path],
        cwd=project,
        check=False,
    )
    return result.returncode == 0


def test_preflight_applies_root_scoped_ignore_rules(
    isolated_home: Path,
    git_project: Path,
) -> None:
    subprocess.run(["git", "init", "-q"], cwd=git_project, check=True)
    run_preflight(cwd=git_project)
    (git_project / ".apiscope" / "local.json").touch()
    nested = git_project / "packages" / "child" / ".apiscope"
    nested.mkdir(parents=True)
    (nested / "data").touch()

    assert not _is_ignored(git_project, ".apiscope/config.json")
    assert _is_ignored(git_project, ".apiscope/local.json")
    assert _is_ignored(git_project, ".apiscope/schema/config.schema.json")
    assert not _is_ignored(git_project, "packages/child/.apiscope/data")
