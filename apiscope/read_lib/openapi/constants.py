# apiscope/read_lib/openapi/constants.py
from typing import Final

STANDARD_METHODS: Final[frozenset[str]] = frozenset(
    {
        "get",
        "put",
        "post",
        "delete",
        "options",
        "head",
        "patch",
        "trace",
        "query",
    }
)
