# apiscope/sync/_lib/rfc/parser.py
from pathlib import Path

from apiscope.sync._lib.errors import SourceLocationError, SourceParseError
from apiscope.sync._lib.location import parse_local_or_remote
from apiscope.sync._lib.rfc.constants import REMOTE_SCHEMES, SOURCE_TYPE
from apiscope.sync._lib.schema import ParsedSource


class RfcParser:
    def parse(self, source: str, *, base_dir: Path) -> ParsedSource:
        try:
            canonical, location = parse_local_or_remote(source, base_dir=base_dir, remote_schemes=REMOTE_SCHEMES)
        except SourceLocationError as error:
            raise SourceParseError(source, error.reason_code, error.values) from error
        except (OSError, RuntimeError, ValueError) as error:
            raise SourceParseError(source, "parse.location_invalid", {"detail": str(error)}) from error
        return ParsedSource(doc_type=SOURCE_TYPE, original=source, canonical=canonical, location=location)
