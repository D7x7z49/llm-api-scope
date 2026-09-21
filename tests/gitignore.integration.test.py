# tests/gitignore.integration.test.py

import subprocess
from pathlib import Path

from apiscope.constants import APISCOPE_IGNORE_RULE
from apiscope.preflight import run_preflight


def _is_ignored(git_executable: str, project: Path, path: str) -> bool:
    result = subprocess.run(
        [git_executable, "check-ignore", "--no-index", "-q", "--", path],
        cwd=project,
        check=False,
    )
    return result.returncode == 0


def test_preflight_ignores_the_state_directory_at_every_depth(
    isolated_home: Path,
    git_project: Path,
    git_executable: str,
) -> None:
    subprocess.run([git_executable, "init", "-q"], cwd=git_project, check=True)
    run_preflight(cwd=git_project)
    (git_project / ".apiscope" / "local.json").touch()
    nested = git_project / "packages" / "child" / ".apiscope"
    nested.mkdir(parents=True)
    (nested / "data").touch()

    assert (git_project / ".gitignore").read_text(encoding="utf-8") == f"{APISCOPE_IGNORE_RULE}\n"
    assert _is_ignored(git_executable, git_project, ".apiscope/config.json")
    assert _is_ignored(git_executable, git_project, ".apiscope/local.json")
    assert _is_ignored(git_executable, git_project, ".apiscope/schema/config.schema.json")
    assert _is_ignored(git_executable, git_project, "packages/child/.apiscope/data")


def test_preflight_keeps_existing_user_rules_untouched(
    isolated_home: Path,
    git_project: Path,
    git_executable: str,
) -> None:
    subprocess.run([git_executable, "init", "-q"], cwd=git_project, check=True)
    gitignore = git_project / ".gitignore"
    content = f"{APISCOPE_IGNORE_RULE}\n*.log\n"
    gitignore.write_text(content, encoding="utf-8")

    run_preflight(cwd=git_project)

    assert gitignore.read_text(encoding="utf-8") == content
