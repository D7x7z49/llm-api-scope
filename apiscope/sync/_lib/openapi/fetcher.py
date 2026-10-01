# apiscope/sync/_lib/openapi/fetcher.py
import shutil
from datetime import datetime, timezone
from pathlib import Path

import httpx

from apiscope.sync._lib.errors import SourceFetchError, TransportError
from apiscope.sync._lib.schema import FetchResult, ParsedSource
from apiscope.sync._lib.transport import fetch_location


class OpenapiFetcher:
    def fetch(
        self,
        source: ParsedSource,
        *,
        destination: Path,
        proxy: str | None = None,
    ) -> FetchResult:
        try:
            content_kind, content_name, digest = fetch_location(source.location, destination=destination, proxy=proxy)
        except TransportError as error:
            raise SourceFetchError(source.original, error.reason_code, error.values) from error
        except (OSError, ValueError, shutil.Error, httpx.HTTPError) as error:
            raise SourceFetchError(source.original, "fetch.transport_failed", {"detail": str(error)}) from error
        return FetchResult(
            fetched_at=datetime.now(timezone.utc),
            content_kind=content_kind,
            content_name=content_name,
            content_digest=digest,
        )
