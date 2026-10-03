# apiscope/sync/_lib/repo/fetcher.py
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from apiscope.cache import digest_content
from apiscope.source import LocalLocation, RemoteLocation, RepoSource
from apiscope.sync._lib.errors import SourceFetchError
from apiscope.sync._lib.repo.constants import (
    GH_COMMAND,
    GIT_COMMAND,
    GIT_PROXY_SCHEMES,
    GIT_TIMEOUT_SECONDS,
)
from apiscope.sync._lib.schema import FetchResult, ParsedSource

_GITHUB_HOSTS: frozenset[str] = frozenset({"github.com", "www.github.com"})


class RepoFetcher:
    def fetch(
        self,
        source: ParsedSource,
        *,
        destination: Path,
        proxy: str | None = None,
        no_proxy: str | None = None,
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
            proxy_options = _git_proxy_options(source.location, proxy)
            self._clone(git, source, repository, worktree, proxy_options, proxy, no_proxy)
            self._checkout_ref(git, source, worktree, proxy_options, no_proxy)
            self._select_subpath(git, source, worktree, proxy_options, no_proxy)
            _copy_repository(_source_root(source, worktree), content_path)
            digest = digest_content(content_path)
        except (OSError, shutil.Error) as error:
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
        proxy: str | None,
        no_proxy: str | None,
    ) -> None:
        args = [*proxy_options, "clone", "--depth=1"]
        if source.subpath is not None:
            args.extend(["--filter=blob:none", "--sparse"])
        args.extend([repository, str(worktree)])
        result = _run_command(
            [git, *args],
            cwd=None,
            source=source.original,
            reason="fetch.repo_clone_failed_detail",
            values={},
            no_proxy=no_proxy,
        )
        if result.returncode == 0:
            return

        detail = result.stderr.strip() or result.stdout.strip()
        github = _github_repository(source.location)
        gh = shutil.which(GH_COMMAND) if github is not None else None
        if gh is None or github is None:
            raise _clone_failure(source.original, detail)

        # a failed clone can leave a partial worktree, so clear it before the fallback
        shutil.rmtree(worktree, ignore_errors=True)
        gh_result = _run_gh_clone(gh, source, github, worktree, proxy, no_proxy)
        if gh_result.returncode == 0:
            return
        gh_detail = gh_result.stderr.strip() or gh_result.stdout.strip()
        raise SourceFetchError(
            source.original,
            "fetch.repo_clone_failed_detail",
            {"detail": _join_details(detail, gh_detail)},
        )

    def _checkout_ref(
        self,
        git: str,
        source: RepoSource,
        worktree: Path,
        proxy_options: list[str],
        no_proxy: str | None,
    ) -> None:
        if source.ref is None:
            return
        values = {"ref": source.ref}
        # a branch, tag, or commit that the clone already holds needs no fetch
        if _has_local_ref(git, source.ref, worktree, source=source.original, values=values, no_proxy=no_proxy):
            _run_git(
                git,
                ["checkout", "--detach", source.ref],
                cwd=worktree,
                source=source.original,
                reason="fetch.repo_ref_failed",
                values=values,
                no_proxy=no_proxy,
            )
            return
        _run_git(
            git,
            [*proxy_options, "fetch", "--depth=1", "origin", source.ref],
            cwd=worktree,
            source=source.original,
            reason="fetch.repo_ref_failed",
            values=values,
            no_proxy=no_proxy,
        )
        _run_git(
            git,
            ["checkout", "--detach", "FETCH_HEAD"],
            cwd=worktree,
            source=source.original,
            reason="fetch.repo_ref_failed",
            values=values,
            no_proxy=no_proxy,
        )

    def _select_subpath(
        self,
        git: str,
        source: RepoSource,
        worktree: Path,
        proxy_options: list[str],
        no_proxy: str | None,
    ) -> None:
        if source.subpath is None:
            return
        _run_git(
            git,
            [*proxy_options, "sparse-checkout", "set", source.subpath],
            cwd=worktree,
            source=source.original,
            reason="fetch.repo_path_failed",
            values={"path": source.subpath},
            no_proxy=no_proxy,
        )


