# apiscope/sync/_lib/registry.py
from pathlib import Path

from apiscope.schema import DocumentType
from apiscope.source import SourceResolutionError
from apiscope.source import parse_source as resolve_source
from apiscope.sync._lib.errors import SourceParseError
from apiscope.sync._lib.filesystem.fetcher import FilesystemFetcher
from apiscope.sync._lib.llmstxt.fetcher import LlmstxtFetcher
from apiscope.sync._lib.openapi.fetcher import OpenapiFetcher
from apiscope.sync._lib.protocols import SourceFetcher
from apiscope.sync._lib.repo.fetcher import RepoFetcher
from apiscope.sync._lib.rfc.fetcher import RfcFetcher
from apiscope.sync._lib.schema import FetchResult, ParsedSource

_FETCHERS: dict[DocumentType, SourceFetcher] = {
    "filesystem": FilesystemFetcher(),
    "repo": RepoFetcher(),
    "openapi": OpenapiFetcher(),
    "rfc": RfcFetcher(),
    "llmstxt": LlmstxtFetcher(),
}


def parse_source(doc_type: DocumentType, source: str, *, base_dir: Path) -> ParsedSource:
    try:
        return resolve_source(doc_type, source, base_dir=base_dir)
    except SourceResolutionError as error:
        raise SourceParseError(source, error.reason_code, error.values) from error


def fetch_source(
    source: ParsedSource,
    *,
    destination: Path,
    proxy: str | None = None,
    no_proxy: str | None = None,
) -> FetchResult:
    return _FETCHERS[source.doc_type].fetch(source, destination=destination, proxy=proxy, no_proxy=no_proxy)
