# tests/view_lib/address.unit.test.py
from apiscope.view_lib.address import split_address


def test_split_address_keeps_the_complete_route_suffix() -> None:
    assert split_address("docs/api/v1", ["docs"]) == ("docs", "api/v1")


def test_split_address_uses_the_longest_registered_source_name() -> None:
    assert split_address("team/docs/api", ["team", "team/docs"]) == ("team/docs", "api")


def test_source_only_address_selects_the_tree_root() -> None:
    assert split_address("docs", ["docs"]) == ("docs", ".")


def test_address_preserves_a_leading_route_slash() -> None:
    assert split_address("pets//pets/GET", ["pets"]) == ("pets", "/pets/GET")
