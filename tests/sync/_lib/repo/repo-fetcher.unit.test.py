# tests/sync/_lib/repo/repo-fetcher.unit.test.py
import subprocess
from pathlib import Path

import pytest

from apiscope.sync._lib.errors import SourceFetchError
from apiscope.sync._lib.repo import fetcher as repo_fetcher
from apiscope.sync._lib.repo.constants import GIT_PROXY_ENVIRONMENT_NAMES
from apiscope.sync._lib.repo.fetcher import RepoFetcher
from apiscope.sync._lib.schema import LocalSource, ParsedSource, RemoteSource


def _parsed_source(path: Path) -> ParsedSource:
    return ParsedSource(
        doc_type="repo",
        original=str(path),
        canonical=path.resolve().as_posix(),
        location=LocalSource(path.resolve()),
    )


def _remote_source(url: str) -> ParsedSource:
    return ParsedSource(
        doc_type="repo",
        original=url,
        canonical=url,
        location=RemoteSource(url),
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
            "--filter=blob:none",
            "--sparse",
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


def test_repo_fetcher_passes_an_http_proxy_without_proxy_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[list[str]] = []
    environments: list[dict[str, str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        environment = kwargs["env"]
        assert isinstance(environment, dict)
        environments.append(environment)
        worktree = Path(command[-1])
        (worktree / "README.md").parent.mkdir(parents=True)
        (worktree / "README.md").write_text("hello\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    for name in GIT_PROXY_ENVIRONMENT_NAMES:
        monkeypatch.setenv(name, f"{name}-from-environment")
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
    assert all(name not in environments[0] for name in GIT_PROXY_ENVIRONMENT_NAMES)


def test_repo_fetcher_disables_proxy_environment_without_configured_proxy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[list[str]] = []
    environments: list[dict[str, str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        environment = kwargs["env"]
        assert isinstance(environment, dict)
        environments.append(environment)
        worktree = Path(command[-1])
        worktree.mkdir(parents=True)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    for name in GIT_PROXY_ENVIRONMENT_NAMES:
        monkeypatch.setenv(name, f"{name}-from-environment")
    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")
    monkeypatch.setattr(repo_fetcher.subprocess, "run", fake_run)

    RepoFetcher().fetch(
        _remote_source("https://example.test/docs.git"),
        destination=tmp_path / "staging",
    )

    assert commands[0][1:6] == ["-c", "http.proxy=", "-c", "https.proxy=", "clone"]
    assert all(name not in environments[0] for name in GIT_PROXY_ENVIRONMENT_NAMES)


@pytest.mark.parametrize(
    ("url", "scheme"),
    [
        pytest.param("ssh://git@example.test/docs.git", "ssh", id="ssh"),
        pytest.param("git://example.test/docs.git", "git", id="git"),
    ],
)
def test_repo_fetcher_rejects_proxy_for_unsupported_repository_schemes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    url: str,
    scheme: str,
) -> None:
    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")

    with pytest.raises(SourceFetchError) as raised:
        RepoFetcher().fetch(
            _remote_source(url),
            destination=tmp_path / "staging",
            proxy="http://proxy.example.test:8080",
        )

    assert raised.value.reason_code == "fetch.repo_proxy_unsupported"
    assert raised.value.values == {"scheme": scheme}


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

    assert raised.value.reason_code == "fetch.repo_clone_failed"
    assert raised.value.values == {"detail": "git process unavailable"}
    assert raised.value.__cause__ is process_error
