# apiscope/sync/_lib/filesystem/fetcher.py
import shutil
from datetime import datetime, timezone
from pathlib import Path

from apiscope.cache import digest_content
from apiscope.sync._lib.errors import SourceFetchError
from apiscope.sync._lib.filesystem.constants import DEFAULT_CONTENT_NAME
from apiscope.sync._lib.schema import ContentKind, FetchResult, LocalLocation, ParsedSource


class FilesystemFetcher:
    def fetch(
        self,
        source: ParsedSource,
        *,
        destination: Path,
        proxy: str | None = None,
    ) -> FetchResult:
        del proxy
        if not isinstance(source.location, LocalLocation):
            raise SourceFetchError(source.original, "fetch.filesystem_local_required")
        path = source.location.path
        content_path = destination / "content"
        content_path.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            raise SourceFetchError(source.original, "fetch.source_path_missing", {"path": str(path)})
        try:
            if path.is_dir():
                _copy_directory(path, content_path)
                content_kind: ContentKind = "directory"
                content_name = None
            else:
                content_name = path.name or DEFAULT_CONTENT_NAME
                shutil.copy2(path, content_path / content_name)
                content_kind = "file"
            digest = digest_content(content_path)
        except (OSError, shutil.Error) as error:
            raise SourceFetchError(source.original, "fetch.filesystem_copy_failed", {"detail": str(error)}) from error
        return FetchResult(
            fetched_at=datetime.now(timezone.utc),
            content_kind=content_kind,
            content_name=content_name,
            content_digest=digest,
        )


def _copy_directory(source: Path, destination: Path) -> None:
    for child in source.iterdir():
        target = destination / child.name
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True)
        else:
            shutil.copy2(child, target)
