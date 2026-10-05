# tests/sync/_lib/repo/repo-fetcher.unit.test.py
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from apiscope.source import LocalLocation, RemoteLocation, RepoSource
from apiscope.sync._lib.errors import SourceFetchError
from apiscope.sync._lib.repo import fetcher as repo_fetcher
from apiscope.sync._lib.repo.fetcher import RepoFetcher


def _parsed_source(path: Path, *, subpath: str | None = None, ref: str | None = None) -> RepoSource:
    return RepoSource(
        original=str(path),
        location=LocalLocation(path.resolve()),
        subpath=subpath,
        ref=ref,
    )


def _remote_source(url: str, *, subpath: str | None = None, ref: str | None = None) -> RepoSource:
    return RepoSource(
        original=url,
        location=RemoteLocation(url),
        subpath=subpath,
        ref=ref,
    )


def test_repo_fetcher_copies_a_mocked_clone_without_git_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        worktree = Path(command[-1])
        (worktree / ".git").mkdir(parents=True)
        (worktree / "README.md").write_text("hello\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", fake_run)
    destination = tmp_path / "staging"

    result = RepoFetcher().fetch(
        _parsed_source(tmp_path / "source-repository"),
        destination=destination,
    )

    assert commands == [
        [
            "/usr/bin/git",
            "clone",
            "--depth=1",
            (tmp_path / "source-repository").resolve().as_posix(),
            str(tmp_path / ".staging.git"),
        ]
    ]
    assert result.content_kind == "directory"
    assert result.content_name is None
    assert (destination / "content" / "README.md").read_text(encoding="utf-8") == "hello\n"
    assert not (destination / "content" / ".git").exists()
    assert not (tmp_path / ".staging.git").exists()
    assert result.content_digest


def test_repo_fetcher_passes_a_configured_http_proxy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[list[str]] = []
    environments: list[object] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        environments.append(kwargs["env"])
        worktree = Path(command[-1])
        (worktree / "README.md").parent.mkdir(parents=True)
        (worktree / "README.md").write_text("hello\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", fake_run)

    RepoFetcher().fetch(
        _remote_source("https://example.test/docs.git"),
        destination=tmp_path / "staging",
        proxy="http://proxy.example.test:8080",
    )

    assert commands[0][:5] == [
        "/usr/bin/git",
        "-c",
        "http.proxy=http://proxy.example.test:8080",
        "-c",
        "https.proxy=http://proxy.example.test:8080",
    ]
    assert commands[0][5] == "clone"
    # the git process inherits the environment, so it keeps its own proxy settings
    assert environments[0] is None


def test_repo_fetcher_leaves_the_git_environment_without_a_configured_proxy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[list[str]] = []
    environments: list[object] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        environments.append(kwargs["env"])
        worktree = Path(command[-1])
        worktree.mkdir(parents=True)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", fake_run)

    RepoFetcher().fetch(
        _remote_source("https://example.test/docs.git"),
        destination=tmp_path / "staging",
    )

    assert commands[0][1:3] == ["clone", "--depth=1"]
    assert "-c" not in commands[0]
    assert environments[0] is None


def test_repo_fetcher_passes_a_configured_no_proxy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    environments: list[object] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        environments.append(kwargs["env"])
        worktree = Path(command[-1])
        worktree.mkdir(parents=True)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", fake_run)

    RepoFetcher().fetch(
        _remote_source("https://example.test/docs.git"),
        destination=tmp_path / "staging",
        no_proxy="example.test,internal.test",
    )

    assert isinstance(environments[0], dict)
    assert environments[0]["NO_PROXY"] == "example.test,internal.test"
    assert environments[0]["no_proxy"] == "example.test,internal.test"


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("ssh://git@example.test/docs.git", id="ssh"),
        pytest.param("git://example.test/docs.git", id="git"),
        pytest.param("file://example.test/docs.git", id="file"),
    ],
)
def test_repo_fetcher_ignores_the_proxy_for_unsupported_repository_schemes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    url: str,
) -> None:
    commands: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        worktree = Path(command[-1])
        worktree.mkdir(parents=True)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", fake_run)

    RepoFetcher().fetch(
        _remote_source(url),
        destination=tmp_path / "staging",
        proxy="http://proxy.example.test:8080",
    )

    assert "-c" not in commands[0]


