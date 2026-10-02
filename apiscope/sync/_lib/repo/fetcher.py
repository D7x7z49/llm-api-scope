# apiscope/sync/_lib/repo/fetcher.py
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from apiscope.cache import digest_content
from apiscope.source import RepoSource
from apiscope.sync._lib.errors import SourceFetchError
from apiscope.sync._lib.repo.constants import (
    GIT_COMMAND,
    GIT_PROXY_ENVIRONMENT_NAMES,
    GIT_PROXY_SCHEMES,
    GIT_TIMEOUT_SECONDS,
)
from apiscope.sync._lib.schema import FetchResult, LocalLocation, ParsedSource, RemoteLocation


class RepoFetcher:
    def fetch(
        self,
        source: ParsedSource,
        *,
        destination: Path,
        proxy: str | None = None,
    ) -> FetchResult:
        if not isinstance(source, RepoSource):
            raise SourceFetchError(source.original, "fetch.repo_location_invalid")
        git = shutil.which(GIT_COMMAND)
        if git is None:
            raise SourceFetchError(source.original, "fetch.git_missing")

        worktree = destination.parent / f".{destination.name}.git"
        shutil.rmtree(worktree, ignore_errors=True)
        repository = (
            source.location.path.as_posix() if isinstance(source.location, LocalLocation) else source.location.url
        )
        content_path = destination / "content"
        content_path.mkdir(parents=True, exist_ok=True)
        try:
            proxy_options = _git_proxy_options(source.original, source.location, proxy)
            self._clone(git, source, repository, worktree, proxy_options)
            self._checkout_ref(git, source, worktree, proxy_options)
            self._select_subpath(git, source, worktree)
            _copy_repository(_source_root(source, worktree), content_path)
            digest = digest_content(content_path)
        except (OSError, shutil.Error, subprocess.TimeoutExpired) as error:
            raise SourceFetchError(source.original, "fetch.repo_clone_failed", {"detail": str(error)}) from error
        finally:
            shutil.rmtree(worktree, ignore_errors=True)
        return FetchResult(
            fetched_at=datetime.now(timezone.utc),
            content_kind="directory",
            content_name=None,
            content_digest=digest,
        )

    def _clone(
        self,
        git: str,
        source: RepoSource,
        repository: str,
        worktree: Path,
        proxy_options: list[str],
    ) -> None:
        args = [*proxy_options, "clone", "--depth=1"]
        if source.subpath is not None:
            args.extend(["--filter=blob:none", "--sparse"])
        args.extend([repository, str(worktree)])
        result = subprocess.run(
            [git, *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
            env=_git_environment(),
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip()
            if detail:
                raise SourceFetchError(source.original, "fetch.repo_clone_failed_detail", {"detail": detail})
            raise SourceFetchError(source.original, "fetch.repo_clone_failed")

    def _checkout_ref(
        self,
        git: str,
        source: RepoSource,
        worktree: Path,
        proxy_options: list[str],
    ) -> None:
        if source.ref is None:
            return
        values = {"ref": source.ref}
        # a branch, tag, or commit that the clone already holds needs no fetch
        if _has_local_ref(git, source.ref, worktree):
            _run_git(
                git,
                ["checkout", "--detach", source.ref],
                cwd=worktree,
                source=source.original,
                reason="fetch.repo_ref_failed",
                values=values,
            )
            return
        _run_git(
            git,
            [*proxy_options, "fetch", "--depth=1", "origin", source.ref],
            cwd=worktree,
            source=source.original,
            reason="fetch.repo_ref_failed",
            values=values,
        )
        _run_git(
            git,
            ["checkout", "--detach", "FETCH_HEAD"],
            cwd=worktree,
            source=source.original,
            reason="fetch.repo_ref_failed",
            values=values,
        )

    def _select_subpath(self, git: str, source: RepoSource, worktree: Path) -> None:
        if source.subpath is None:
            return
        _run_git(
            git,
            ["sparse-checkout", "set", source.subpath],
            cwd=worktree,
            source=source.original,
            reason="fetch.repo_path_failed",
            values={"path": source.subpath},
        )


def _run_git(
    git: str,
    args: list[str],
    *,
    cwd: Path,
    source: str,
    reason: str,
    values: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [git, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT_SECONDS,
        env=_git_environment(),
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SourceFetchError(source, reason, {**values, "detail": detail})
    return result


def _source_root(source: RepoSource, worktree: Path) -> Path:
    if source.subpath is None:
        return worktree
    root = worktree / source.subpath
    if not root.is_dir():
        raise SourceFetchError(source.original, "fetch.repo_path_missing", {"path": source.subpath})
    return root


def _has_local_ref(git: str, ref: str, worktree: Path) -> bool:
    result = subprocess.run(
        [git, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT_SECONDS,
        env=_git_environment(),
    )
    return result.returncode == 0


def _git_proxy_options(
    original: str,
    location: LocalLocation | RemoteLocation,
    proxy: str | None,
) -> list[str]:
    if isinstance(location, LocalLocation):
        return []

    scheme = urlsplit(location.url).scheme.lower()
    if scheme not in GIT_PROXY_SCHEMES:
        # a scp-style location has no scheme and never uses an HTTP proxy
        if proxy is not None and scheme:
            raise SourceFetchError(
                original,
                "fetch.repo_proxy_unsupported",
                {"scheme": scheme},
            )
        return []

    value = "" if proxy is None else proxy
    return ["-c", f"http.proxy={value}", "-c", f"https.proxy={value}"]


def _git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in GIT_PROXY_ENVIRONMENT_NAMES:
        environment.pop(name, None)
    return environment


def _copy_repository(source: Path, destination: Path) -> None:
    for child in source.iterdir():
        if child.name == ".git":
            continue
        target = destination / child.name
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True)
        else:
            shutil.copy2(child, target)
