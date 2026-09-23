# tests/sync/sync.component.test.py
import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from apiscope.main import app
from apiscope.sync import preflight as sync_preflight
from apiscope.sync._lib.repo import fetcher as repo_fetcher


def _only_cache_entry(isolated_home: Path) -> Path:
    entries = list((isolated_home / ".apiscope" / "cache").iterdir())
    assert len(entries) == 1
    return entries[0]


def test_sync_fetches_a_filesystem_source(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs" / "readme.txt"
    source.parent.mkdir()
    source.write_text("hello\n", encoding="utf-8")
    runner = CliRunner()

    added = runner.invoke(
        app,
        ["add", "docs", "docs/readme.txt", "--type", "filesystem"],
        catch_exceptions=False,
    )
    assert added.exit_code == 0

    result = runner.invoke(app, ["sync", "docs"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "[action=sync]" in result.output
    cache_entry = _only_cache_entry(isolated_home)
    metadata = json.loads((cache_entry / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["doc_type"] == "filesystem"
    assert (cache_entry / "content" / "readme.txt").read_text(encoding="utf-8") == "hello\n"


def test_sync_uses_local_proxy_for_a_remote_source(
    isolated_home: Path,
    project_cwd: Path,
    install_httpx_mock_client: Callable[[Callable[[httpx.Request], httpx.Response]], None],
    httpx_client_options: dict[str, object],
) -> None:
    proxy = "http://proxy.example.test:8080"
    runner = CliRunner()
    added = runner.invoke(
        app,
        ["add", "api", "https://example.test/openapi.json", "--type", "openapi"],
        catch_exceptions=False,
    )
    (project_cwd / ".apiscope" / "local.json").write_text(
        json.dumps(
            {
                "$schema": "./schema/config.local.schema.json",
                "setting": {"proxy": proxy},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, content=b"openapi")

    install_httpx_mock_client(handler)
    result = runner.invoke(app, ["sync", "api"], catch_exceptions=False)

    assert added.exit_code == 0
    assert result.exit_code == 0
    assert httpx_client_options["proxy"] == proxy
    assert httpx_client_options["trust_env"] is False
    assert (isolated_home / ".apiscope" / "cache").is_dir()


def test_sync_checks_git_before_fetching_repository_sources(
    isolated_home: Path,
    project_cwd: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = CliRunner()
    added = runner.invoke(
        app,
        ["add", "docs", "https://example.test/docs.git", "--type", "repo"],
        catch_exceptions=False,
    )
    monkeypatch.setattr(sync_preflight.shutil, "which", lambda command: None)

    result = runner.invoke(app, ["sync", "docs"], catch_exceptions=False)

    cache = isolated_home / ".apiscope" / "cache"
    assert added.exit_code == 0
    assert result.exit_code == 1
    assert "sync.error.preflight.git_missing" in result.output
    assert "cannot sync docs because the Git executable is not available" in result.output
    assert not list(cache.iterdir())


def test_sync_checks_dependencies_before_a_mixed_range(
    isolated_home: Path,
    project_cwd: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = project_cwd / "docs.txt"
    source.write_text("hello\n", encoding="utf-8")
    runner = CliRunner()
    filesystem_added = runner.invoke(
        app,
        ["add", "docs", "docs.txt", "--type", "filesystem"],
        catch_exceptions=False,
    )
    repo_added = runner.invoke(
        app,
        ["add", "repo", "https://example.test/docs.git", "--type", "repo"],
        catch_exceptions=False,
    )
    monkeypatch.setattr(sync_preflight.shutil, "which", lambda command: None)

    result = runner.invoke(app, ["sync"], catch_exceptions=False)

    cache = isolated_home / ".apiscope" / "cache"
    assert filesystem_added.exit_code == 0
    assert repo_added.exit_code == 0
    assert result.exit_code == 1
    assert "sync.error.preflight.git_missing" in result.output
    assert not list(cache.iterdir())


def test_sync_does_not_check_git_for_a_filesystem_source(
    isolated_home: Path,
    project_cwd: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = project_cwd / "docs.txt"
    source.write_text("hello\n", encoding="utf-8")
    runner = CliRunner()
    added = runner.invoke(
        app,
        ["add", "docs", "docs.txt", "--type", "filesystem"],
        catch_exceptions=False,
    )
    monkeypatch.setattr(sync_preflight.shutil, "which", lambda command: None)

    result = runner.invoke(app, ["sync", "docs"], catch_exceptions=False)

    assert added.exit_code == 0
    assert result.exit_code == 0
    assert "[synced=1]" in result.output


def test_sync_reports_an_unsupported_proxy_for_an_ssh_repo(
    isolated_home: Path,
    project_cwd: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proxy = "http://proxy.example.test:8080"
    runner = CliRunner()
    added = runner.invoke(
        app,
        ["add", "docs", "ssh://example.test/docs.git", "--type", "repo"],
        catch_exceptions=False,
    )
    (project_cwd / ".apiscope" / "local.json").write_text(
        json.dumps(
            {
                "$schema": "./schema/config.local.schema.json",
                "setting": {"proxy": proxy},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(repo_fetcher.shutil, "which", lambda command: "/usr/bin/git")

    result = runner.invoke(app, ["sync", "docs"], catch_exceptions=False)

    assert added.exit_code == 0
    assert result.exit_code == 1
    assert "sync.error.fetch.repo_proxy_unsupported" in result.output
    assert "repository scheme ssh" in result.output


def test_sync_default_range_skips_a_fresh_source(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs.txt"
    source.write_text("hello\n", encoding="utf-8")
    runner = CliRunner()
    added = runner.invoke(
        app,
        ["add", "docs", "docs.txt", "--type", "filesystem"],
        catch_exceptions=False,
    )
    first = runner.invoke(app, ["sync"], catch_exceptions=False)
    second = runner.invoke(app, ["sync"], catch_exceptions=False)

    assert added.exit_code == 0
    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "[skipped=1]" in second.output
    assert "[synced=0]" in second.output


def test_sync_default_range_skips_an_expired_source(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs.txt"
    source.write_text("hello\n", encoding="utf-8")
    runner = CliRunner()
    added = runner.invoke(
        app,
        ["add", "docs", "docs.txt", "--type", "filesystem"],
        catch_exceptions=False,
    )
    first = runner.invoke(app, ["sync", "docs"], catch_exceptions=False)
    cache_entry = _only_cache_entry(isolated_home)
    metadata_path = cache_entry / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["fetched_at"] = "2000-01-01T00:00:00Z"
    metadata_path.write_text(json.dumps(metadata) + "\n", encoding="utf-8")

    result = runner.invoke(app, ["sync"], catch_exceptions=False)

    assert added.exit_code == 0
    assert first.exit_code == 0
    assert result.exit_code == 0
    assert "[skipped=1]" in result.output
    assert "[synced=0]" in result.output


def test_sync_force_refreshes_a_fresh_source(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs.txt"
    source.write_text("hello\n", encoding="utf-8")
    runner = CliRunner()
    added = runner.invoke(
        app,
        ["add", "docs", "docs.txt", "--type", "filesystem"],
        catch_exceptions=False,
    )
    first = runner.invoke(app, ["sync", "docs"], catch_exceptions=False)
    result = runner.invoke(app, ["sync", "docs", "--force"], catch_exceptions=False)

    assert added.exit_code == 0
    assert first.exit_code == 0
    assert result.exit_code == 0
    assert "[skipped=0]" in result.output
    assert "[synced=1]" in result.output


def test_failed_force_refresh_keeps_the_previous_cache(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs.txt"
    source.write_text("hello\n", encoding="utf-8")
    runner = CliRunner()
    added = runner.invoke(
        app,
        ["add", "docs", "docs.txt", "--type", "filesystem"],
        catch_exceptions=False,
    )
    first = runner.invoke(app, ["sync", "docs"], catch_exceptions=False)
    source.unlink()
    result = runner.invoke(app, ["sync", "docs", "--force"], catch_exceptions=False)

    cache_entry = _only_cache_entry(isolated_home)
    assert added.exit_code == 0
    assert first.exit_code == 0
    assert result.exit_code == 1
    assert "sync.error.fetch.source_path_missing" in result.output
    assert "does not exist" in result.output
    assert (cache_entry / "content" / "docs.txt").read_text(encoding="utf-8") == "hello\n"


def test_sync_filters_sources_by_type_before_fetching(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs.txt"
    source.write_text("hello\n", encoding="utf-8")
    runner = CliRunner()
    filesystem_added = runner.invoke(
        app,
        ["add", "docs", "docs.txt", "--type", "filesystem"],
        catch_exceptions=False,
    )
    openapi_added = runner.invoke(
        app,
        ["add", "api", "https://example.test/openapi.json", "--type", "openapi"],
        catch_exceptions=False,
    )

    result = runner.invoke(app, ["sync", "--source-type", "filesystem"], catch_exceptions=False)

    assert filesystem_added.exit_code == 0
    assert openapi_added.exit_code == 0
    assert result.exit_code == 0
    assert "[target=type%3Afilesystem]" in result.output
    assert "[synced=1]" in result.output
    assert _only_cache_entry(isolated_home).is_dir()


def test_sync_reports_a_partial_failure_after_syncing_valid_sources(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    valid = project_cwd / "valid.txt"
    valid.write_text("hello\n", encoding="utf-8")
    runner = CliRunner()
    valid_added = runner.invoke(
        app,
        ["add", "valid", "valid.txt", "--type", "filesystem"],
        catch_exceptions=False,
    )
    missing_added = runner.invoke(
        app,
        ["add", "missing", "missing.txt", "--type", "filesystem"],
        catch_exceptions=False,
    )

    result = runner.invoke(app, ["sync"], catch_exceptions=False)

    assert valid_added.exit_code == 0
    assert missing_added.exit_code == 0
    assert result.exit_code == 1
    assert "sync.error.partial_failed" in result.output
    assert "[failed=1]" in result.output
    assert "[total=2]" in result.output
    assert (isolated_home / ".apiscope" / "cache").is_dir()
    assert len(list((isolated_home / ".apiscope" / "cache").iterdir())) == 1


def test_sync_reports_a_missing_name(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    result = CliRunner().invoke(app, ["sync", "missing"], catch_exceptions=False)

    assert result.exit_code == 1
    assert "sync.error.name_not_found" in result.output
    assert "source missing does not exist" in result.output


def test_sync_rejects_a_name_with_a_range_option(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    result = CliRunner().invoke(
        app,
        ["sync", "docs", "--source-type", "filesystem"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert "sync.error.range_conflict" in result.output


def test_sync_reports_a_malformed_port_with_a_namespaced_source_error(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    runner = CliRunner()
    added = runner.invoke(
        app,
        ["add", "api", "https://example.test:invalid/openapi.json", "--type", "openapi"],
        catch_exceptions=False,
    )

    result = runner.invoke(app, ["sync", "api"], catch_exceptions=False)

    assert added.exit_code == 0
    assert result.exit_code == 1
    assert "sync.error.source.parse.location_invalid" in result.output
    assert "cannot parse source" in result.output
    assert "Traceback" not in result.output
