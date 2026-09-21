# apiscope/sync/_lib/repo/fetcher.py
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from apiscope.sync._lib.cache import digest_content
from apiscope.sync._lib.errors import SourceFetchError
from apiscope.sync._lib.repo.constants import (
    GIT_COMMAND,
    GIT_PROXY_ENVIRONMENT_NAMES,
    GIT_PROXY_SCHEMES,
    GIT_TIMEOUT_SECONDS,
)
from apiscope.sync._lib.schema import FetchResult, LocalSource, ParsedSource, RemoteSource


class RepoFetcher:
    def fetch(
        self,
        source: ParsedSource,
        *,
        destination: Path,
        proxy: str | None = None,
    ) -> FetchResult:
        if not isinstance(source.location, (LocalSource, RemoteSource)):
            raise SourceFetchError(source.original, "fetch.repo_location_invalid")
        git = shutil.which(GIT_COMMAND)
        if git is None:
            raise SourceFetchError(source.original, "fetch.git_missing")

        worktree = destination.parent / f".{destination.name}.git"
        shutil.rmtree(worktree, ignore_errors=True)
        repository = (
            source.location.path.as_posix() if isinstance(source.location, LocalSource) else source.location.url
        )
        content_path = destination / "content"
        content_path.mkdir(parents=True, exist_ok=True)
        try:
            result = subprocess.run(
                [
                    git,
                    *_git_proxy_options(source.original, source.location, proxy),
                    "clone",
                    "--depth=1",
                    "--filter=blob:none",
                    "--sparse",
                    repository,
                    str(worktree),
                ],
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
            _copy_repository(worktree, content_path)
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


def _git_proxy_options(
    original: str,
    location: LocalSource | RemoteSource,
    proxy: str | None,
) -> list[str]:
    if isinstance(location, LocalSource):
        return []

    scheme = urlsplit(location.url).scheme.lower()
    if proxy is not None and scheme not in GIT_PROXY_SCHEMES:
        raise SourceFetchError(
            original,
            "fetch.repo_proxy_unsupported",
            {"scheme": scheme},
        )
    if scheme not in GIT_PROXY_SCHEMES:
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
