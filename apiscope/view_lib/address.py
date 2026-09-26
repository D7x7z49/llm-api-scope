# apiscope/view_lib/address.py
from collections.abc import Iterable


def split_address(address: str, source_names: Iterable[str]) -> tuple[str, str]:
    names = tuple(source_names)
    exact = [name for name in names if address == name]
    if exact:
        return max(exact, key=len), "."

    matches = [name for name in names if address.startswith(f"{name}/")]
    if matches:
        source_name = max(matches, key=len)
        route = address[len(source_name) + 1 :]
        return source_name, route or "."

    source_name, separator, route = address.partition("/")
    return source_name, route if separator and route else "."
