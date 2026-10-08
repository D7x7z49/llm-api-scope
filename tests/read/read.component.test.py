# tests/read/read.component.test.py
# ruff: noqa: N999

import json
import shutil
from pathlib import Path
from typing import Any

import httpx2
import pytest
import yaml
from typer.testing import CliRunner

from apiscope.main import app

OPENAPI_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "read" / "openapi" / "openapi.yaml"
READ_FILESYSTEM_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "read" / "filesystem"


def test_read_returns_cached_text_at_a_view_index(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs"
    shutil.copytree(READ_FILESYSTEM_FIXTURE, source)
    runner = CliRunner()

    _register_and_sync(runner, "docs", "docs")
    view = runner.invoke(app, ["--json", "view", "docs"], catch_exceptions=False)
    assert view.exit_code == 0
    view_node = next(item for item in json.loads(view.output)["data"] if item.get("path") == "api/overview.md")
    view_target = view_node["path"]
    result = runner.invoke(app, ["--json", "read", "docs", view_node["index"]], catch_exceptions=False)

    assert result.exit_code == 0
    payload = json.loads(result.output)
    expected_content = "# API overview\n\nThe service exposes a health endpoint.\n"
    assert payload["meta"] == {"name": "docs", "target": view_target}
    assert payload["data"] == [
        {
            "kind": "markdown",
            "content": expected_content,
            "media_type": "text/markdown",
            "encoding": "utf-8",
        }
    ]
    assert payload["extra"] == {
        "cache": "fresh",
        "encoding": "utf-8",
        "kind": "markdown",
        "media_type": "text/markdown",
        "size": len(expected_content.encode("utf-8")),
    }


def test_read_accepts_a_leaf_address_without_an_index(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs"
    shutil.copytree(READ_FILESYSTEM_FIXTURE, source)
    runner = CliRunner()

    _register_and_sync(runner, "docs", "docs")
    result = runner.invoke(app, ["--json", "read", "docs/api/overview.md"], catch_exceptions=False)

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["meta"] == {"name": "docs", "target": "api/overview.md"}
    assert payload["data"][0]["content"].startswith("# API overview")


def test_read_rejects_a_non_leaf_address_without_an_index(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs"
    shutil.copytree(READ_FILESYSTEM_FIXTURE, source)
    runner = CliRunner()

    _register_and_sync(runner, "docs", "docs")
    result = runner.invoke(app, ["--json", "read", "docs/api"], catch_exceptions=False)

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["code"] == "read.error.target_not_leaf"
    assert payload["extra"]["address"] == "docs/api"
    assert payload["extra"]["nodes"] == [{"index": "1", "key": "overview.md", "node_type": "leaf"}]


def test_read_rejects_a_root_address_without_an_index(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs"
    (source / "api").mkdir(parents=True)
    (source / "api" / "overview.md").write_text("overview\n", encoding="utf-8")
    (source / "README.md").write_text("readme\n", encoding="utf-8")
    runner = CliRunner()

    _register_and_sync(runner, "docs", "docs")
    result = runner.invoke(app, ["--json", "read", "docs"], catch_exceptions=False)

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["code"] == "read.error.target_not_leaf"
    assert payload["extra"]["address"] == "docs"


def test_read_accepts_a_single_file_source_without_an_index(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    (project_cwd / "README.md").write_text("readme\n", encoding="utf-8")
    runner = CliRunner()

    _register_and_sync(runner, "readme", "README.md")
    result = runner.invoke(app, ["--json", "read", "readme"], catch_exceptions=False)

    assert result.exit_code == 0
    assert json.loads(result.output)["data"][0]["content"] == "readme\n"


def test_read_prompts_for_routes_when_address_selects_an_openapi_branch(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "openapi.yaml"
    shutil.copyfile(OPENAPI_FIXTURE, source)
    runner = CliRunner()

    _register_and_sync(runner, "pets", "openapi.yaml", doc_type="openapi")
    view = runner.invoke(app, ["--json", "view", "pets"], catch_exceptions=False)
    assert view.exit_code == 0
    view_target = next(item["path"] for item in json.loads(view.output)["data"] if item.get("path") == "pets")
    result = runner.invoke(app, ["--json", "read", "pets/pets"], catch_exceptions=False)

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["code"] == "read.error.target_not_leaf"
    assert payload["meta"] == {}
    assert payload["message"] == f"{view_target} is an ordinary node, not a leaf"
    assert any(item["key"] == "GET" for item in payload["extra"]["nodes"])


def test_read_returns_one_openapi_operation_from_a_view_index(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "openapi.yaml"
    shutil.copyfile(OPENAPI_FIXTURE, source)
    runner = CliRunner()

    _register_and_sync(runner, "pets", "openapi.yaml", doc_type="openapi")
    view = runner.invoke(app, ["--json", "view", "pets/pets"], catch_exceptions=False)
    assert view.exit_code == 0
    view_data = json.loads(view.output)["data"]
    operation_node = next(item for item in view_data if item.get("path") == "pets/GET")
    operation_target = operation_node["path"]
    result = runner.invoke(app, ["--json", "read", "pets/pets", operation_node["index"]], catch_exceptions=False)

    assert result.exit_code == 0
    payload = json.loads(result.output)
    document = yaml.safe_load(OPENAPI_FIXTURE.read_text(encoding="utf-8"))
    expected = {
        "summary": document["paths"]["/pets"]["summary"],
        "parameters": document["paths"]["/pets"]["parameters"],
        "get": document["paths"]["/pets"]["get"],
    }
    assert payload["meta"] == {"name": "pets", "target": operation_target}
    assert yaml.safe_load(payload["data"][0]["content"]) == expected
    assert payload["data"][0]["media_type"] == "application/yaml"

    query_node = next(item for item in view_data if item.get("path") == "pets/QUERY")
    query_result = runner.invoke(app, ["--json", "read", "pets/pets", query_node["index"]], catch_exceptions=False)
    assert query_result.exit_code == 0
    assert yaml.safe_load(json.loads(query_result.output)["data"][0]["content"]) == {
        "summary": "Pet collection",
        "parameters": document["paths"]["/pets"]["parameters"],
        "query": document["paths"]["/pets"]["query"],
    }

    copy_node = next(item for item in view_data if item.get("path") == "pets/COPY")
    copy_result = runner.invoke(app, ["--json", "read", "pets/pets", copy_node["index"]], catch_exceptions=False)
    assert copy_result.exit_code == 0
    copy_payload = json.loads(copy_result.output)
    assert yaml.safe_load(copy_payload["data"][0]["content"]) == {
        "summary": "Pet collection",
        "parameters": document["paths"]["/pets"]["parameters"],
        "additionalOperations": {"COPY": document["paths"]["/pets"]["additionalOperations"]["COPY"]},
    }


def test_read_route_error_uses_the_shared_prefix_hint(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs"
    shutil.copytree(READ_FILESYSTEM_FIXTURE, source)
    runner = CliRunner()

    _register_and_sync(runner, "docs", "docs")
    result = runner.invoke(app, ["--json", "read", "docs/api/missing.md", "1"], catch_exceptions=False)

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["code"] == "view_lib.projection.path_not_found"
    assert payload["meta"] == {}
    assert payload["extra"]["address"] == "docs/api"
    assert payload["extra"]["nodes"] == [{"index": "1", "key": "overview.md", "node_type": "leaf"}]
    assert payload["message"] == "route api/missing.md does not exist"


def test_read_text_output_has_a_head_body_and_foot(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs"
    shutil.copytree(READ_FILESYSTEM_FIXTURE, source)
    runner = CliRunner()

    _register_and_sync(runner, "docs", "docs")
    result = runner.invoke(app, ["read", "docs", "1.1"], catch_exceptions=False)

    expected_content = "# API overview\n\nThe service exposes a health endpoint.\n"
    expected_foot = (
        "[cache=fresh] [kind=markdown] [media_type=text/markdown] "
        f"[encoding=utf-8] [size={len(expected_content.encode('utf-8'))}]"
    )
    assert result.exit_code == 0
    expected_output = (
        "[ok] [scope=project] [action=read] [name=docs] [target=api/overview.md]\n\n"
        "---\n\n"
        f"{expected_content}\n\n---\n\n"
        f"{expected_foot}\n"
    )
    assert result.output == expected_output, repr(result.output)


def test_read_supports_a_single_file_source(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    (project_cwd / "README.md").write_text("readme\n", encoding="utf-8")
    runner = CliRunner()

    _register_and_sync(runner, "readme", "README.md")
    result = runner.invoke(app, ["--json", "read", "readme", "1"], catch_exceptions=False)

    assert result.exit_code == 0
    assert json.loads(result.output)["data"][0]["content"] == "readme\n"


def test_read_index_must_exist_in_the_address_scope(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs"
    (source / "api").mkdir(parents=True)
    (source / "api" / "overview.md").write_text("overview\n", encoding="utf-8")
    (source / "README.md").write_text("readme\n", encoding="utf-8")
    runner = CliRunner()

    _register_and_sync(runner, "docs", "docs")
    outside = runner.invoke(app, ["--json", "read", "docs/api", "2"], catch_exceptions=False)
    parent = runner.invoke(app, ["--json", "read", "docs/api", "1.1"], catch_exceptions=False)

    assert outside.exit_code == 1
    outside_payload = json.loads(outside.output)
    assert outside_payload["code"] == "view_lib.projection.index_not_found"
    assert outside_payload["meta"] == {}
    assert outside_payload["message"] == "tree index 2 does not exist"

    assert parent.exit_code == 1
    assert json.loads(parent.output)["code"] == "view_lib.projection.index_not_found"


def test_read_prompts_for_routes_instead_of_reading_a_directory(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs"
    (source / "api").mkdir(parents=True)
    (source / "api" / "overview.md").write_text("overview\n", encoding="utf-8")
    (source / "README.md").write_text("readme\n", encoding="utf-8")
    runner = CliRunner()

    _register_and_sync(runner, "docs", "docs")
    result = runner.invoke(app, ["--json", "read", "docs", "1"], catch_exceptions=False)

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["code"] == "read.error.target_not_leaf"
    assert payload["extra"]["address"] == "docs"
    assert payload["extra"]["nodes"] == [{"index": "1", "key": "overview.md", "node_type": "leaf"}]
    assert payload["message"] == "api is an ordinary node, not a leaf"


def test_read_reports_missing_cache(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "README.md"
    source.write_text("readme\n", encoding="utf-8")
    runner = CliRunner()
    added = runner.invoke(app, ["add", "docs", "README.md", "--type", "filesystem"], catch_exceptions=False)

    result = runner.invoke(app, ["read", "docs", "1"], catch_exceptions=False)

    assert added.exit_code == 0
    assert result.exit_code == 1
    assert "read.error.cache_missing" in result.output
    assert "sync it before retrying" in result.output


def test_read_uses_the_shared_index_not_found_message(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    (project_cwd / "README.md").write_text("readme\n", encoding="utf-8")
    runner = CliRunner()

    _register_and_sync(runner, "docs", "README.md")
    result = runner.invoke(app, ["--json", "read", "docs", "9"], catch_exceptions=False)

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["code"] == "view_lib.projection.index_not_found"
    assert payload["message"] == "tree index 9 does not exist"


def test_read_reports_a_route_placed_in_the_index_argument(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["read", "docs", "guide/intro.md"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert result.output == (
        "[error] [scope=project] [action=read] [code=read.error.index_form]: "
        "the [index] argument received [guide/intro.md], but it must be a numeric index. "
        "put the route in the address, as in [apiscope read docs/guide/intro.md]\n"
    )


def test_read_returns_one_rfc_txt_page(
    isolated_home: Path,
    project_cwd: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_client = httpx2.Client

    def handle(request: httpx2.Request) -> httpx2.Response:
        if str(request.url).endswith(".xml"):
            return httpx2.Response(404, request=request)
        return httpx2.Response(
            200,
            headers={"content-type": "text/plain; charset=utf-8"},
            content=b"cover\fcontents\fbody page\n",
            request=request,
        )

    def client_factory(**kwargs: Any) -> httpx2.Client:
        return original_client(transport=httpx2.MockTransport(handle), **kwargs)

    monkeypatch.setattr(httpx2, "Client", client_factory)
    runner = CliRunner()

    _register_and_sync(runner, "rfc", "9110", doc_type="rfc")
    page_view = runner.invoke(app, ["--json", "view", "rfc/page"], catch_exceptions=False)
    page_index = next(item["index"] for item in json.loads(page_view.output)["data"] if item["path"] == "page/2")
    result = runner.invoke(app, ["--json", "read", "rfc/page", page_index], catch_exceptions=False)

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["meta"] == {"name": "rfc", "target": "page/2"}
    assert payload["data"][0]["content"] == "contents"
    assert payload["data"][0]["media_type"] == "text/plain"


def test_sync_downloads_llmstxt_pages_and_read_returns_them(
    isolated_home: Path,
    project_cwd: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index = (
        "# Docs\n\n## Guides\n"
        "- [Guide](https://example.test/docs/guide.md): Read this guide.\n"
        "- [API](https://example.test/docs/api.md)\n"
    )
    requested: list[str] = []
    original_client = httpx2.Client

    def handle(request: httpx2.Request) -> httpx2.Response:
        requested.append(str(request.url))
        if str(request.url) == "https://example.test/llms.txt":
            return httpx2.Response(
                200,
                headers={"content-type": "text/plain; charset=utf-8"},
                content=index.encode(),
                request=request,
            )
        return httpx2.Response(
            200,
            headers={"content-type": "text/markdown; charset=utf-8"},
            content=b"# Guide\n",
            request=request,
        )

    def client_factory(**kwargs: Any) -> httpx2.Client:
        return original_client(transport=httpx2.MockTransport(handle), **kwargs)

    monkeypatch.setattr(httpx2, "Client", client_factory)
    runner = CliRunner()

    _register_and_sync(runner, "docs", "https://example.test/llms.txt", doc_type="llmstxt")
    view = runner.invoke(app, ["--json", "view", "docs"], catch_exceptions=False)
    link = next(item for item in json.loads(view.output)["data"] if item.get("key") == "guide.md")
    result = runner.invoke(app, ["--json", "read", "docs", link["index"]], catch_exceptions=False)

    assert result.exit_code == 0
    assert "https://example.test/docs/guide.md" in requested
    payload = json.loads(result.output)
    assert payload["data"][0]["content"] == "# Guide\n"
    assert "retrieval" not in payload["extra"]


def test_sync_skips_a_failed_llmstxt_page(
    isolated_home: Path,
    project_cwd: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index = b"# Docs\n\n## Guides\n- [Guide](https://example.test/docs/guide.md)\n"
    original_client = httpx2.Client

    def handle(request: httpx2.Request) -> httpx2.Response:
        if str(request.url) == "https://example.test/llms.txt":
            return httpx2.Response(
                200,
                headers={"content-type": "text/plain; charset=utf-8"},
                content=index,
                request=request,
            )
        return httpx2.Response(404, request=request)

    def client_factory(**kwargs: Any) -> httpx2.Client:
        return original_client(transport=httpx2.MockTransport(handle), **kwargs)

    monkeypatch.setattr(httpx2, "Client", client_factory)
    runner = CliRunner()

    added = runner.invoke(
        app,
        ["add", "docs", "https://example.test/llms.txt", "--type", "llmstxt"],
        catch_exceptions=False,
    )
    result = runner.invoke(app, ["sync", "all", "docs"], catch_exceptions=False)
    view = runner.invoke(app, ["--json", "view", "docs"], catch_exceptions=False)

    assert added.exit_code == 0
    assert result.exit_code == 0
    assert [item["key"] for item in json.loads(view.output)["data"]] == ["llms.txt"]
    assert "Traceback" not in result.output


def test_read_rejects_a_path_outside_the_cached_tree(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    source = project_cwd / "docs"
    source.mkdir()
    (source / "README.md").write_text("readme\n", encoding="utf-8")
    runner = CliRunner()

    _register_and_sync(runner, "docs", "docs")
    result = runner.invoke(app, ["read", "docs/../secret", "1"], catch_exceptions=False)

    assert result.exit_code == 1
    assert "read.error.target_invalid" in result.output
    assert "Traceback" not in result.output


def test_arxiv_source_can_be_added_synced_viewed_and_read(
    isolated_home: Path,
    project_cwd: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    html = (
        '<html><article class="ltx_document"><section id="S1" class="ltx_section">'
        '<h2 class="ltx_title ltx_title_section">Introduction</h2><p>Paper text.</p>'
        "</section></article></html>"
    )
    requested: list[str] = []
    original_client = httpx2.Client

    def handle(request: httpx2.Request) -> httpx2.Response:
        requested.append(str(request.url))
        return httpx2.Response(200, content=html.encode(), request=request)

    def client_factory(**kwargs: Any) -> httpx2.Client:
        return original_client(transport=httpx2.MockTransport(handle), **kwargs)

    monkeypatch.setattr(httpx2, "Client", client_factory)
    runner = CliRunner()

    added = runner.invoke(app, ["add", "paper", "1706.03762v7", "--type", "arxiv"], catch_exceptions=False)
    listed = runner.invoke(app, ["--json", "list", "arxiv"], catch_exceptions=False)
    synced = runner.invoke(app, ["sync", "arxiv", "paper"], catch_exceptions=False)
    viewed = runner.invoke(app, ["--json", "view", "paper"], catch_exceptions=False)
    read = runner.invoke(app, ["--json", "read", "paper/S1"], catch_exceptions=False)

    assert added.exit_code == 0
    assert listed.exit_code == 0
    assert json.loads(listed.output)["data"][0]["type"] == "arxiv"
    assert synced.exit_code == 0
    assert viewed.exit_code == 0
    assert any(node["path"] == "S1" for node in json.loads(viewed.output)["data"])
    assert read.exit_code == 0
    assert json.loads(read.output)["data"][0]["content"] == (
        '<section id="S1" class="ltx_section">'
        '<h2 class="ltx_title ltx_title_section">Introduction</h2><p>Paper text.</p></section>'
    )
    assert requested == ["https://arxiv.org/html/1706.03762v7"]


def _register_and_sync(
    runner: CliRunner,
    name: str,
    source: str,
    *,
    doc_type: str = "filesystem",
) -> None:
    added = runner.invoke(app, ["add", name, source, "--type", doc_type], catch_exceptions=False)
    synced = runner.invoke(app, ["sync", "all", name], catch_exceptions=False)
    assert added.exit_code == 0
    assert synced.exit_code == 0
