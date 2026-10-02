# tests/sync/_lib/repo/repo-fetcher.integration.test.py

import subprocess
from pathlib import Path

import pytest

from apiscope.source import LocalLocation, RepoSource
from apiscope.sync._lib.repo.fetcher import RepoFetcher


def _run_git(git: str, args: list[str], cwd: Path) -> str:
    result = subprocess.run([git, *args], cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _commit(git: str, root: Path, message: str) -> None:
    _run_git(git, ["-c", "user.email=e2e@example.test", "-c", "user.name=e2e", "commit", "-qm", message], root)


def _make_repository(git: str, root: Path) -> Path:
    root.mkdir()
    _run_git(git, ["init", "-q", "-b", "main"], root)
    (root / "ROOT.md").write_text("one\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "intro.md").write_text("intro\n", encoding="utf-8")
    (root / "docs" / "api.md").write_text("api\n", encoding="utf-8")
    _run_git(git, ["add", "-A"], root)
    _commit(git, root, "one")
    _run_git(git, ["tag", "v1.0.0"], root)
    _run_git(git, ["branch", "feature"], root)
    (root / "ROOT.md").write_text("one\ntwo\n", encoding="utf-8")
    _run_git(git, ["add", "-A"], root)
    _commit(git, root, "two")
    return root


def _parsed(repository: Path, *, subpath: str | None = None, ref: str | None = None) -> RepoSource:
    return RepoSource(
        original=repository.as_posix(),
        canonical=repository.resolve().as_posix(),
        location=LocalLocation(repository.resolve()),
        subpath=subpath,
        ref=ref,
    )


def test_repo_fetcher_selects_only_the_subpath(tmp_path: Path, git_executable: str) -> None:
    repository = _make_repository(git_executable, tmp_path / "repository")

    RepoFetcher().fetch(_parsed(repository, subpath="docs"), destination=tmp_path / "staging")

    content = tmp_path / "staging" / "content"
    assert (content / "intro.md").read_text(encoding="utf-8") == "intro\n"
    assert (content / "api.md").read_text(encoding="utf-8") == "api\n"
    assert not (content / "ROOT.md").exists()
    assert not (content / ".git").exists()
    assert not (tmp_path / ".staging.git").exists()


def test_repo_fetcher_copies_the_whole_repository_without_a_subpath(tmp_path: Path, git_executable: str) -> None:
    repository = _make_repository(git_executable, tmp_path / "repository")

    RepoFetcher().fetch(_parsed(repository, ref="main"), destination=tmp_path / "staging")

    content = tmp_path / "staging" / "content"
    assert (content / "ROOT.md").read_text(encoding="utf-8") == "one\ntwo\n"
    assert (content / "docs" / "intro.md").read_text(encoding="utf-8") == "intro\n"
    assert not (content / ".git").exists()


@pytest.mark.parametrize(
    ("ref_kind", "expected"),
    [
        pytest.param("branch", "one\ntwo\n", id="branch"),
        pytest.param("tag", "one\n", id="tag"),
        pytest.param("branch-off-head", "one\n", id="branch-off-head"),
        pytest.param("short-hash", "one\ntwo\n", id="short-hash"),
        pytest.param("full-hash", "one\ntwo\n", id="full-hash"),
    ],
)
def test_repo_fetcher_checks_out_common_ref_kinds(
    tmp_path: Path,
    git_executable: str,
    ref_kind: str,
    expected: str,
) -> None:
    repository = _make_repository(git_executable, tmp_path / "repository")
    head = _run_git(git_executable, ["rev-parse", "HEAD"], repository)
    refs = {
        "branch": "main",
        "tag": "v1.0.0",
        "branch-off-head": "feature",
        "short-hash": head[:7],
        "full-hash": head,
    }

    RepoFetcher().fetch(_parsed(repository, ref=refs[ref_kind]), destination=tmp_path / "staging")

    content = tmp_path / "staging" / "content"
    assert (content / "ROOT.md").read_text(encoding="utf-8") == expected
