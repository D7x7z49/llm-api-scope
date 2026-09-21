# apiscope/sync/_lib/registry.py
from pathlib import Path

from apiscope.sync._lib.filesystem.fetcher import FilesystemFetcher
from apiscope.sync._lib.filesystem.parser import FilesystemParser
from apiscope.sync._lib.llmstxt.fetcher import LlmstxtFetcher
from apiscope.sync._lib.llmstxt.parser import LlmstxtParser
from apiscope.sync._lib.openapi.fetcher import OpenapiFetcher
from apiscope.sync._lib.openapi.parser import OpenapiParser
from apiscope.sync._lib.protocols import SourceFetcher, SourceParser
from apiscope.sync._lib.repo.fetcher import RepoFetcher
from apiscope.sync._lib.repo.parser import RepoParser
from apiscope.sync._lib.rfc.fetcher import RfcFetcher
from apiscope.sync._lib.rfc.parser import RfcParser
from apiscope.sync._lib.schema import DocumentType, FetchResult, ParsedSource

_PARSERS: dict[DocumentType, SourceParser] = {
    "filesystem": FilesystemParser(),
    "repo": RepoParser(),
    "openapi": OpenapiParser(),
    "rfc": RfcParser(),
    "llmstxt": LlmstxtParser(),
}
_FETCHERS: dict[DocumentType, SourceFetcher] = {
    "filesystem": FilesystemFetcher(),
    "repo": RepoFetcher(),
    "openapi": OpenapiFetcher(),
    "rfc": RfcFetcher(),
    "llmstxt": LlmstxtFetcher(),
}


def parse_source(doc_type: DocumentType, source: str, *, base_dir: Path) -> ParsedSource:
    return _PARSERS[doc_type].parse(source, base_dir=base_dir)


def fetch_source(
    source: ParsedSource,
    *,
    destination: Path,
    proxy: str | None = None,
) -> FetchResult:
    return _FETCHERS[source.doc_type].fetch(source, destination=destination, proxy=proxy)