def test_repo_fetcher_reports_missing_git(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: None)

    with pytest.raises(SourceFetchError) as raised:
        RepoFetcher().fetch(_parsed_source(tmp_path / "source-repository"), destination=tmp_path / "staging")

    assert raised.value.reason_code == "fetch.git_missing"
    assert raised.value.values == {}


def test_repo_fetcher_preserves_clone_failure_detail_and_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        worktree = Path(command[-1])
        worktree.mkdir()
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="permission denied\n")

    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", fake_run)
    source = _parsed_source(tmp_path / "source-repository")

    with pytest.raises(SourceFetchError) as raised:
        RepoFetcher().fetch(source, destination=tmp_path / "staging")

    assert raised.value.reason_code == "fetch.repo_clone_failed_detail"
    assert raised.value.values == {"detail": "permission denied"}
    assert not (tmp_path / ".staging.git").exists()


def test_repo_fetcher_wraps_process_errors_with_the_original_cause(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process_error = OSError("git process unavailable")

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise process_error

    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", fake_run)
    source = _parsed_source(tmp_path / "source-repository")

    with pytest.raises(SourceFetchError) as raised:
        RepoFetcher().fetch(source, destination=tmp_path / "staging")

    assert raised.value.reason_code == "fetch.repo_clone_failed_detail"
    assert raised.value.values == {"detail": "git process unavailable"}
    assert raised.value.__cause__ is process_error


def test_repo_fetcher_sparse_checks_out_the_subpath(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[tuple[list[str], str | None]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        cwd = kwargs.get("cwd")
        commands.append((command, None if cwd is None else str(cwd)))
        if command[1] == "clone":
            worktree = Path(command[-1])
            (worktree / ".git").mkdir(parents=True)
            (worktree / "README.md").write_text("root\n", encoding="utf-8")
            (worktree / "docs").mkdir()
            (worktree / "docs" / "intro.md").write_text("intro\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", fake_run)
    destination = tmp_path / "staging"

    result = RepoFetcher().fetch(
        _parsed_source(tmp_path / "source-repository", subpath="docs"),
        destination=destination,
    )

    worktree = str(tmp_path / ".staging.git")
    assert commands == [
        (
            [
                "/usr/bin/git",
                "clone",
                "--depth=1",
                "--filter=blob:none",
                "--sparse",
                (tmp_path / "source-repository").resolve().as_posix(),
                worktree,
            ],
            None,
        ),
        (["/usr/bin/git", "sparse-checkout", "set", "docs"], worktree),
    ]
    assert (destination / "content" / "intro.md").read_text(encoding="utf-8") == "intro\n"
    assert not (destination / "content" / "README.md").exists()
    assert result.content_kind == "directory"


def _ref_mock(
    commands: list[tuple[list[str], str | None]],
    resolves_locally: bool,
) -> Callable[..., subprocess.CompletedProcess[str]]:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        cwd = kwargs.get("cwd")
        commands.append((command, None if cwd is None else str(cwd)))
        if command[1] == "clone":
            worktree = Path(command[-1])
            (worktree / ".git").mkdir(parents=True)
            (worktree / "README.md").write_text("hello\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        if command[1] == "rev-parse":
            return subprocess.CompletedProcess(command, 0 if resolves_locally else 1, stdout="", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    return fake_run


def test_repo_fetcher_checks_out_a_local_ref_without_fetching(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[tuple[list[str], str | None]] = []
    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", _ref_mock(commands, resolves_locally=True))

    RepoFetcher().fetch(
        _parsed_source(tmp_path / "source-repository", ref="main"),
        destination=tmp_path / "staging",
    )

    worktree = str(tmp_path / ".staging.git")
    assert commands[1] == (
        ["/usr/bin/git", "rev-parse", "--verify", "--quiet", "main^{commit}"],
        worktree,
    )
    assert commands[2] == (["/usr/bin/git", "checkout", "--detach", "main"], worktree)
    assert all(command[1] != "fetch" for command, _ in commands)


def test_repo_fetcher_fetches_a_ref_that_is_not_present(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[tuple[list[str], str | None]] = []
    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", _ref_mock(commands, resolves_locally=False))

    RepoFetcher().fetch(
        _parsed_source(tmp_path / "source-repository", ref="feature"),
        destination=tmp_path / "staging",
    )

    worktree = str(tmp_path / ".staging.git")
    assert commands[2] == (["/usr/bin/git", "fetch", "--depth=1", "origin", "feature"], worktree)
    assert commands[3] == (["/usr/bin/git", "checkout", "--detach", "FETCH_HEAD"], worktree)


def test_repo_fetcher_reports_a_missing_subpath(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if command[1] == "clone":
            worktree = Path(command[-1])
            (worktree / ".git").mkdir(parents=True)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", fake_run)

    with pytest.raises(SourceFetchError) as raised:
        RepoFetcher().fetch(
            _parsed_source(tmp_path / "source-repository", subpath="docs"),
            destination=tmp_path / "staging",
        )

    assert raised.value.reason_code == "fetch.repo_path_missing"
    assert raised.value.values == {"path": "docs"}
    assert not (tmp_path / ".staging.git").exists()


def test_repo_fetcher_reports_a_ref_failure_with_detail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if command[1] == "clone":
            worktree = Path(command[-1])
            (worktree / ".git").mkdir(parents=True)
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="unknown revision\n")

    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", fake_run)

    with pytest.raises(SourceFetchError) as raised:
        RepoFetcher().fetch(
            _parsed_source(tmp_path / "source-repository", ref="nope"),
            destination=tmp_path / "staging",
        )

    assert raised.value.reason_code == "fetch.repo_ref_failed"
    assert raised.value.values == {"ref": "nope", "detail": "unknown revision"}


def test_repo_fetcher_reports_a_timeout_with_the_stage_reason(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if command[1] == "clone":
            worktree = Path(command[-1])
            (worktree / ".git").mkdir(parents=True)
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        if command[1] == "rev-parse":
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="")
        raise subprocess.TimeoutExpired(command, 120.0)

    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", fake_run)

    with pytest.raises(SourceFetchError) as raised:
        RepoFetcher().fetch(
            _parsed_source(tmp_path / "source-repository", ref="feature"),
            destination=tmp_path / "staging",
        )

    assert raised.value.reason_code == "fetch.repo_ref_failed"
    assert raised.value.values == {"ref": "feature", "detail": "the command timed out after 120 seconds"}


def test_repo_fetcher_reports_a_local_ref_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if command[1] == "clone":
            worktree = Path(command[-1])
            (worktree / ".git").mkdir(parents=True)
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        raise subprocess.TimeoutExpired(command, 120.0)

    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", fake_run)

    with pytest.raises(SourceFetchError) as raised:
        RepoFetcher().fetch(
            _parsed_source(tmp_path / "source-repository", ref="main"),
            destination=tmp_path / "staging",
        )

    assert raised.value.reason_code == "fetch.repo_ref_failed"
    assert raised.value.values == {"ref": "main", "detail": "the command timed out after 120 seconds"}


def test_repo_fetcher_falls_back_to_gh_for_github(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if command[0].endswith("gh"):
            worktree = Path(command[4])
            (worktree / ".git").mkdir(parents=True)
            (worktree / "README.md").write_text("gh\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="proxy failure\n")

    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: f"/usr/bin/{command}")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", fake_run)
    destination = tmp_path / "staging"

    RepoFetcher().fetch(
        _remote_source("https://github.com/owner/repo.git"),
        destination=destination,
    )

    assert (destination / "content" / "README.md").read_text(encoding="utf-8") == "gh\n"
    assert "clone" in commands[0]
    assert commands[1][1:5] == [
        "repo",
        "clone",
        "https://github.com/owner/repo.git",
        str(tmp_path / ".staging.git"),
    ]


def test_repo_fetcher_reports_git_and_gh_failures_together(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if command[0].endswith("gh"):
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="gh failure\n")
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="git failure\n")

    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: f"/usr/bin/{command}")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", fake_run)

    with pytest.raises(SourceFetchError) as raised:
        RepoFetcher().fetch(
            _remote_source("https://github.com/owner/repo.git"),
            destination=tmp_path / "staging",
        )

    assert raised.value.reason_code == "fetch.repo_clone_failed_detail"
    assert raised.value.values == {"detail": "git failure; gh failure"}