def _run_gh_clone(
    gh: str,
    source: RepoSource,
    repository: str,
    worktree: Path,
    proxy: str | None,
    no_proxy: str | None,
) -> subprocess.CompletedProcess[str]:
    args = [gh, "repo", "clone", repository, str(worktree), "--", "--depth=1"]
    if source.subpath is not None:
        args.extend(["--filter=blob:none", "--sparse"])
    return _run_command(
        args,
        cwd=None,
        source=source.original,
        reason="fetch.repo_clone_failed_detail",
        values={},
        env=_gh_environment(proxy, no_proxy),
    )


def _run_git(
    git: str,
    args: list[str],
    *,
    cwd: Path,
    source: str,
    reason: str,
    values: dict[str, str],
    no_proxy: str | None = None,
) -> subprocess.CompletedProcess[str]:
    result = _run_command([git, *args], cwd=cwd, source=source, reason=reason, values=values, no_proxy=no_proxy)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SourceFetchError(source, reason, {**values, "detail": detail})
    return result


# run one external command; a timeout or a start failure keeps the caller reason
def _run_command(
    command: list[str],
    *,
    cwd: Path | None,
    source: str,
    reason: str,
    values: dict[str, str],
    env: dict[str, str] | None = None,
    no_proxy: str | None = None,
) -> subprocess.CompletedProcess[str]:
    effective_env = _git_environment(no_proxy) if env is None else env
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
            env=effective_env,
        )
    except subprocess.TimeoutExpired as error:
        detail = f"the command timed out after {GIT_TIMEOUT_SECONDS:g} seconds"
        raise SourceFetchError(source, reason, {**values, "detail": detail}) from error
    except OSError as error:
        raise SourceFetchError(source, reason, {**values, "detail": str(error)}) from error


def _clone_failure(source: str, detail: str) -> SourceFetchError:
    if detail:
        return SourceFetchError(source, "fetch.repo_clone_failed_detail", {"detail": detail})
    return SourceFetchError(source, "fetch.repo_clone_failed")


def _join_details(*parts: str) -> str:
    return "; ".join(part for part in parts if part) or "git and gh both failed"


def _github_repository(location: LocalLocation | RemoteLocation) -> str | None:
    if isinstance(location, LocalLocation):
        return None
    url = location.url
    if url.startswith("git@github.com:"):
        return url
    try:
        parsed = urlsplit(url)
    except ValueError:
        return None
    if parsed.hostname is not None and parsed.hostname.lower() in _GITHUB_HOSTS:
        return url
    return None


def _source_root(source: RepoSource, worktree: Path) -> Path:
    if source.subpath is None:
        return worktree
    root = worktree / source.subpath
    if not root.is_dir():
        raise SourceFetchError(source.original, "fetch.repo_path_missing", {"path": source.subpath})
    return root


def _has_local_ref(
    git: str,
    ref: str,
    worktree: Path,
    *,
    source: str,
    values: dict[str, str],
    no_proxy: str | None = None,
) -> bool:
    result = _run_command(
        [git, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=worktree,
        source=source,
        reason="fetch.repo_ref_failed",
        values=values,
        no_proxy=no_proxy,
    )
    return result.returncode == 0


# a configured proxy overrides the environment; without one the git process is untouched
def _git_proxy_options(
    location: LocalLocation | RemoteLocation,
    proxy: str | None,
) -> list[str]:
    if isinstance(location, LocalLocation) or not proxy:
        return []

    scheme = urlsplit(location.url).scheme.lower()
    if scheme not in GIT_PROXY_SCHEMES:
        # an HTTP proxy does not apply to scp, ssh, git, or file locations
        return []

    return ["-c", f"http.proxy={proxy}", "-c", f"https.proxy={proxy}"]


# the git process inherits the environment; configuration only adds a bypass list
def _git_environment(no_proxy: str | None) -> dict[str, str] | None:
    if not no_proxy:
        return None
    environment = os.environ.copy()
    environment["NO_PROXY"] = no_proxy
    environment["no_proxy"] = no_proxy
    return environment


# gh uses its own transport; configuration overrides the proxy when one is set
def _gh_environment(proxy: str | None, no_proxy: str | None) -> dict[str, str] | None:
    if not proxy and not no_proxy:
        return None
    environment = os.environ.copy()
    if proxy:
        environment["HTTPS_PROXY"] = proxy
        environment["HTTP_PROXY"] = proxy
    if no_proxy:
        environment["NO_PROXY"] = no_proxy
        environment["no_proxy"] = no_proxy
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
