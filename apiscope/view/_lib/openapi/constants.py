# apiscope/view/_lib/openapi/constants.py
from typing import Final

# ==============================================================================
# operation order
# ==============================================================================


METHOD_ORDER: Final[tuple[str, ...]] = (
    "get",
    "put",
    "post",
    "delete",
    "options",
    "head",
    "patch",
    "trace",
)
