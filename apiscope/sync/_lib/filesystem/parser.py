# apiscope/sync/_lib/filesystem/parser.py
from pathlib import Path
from urllib.parse import urlsplit

from apiscope.sync._lib.errors import SourceParseError
from apiscope.sync._lib.filesystem.constants import SOURCE_TYPE
from apiscope.sync._lib.schema import LocalSource, ParsedSource


class FilesystemParser:
    def parse(self, source: str, *, base_dir: Path) -> ParsedSource:
        value = source.strip()
        if not value:
            raise SourceParseError(source, "parse.source_empty")
        try:
            is_remote = bool(urlsplit(value).scheme)
        except ValueError as error:
            raise SourceParseError(source, "parse.filesystem_path_invalid", {"detail": str(error)}) from error
        if is_remote:
            raise SourceParseError(source, "parse.filesystem_path_required")

        try:
            path = Path(value).expanduser()
            if not path.is_absolute():
                path = base_dir / path
            resolved = path.resolve(strict=False)
        except (OSError, RuntimeError, ValueError) as error:
            raise SourceParseError(source, "parse.filesystem_path_invalid", {"detail": str(error)}) from error
        return ParsedSource(
            doc_type=SOURCE_TYPE,
            original=source,
            canonical=resolved.as_posix(),
            location=LocalSource(path=resolved),
        )
