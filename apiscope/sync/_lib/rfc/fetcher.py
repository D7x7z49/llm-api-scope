# apiscope/sync/_lib/rfc/fetcher.py
import shutil
from datetime import datetime, timezone
from pathlib import Path

import httpx2

from apiscope.sync._lib.errors import SourceFetchError, TransportError
from apiscope.sync._lib.schema import FetchResult, ParsedSource, RemoteLocation
from apiscope.sync._lib.transport import fetch_location

# the rfc editor serves xml for modern rfc and text for almost every rfc
_XML_SUFFIX = ".xml"
_TEXT_SUFFIX = ".txt"
_NOT_FOUND = 404


class RfcFetcher:
    def fetch(
        self,
        source: ParsedSource,
        *,
        destination: Path,
        proxy: str | None = None,
        no_proxy: str | None = None,
    ) -> FetchResult:
        if not isinstance(source.location, RemoteLocation):
            raise SourceFetchError(source.original, "fetch.transport_failed", {"detail": "the rfc source is remote"})
        urls = _representations(source.location.url)
        for url in urls:
            try:
                content_kind, content_name, digest = fetch_location(
                    RemoteLocation(url=url), destination=destination, proxy=proxy, no_proxy=no_proxy
                )
            except TransportError as error:
                raise SourceFetchError(source.original, error.reason_code, error.values) from error
            except httpx2.HTTPStatusError as error:
                if error.response.status_code == _NOT_FOUND and url != urls[-1]:
                    continue
                raise SourceFetchError(source.original, "fetch.transport_failed", {"detail": str(error)}) from error
            except (OSError, ValueError, shutil.Error, httpx2.HTTPError) as error:
                raise SourceFetchError(source.original, "fetch.transport_failed", {"detail": str(error)}) from error
            return FetchResult(
                fetched_at=datetime.now(timezone.utc),
                content_kind=content_kind,
                content_name=content_name,
                content_digest=digest,
            )
        raise SourceFetchError(
            source.original, "fetch.transport_failed", {"detail": "no rfc representation is available"}
        )


# xml is preferred when present; text is the fallback
def _representations(url: str) -> list[str]:
    if url.endswith(_XML_SUFFIX):
        return [url, f"{url[: -len(_XML_SUFFIX)]}{_TEXT_SUFFIX}"]
    return [url]
