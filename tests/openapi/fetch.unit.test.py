# tests/openapi/fetch.unit.test.py

from pathlib import Path

import httpx

from apiscope.openapi import fetch as fetch_mod


class _FakeResponse:
    content: bytes = b"{}"

    def raise_for_status(self) -> None:
        pass


def test_fetch_local_copies_to_cache(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    src = tmp_path / "spec.json"
    src.write_text('{"openapi":"3.0"}')

    result = fetch_mod.fetch_openapi_spec(str(src), cache_dir)

    assert result.parent == cache_dir
    assert result.suffix == ".json"
    assert result.read_text() == '{"openapi":"3.0"}'


def test_fetch_remote_downloads_to_cache(monkeypatch, tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    fake = _FakeResponse()
    fake.content = b'{"openapi":"3.1"}'
    monkeypatch.setattr(httpx, "get", lambda url, **kw: fake)

    result = fetch_mod.fetch_openapi_spec("https://api.example.com/openapi.json", cache_dir)

    assert result.parent == cache_dir
    assert result.suffix == ".json"
    assert result.read_text() == '{"openapi":"3.1"}'


def test_fetch_returns_cached_path_on_hit(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    src = tmp_path / "spec.json"
    src.write_text("{}")

    first = fetch_mod.fetch_openapi_spec(str(src), cache_dir)
    src.write_text("changed")  # modify original, cache stays pristine
    second = fetch_mod.fetch_openapi_spec(str(src), cache_dir)

    assert first == second
    assert second.read_text() == "{}"
