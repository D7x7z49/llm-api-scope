# apiscope/sync/_lib/protocols.py
from pathlib import Path
from typing import Protocol

from apiscope.sync._lib.schema import FetchResult, ParsedSource


class SourceFetcher(Protocol):
    def fetch(
        self,
        source: ParsedSource,
        *,
        destination: Path,
        proxy: str | None = None,
        no_proxy: str | None = None,
    ) -> FetchResult: ...
