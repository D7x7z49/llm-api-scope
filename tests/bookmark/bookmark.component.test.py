# tests/bookmark/bookmark.component.test.py
import json
import shutil
from collections.abc import Callable
from pathlib import Path

from typer.testing import CliRunner

from apiscope.lock import acquire_write_lock
from apiscope.main import app

DESCRIPTION = "a bookmark used by the component test"


def _write(tmp_path: Path, name: str, text: str) -> Path:
    target = tmp_path / name
    target.write_text(text, encoding="utf-8")
    return target


def _add_file(runner: CliRunner, bookmark_id: str, target: Path, *extra: str):
    return runner.invoke(
        app,
        ["bookmark", "add", bookmark_id, "file", str(target), "--description", DESCRIPTION, *extra],
    )


def _add_group(runner: CliRunner, bookmark_id: str, members: list[str]):
    arguments = ["bookmark", "add", bookmark_id, "group", *members]
    arguments += ["--description", DESCRIPTION]
    return runner.invoke(app, arguments)


def test_add_stores_a_file_bookmark_and_list_shows_it_active(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello\n")
    runner = CliRunner()

    added = _add_file(runner, "my-note", target)
    listed = runner.invoke(app, ["bookmark", "list"])

    assert added.exit_code == 0
    assert "[id=my-note]" in added.output
    assert listed.exit_code == 0
    assert "- [my-note] file" in listed.output
    assert "(active)" in listed.output


def test_add_rejects_a_short_description_with_an_actionable_message(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello\n")
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["bookmark", "add", "demo-short", "file", str(target), "--description", "short"],
    )

    assert result.exit_code == 1
    assert result.output == (
        "[error] [scope=project] [action=add] [code=bookmark.add.error.invalid_options]: "
        "the bookmark options are invalid, [--description] must be at least 32 characters, "
        "but 5 characters were given\n"
    )


def test_list_marks_a_changed_file_as_invalid(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello\n")
    runner = CliRunner()
    _add_file(runner, "my-note", target)

    target.write_text("changed\n", encoding="utf-8")
    listed = runner.invoke(app, ["bookmark", "list"])

    assert listed.exit_code == 0
    assert "(invalid)" in listed.output


def test_add_rejects_a_duplicate_id(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello\n")
    runner = CliRunner()
    _add_file(runner, "my-note", target)

    again = _add_file(runner, "my-note", target)

    assert again.exit_code == 1
    assert "already exists" in again.output


def test_add_force_replaces_an_existing_id(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello\n")
    runner = CliRunner()
    _add_file(runner, "my-note", target)

    forced = _add_file(runner, "my-note", target, "--force")

    assert forced.exit_code == 0


def test_remove_marks_the_entry_as_removed(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello\n")
    runner = CliRunner()
    _add_file(runner, "my-note", target)

    removed = runner.invoke(app, ["bookmark", "remove", "my-note"])
    listed = runner.invoke(app, ["bookmark", "list"])

    assert removed.exit_code == 0
    assert listed.exit_code == 0
    assert "(removed)" in listed.output


def test_use_prints_the_file_content(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello world\n")
    runner = CliRunner()
    _add_file(runner, "my-note", target)

    used = runner.invoke(app, ["bookmark", "use", "my-note"])

    assert used.exit_code == 0
    assert "hello world" in used.output


def test_use_honors_a_file_line_range(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "one\ntwo\nthree\nfour\n")
    runner = CliRunner()
    _add_file(runner, "my-note", target, "--start", "1", "--offset", "2")

    used = runner.invoke(app, ["bookmark", "use", "my-note"])

    assert used.exit_code == 0
    assert "two" in used.output
    assert "three" in used.output
    assert "one" not in used.output
    assert "four" not in used.output


def test_use_rejects_a_removed_entry(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello\n")
    runner = CliRunner()
    _add_file(runner, "my-note", target)
    runner.invoke(app, ["bookmark", "remove", "my-note"])

    used = runner.invoke(app, ["bookmark", "use", "my-note"])

    assert used.exit_code == 1
    assert "removed" in used.output


def test_add_reports_a_held_lock(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello\n")
    held = acquire_write_lock(isolated_home / ".apiscope")
    try:
        result = _add_file(CliRunner(), "my-note", target)
    finally:
        held.release()

    assert result.exit_code == 1
    assert "root.error.write_lock.busy" in result.output


def test_list_does_not_take_the_write_lock(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    held = acquire_write_lock(isolated_home / ".apiscope")
    try:
        result = CliRunner().invoke(app, ["bookmark", "list"])
    finally:
        held.release()

    assert result.exit_code == 0


def test_add_writes_the_project_layer_and_global_flag_writes_home(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello\n")
    runner = CliRunner()

    local = _add_file(runner, "local-note", target)

    assert local.exit_code == 0
    assert (project_cwd / ".apiscope" / "bookmarks.json").is_file()
    assert not (isolated_home / ".apiscope" / "bookmarks.json").exists()

    global_add = runner.invoke(
        app,
        ["--global", "bookmark", "add", "home-note", "file", str(target), "--description", DESCRIPTION],
    )
    assert global_add.exit_code == 0
    assert (isolated_home / ".apiscope" / "bookmarks.json").is_file()


def test_group_lists_its_members(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    members = [f"note-{index}" for index in range(1, 6)]
    for member in members:
        _add_file(runner, member, _write(tmp_path, f"{member}.md", "hello\n"))

    added = _add_group(runner, "my-group", members)
    listed = runner.invoke(app, ["bookmark", "list", "my-group"])
    used = runner.invoke(app, ["bookmark", "use", "my-group"])

    assert added.exit_code == 0
    assert listed.exit_code == 0
    assert used.exit_code == 0
    for member in members:
        assert member in listed.output
        assert member in used.output


def test_group_without_five_members_is_rejected(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    members = ["note-1", "note-2"]
    for member in members:
        _add_file(runner, member, _write(tmp_path, f"{member}.md", "hello\n"))

    added = _add_group(runner, "my-group", members)

    assert added.exit_code == 1
    assert "five to nine" in added.output


def test_group_is_invalid_when_no_member_is_active(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    members = [f"note-{index}" for index in range(1, 6)]
    for member in members:
        _add_file(runner, member, _write(tmp_path, f"{member}.md", "hello\n"))
    _add_group(runner, "my-group", members)
    for member in members:
        runner.invoke(app, ["bookmark", "remove", member])

    listed = runner.invoke(app, ["bookmark", "list"])

    assert listed.exit_code == 0
    assert "[my-group] group" in listed.output
    assert "(invalid)" in listed.output


def test_prune_deletes_removed_and_isolated_entries(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    _add_file(runner, "my-note", _write(tmp_path, "note.md", "hello\n"))
    runner.invoke(app, ["bookmark", "remove", "my-note"])

    pruned = runner.invoke(app, ["bookmark", "prune"])
    listed = runner.invoke(app, ["bookmark", "list"])

    assert pruned.exit_code == 0
    assert "[pruned=1]" in pruned.output
    assert "my-note" not in listed.output


def test_prune_keeps_a_removed_entry_that_a_group_references(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    members = [f"note-{index}" for index in range(1, 6)]
    for member in members:
        _add_file(runner, member, _write(tmp_path, f"{member}.md", "hello\n"))
    _add_group(runner, "my-group", members)
    runner.invoke(app, ["bookmark", "remove", "note-1"])

    runner.invoke(app, ["bookmark", "prune"])
    listed = runner.invoke(app, ["bookmark", "list"])

    assert "note-1" in listed.output


def _add_source_bookmark(runner: CliRunner, bookmark_id: str, mode: str, address: str):
    return runner.invoke(
        app,
        ["bookmark", "add", bookmark_id, mode, address, "--description", DESCRIPTION],
    )


def _synced_directory_source(project_cwd: Path, fixture_tree: Callable[[str, Path], Path]) -> None:
    fixture_tree("filesystem", project_cwd / "docs")
    runner = CliRunner()
    added = runner.invoke(app, ["add", "docs", "docs", "--type", "filesystem"])
    synced = runner.invoke(app, ["sync", "all", "docs"])
    assert added.exit_code == 0
    assert synced.exit_code == 0


def _synced_filesystem_source(project_cwd: Path) -> None:
    source = project_cwd / "docs" / "readme.txt"
    source.parent.mkdir()
    source.write_text("hello\n", encoding="utf-8")
    runner = CliRunner()
    runner.invoke(app, ["add", "docs", "docs/readme.txt", "--type", "filesystem"])
    runner.invoke(app, ["sync", "all", "docs"])


def test_use_runs_a_view_bookmark(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    _synced_filesystem_source(project_cwd)
    runner = CliRunner()

    added = _add_source_bookmark(runner, "docs-view", "view", "docs")
    used = runner.invoke(app, ["bookmark", "use", "docs-view"])

    assert added.exit_code == 0
    assert used.exit_code == 0
    assert "- [1] readme.txt" in used.output


def test_use_runs_a_read_bookmark(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    _synced_filesystem_source(project_cwd)
    runner = CliRunner()

    added = _add_source_bookmark(runner, "docs-read", "read", "docs/readme.txt")
    used = runner.invoke(app, ["bookmark", "use", "docs-read"])

    assert added.exit_code == 0
    assert used.exit_code == 0
    assert "hello" in used.output


def test_add_rejects_a_read_target_that_use_cannot_project(
    isolated_home: Path,
    project_cwd: Path,
    fixture_tree: Callable[[str, Path], Path],
) -> None:
    _synced_directory_source(project_cwd, fixture_tree)
    runner = CliRunner()

    rejected = _add_source_bookmark(runner, "docs-nonleaf", "read", "docs")
    used = runner.invoke(app, ["bookmark", "use", "docs-nonleaf"])

    assert rejected.exit_code == 1
    assert rejected.output == (
        "[error] [scope=project] [action=add] [code=bookmark.add.error.target_unresolved] [mode=read] [target=docs]: "
        "cannot resolve the read target docs because the route does not exist. "
        "view the source to pick a route\n"
    )
    assert used.exit_code == 1
    assert "bookmark.use.error.id_not_found" in used.output


def test_add_and_use_agree_on_a_leaf_read_target(
    isolated_home: Path,
    project_cwd: Path,
    fixture_tree: Callable[[str, Path], Path],
) -> None:
    _synced_directory_source(project_cwd, fixture_tree)
    runner = CliRunner()

    added = _add_source_bookmark(runner, "docs-leaf", "read", "docs/README.md")
    used = runner.invoke(app, ["bookmark", "use", "docs-leaf"])

    assert added.exit_code == 0
    assert used.exit_code == 0
    assert "API documentation" in used.output


def test_use_reports_a_missing_cache_with_its_own_code(
    isolated_home: Path,
    project_cwd: Path,
    fixture_tree: Callable[[str, Path], Path],
) -> None:
    _synced_directory_source(project_cwd, fixture_tree)
    runner = CliRunner()
    _add_source_bookmark(runner, "docs-leaf", "read", "docs/README.md")
    cache = isolated_home / ".apiscope" / "cache"
    for entry in cache.iterdir():
        shutil.rmtree(entry)

    used = runner.invoke(app, ["bookmark", "use", "docs-leaf"])

    assert used.exit_code == 1
    assert used.output == (
        "[error] [scope=project] [action=use] [code=bookmark.use.error.cache_missing] "
        "[name=docs] [target=docs/README.md]: "
        "the source docs has no cached content; run sync first\n"
    )


def test_use_reports_an_unknown_source_with_its_own_code(
    isolated_home: Path,
    project_cwd: Path,
    fixture_tree: Callable[[str, Path], Path],
) -> None:
    _synced_directory_source(project_cwd, fixture_tree)
    runner = CliRunner()
    _add_source_bookmark(runner, "docs-leaf", "read", "docs/README.md")
    removed = runner.invoke(app, ["remove", "docs"])

    used = runner.invoke(app, ["bookmark", "use", "docs-leaf"])

    assert removed.exit_code == 0
    assert used.exit_code == 1
    assert used.output == (
        "[error] [scope=project] [action=use] [code=bookmark.use.error.source_not_found] "
        "[name=docs] [target=docs/README.md]: "
        "the address docs/README.md names an unknown source\n"
    )


def test_use_reports_an_invalid_source_definition_with_its_own_code(
    isolated_home: Path,
    project_cwd: Path,
    fixture_tree: Callable[[str, Path], Path],
) -> None:
    # a saved reference can outlive a hand edit that breaks its source definition
    _synced_directory_source(project_cwd, fixture_tree)
    runner = CliRunner()
    added = _add_source_bookmark(runner, "docs-leaf", "read", "docs/README.md")
    config_path = project_cwd / ".apiscope" / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["source"]["docs"]["doc_src"] = "https://example.test/readme.md"
    config_path.write_text(json.dumps(config) + "\n", encoding="utf-8")

    used = runner.invoke(app, ["bookmark", "use", "docs-leaf"])

    assert added.exit_code == 0
    assert used.exit_code == 1
    assert used.output == (
        "[error] [scope=project] [action=use] [code=bookmark.use.error.source_invalid] "
        "[name=docs] [target=docs/README.md]: "
        "the source docs has an invalid definition; check its type and location\n"
    )


def test_use_reports_a_malformed_id_as_a_format_error(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["bookmark", "use", "BAD_ID"])

    assert result.exit_code == 1
    assert result.output == (
        "[error] [scope=project] [action=use] [code=bookmark.use.error.invalid_id] [id=BAD_ID]: "
        "the bookmark id BAD_ID is invalid, [id] must match the pattern "
        "^[a-z][a-z0-9]*(-[a-z0-9]+){0,2}$, but [BAD_ID] was given\n"
    )


def test_project_write_ignores_the_state_directory(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello\n")
    _add_file(CliRunner(), "my-note", target)

    ignore = (project_cwd / ".gitignore").read_text(encoding="utf-8")

    assert ".apiscope/" in ignore


def test_remove_finds_a_global_entry_from_a_project(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello\n")
    runner = CliRunner()
    runner.invoke(
        app,
        ["--global", "bookmark", "add", "home-note", "file", str(target), "--description", DESCRIPTION],
    )

    removed = runner.invoke(app, ["bookmark", "remove", "home-note"])

    assert removed.exit_code == 0
    payload = json.loads((isolated_home / ".apiscope" / "bookmarks.json").read_text(encoding="utf-8"))
    assert payload["bookmarks"]["home-note"]["removed"] is True


def test_remove_reports_an_unknown_id(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    removed = CliRunner().invoke(app, ["bookmark", "remove", "nope"])

    assert removed.exit_code == 1
    assert "no bookmark has the id" in removed.output


def test_prune_keeps_an_invalid_entry_without_the_flag(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello\n")
    runner = CliRunner()
    _add_file(runner, "my-note", target)
    target.unlink()

    runner.invoke(app, ["bookmark", "prune"])
    listed = runner.invoke(app, ["bookmark", "list"])

    assert "my-note" in listed.output
    assert "(invalid)" in listed.output


def test_prune_invalid_deletes_an_invalid_and_isolated_entry(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello\n")
    runner = CliRunner()
    _add_file(runner, "my-note", target)
    target.unlink()

    pruned = runner.invoke(app, ["bookmark", "prune", "--invalid"])
    listed = runner.invoke(app, ["bookmark", "list"])

    assert pruned.exit_code == 0
    assert "[pruned=1]" in pruned.output
    assert "my-note" not in listed.output


def test_an_invalid_stored_file_is_reported(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    path = project_cwd / ".apiscope" / "bookmarks.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "$schema": "./schema/bookmarks.schema.json",
                "bookmarks": {
                    "broken": {
                        "id": "broken",
                        "description": DESCRIPTION,
                        "mode": "group",
                        "members": ["a", "b"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    listed = CliRunner().invoke(app, ["bookmark", "list"])

    assert listed.exit_code == 1
    assert "root.error.config.invalid" in listed.output


def test_prune_cleans_a_global_entry_from_a_project(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello\n")
    runner = CliRunner()
    runner.invoke(
        app,
        ["--global", "bookmark", "add", "home-note", "file", str(target), "--description", DESCRIPTION],
    )
    runner.invoke(app, ["bookmark", "remove", "home-note"])

    pruned = runner.invoke(app, ["bookmark", "prune"])

    assert pruned.exit_code == 0
    payload = json.loads((isolated_home / ".apiscope" / "bookmarks.json").read_text(encoding="utf-8"))
    assert "home-note" not in payload["bookmarks"]


def test_prune_keeps_a_shadowed_active_global_entry(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello\n")
    runner = CliRunner()
    runner.invoke(
        app,
        ["--global", "bookmark", "add", "home-note", "file", str(target), "--description", DESCRIPTION],
    )
    runner.invoke(
        app,
        ["bookmark", "add", "home-note", "file", str(target), "--description", DESCRIPTION, "--force"],
    )
    runner.invoke(app, ["bookmark", "remove", "home-note"])

    pruned = runner.invoke(app, ["bookmark", "prune"])
    listed = runner.invoke(app, ["bookmark", "list"])

    assert pruned.exit_code == 0
    payload = json.loads((isolated_home / ".apiscope" / "bookmarks.json").read_text(encoding="utf-8"))
    assert payload["bookmarks"]["home-note"].get("removed") is not True
    assert "[home-note]" in listed.output
    assert "(active)" in listed.output


def test_view_bookmark_invalidates_when_the_source_changes(
    isolated_home: Path,
    project_cwd: Path,
) -> None:
    _synced_filesystem_source(project_cwd)
    runner = CliRunner()
    _add_source_bookmark(runner, "docs-view", "view", "docs/readme.txt")

    (project_cwd / "docs" / "readme.txt").write_text("changed\n", encoding="utf-8")
    runner.invoke(app, ["sync", "all", "docs", "--force"])
    listed = runner.invoke(app, ["bookmark", "list"])

    assert listed.exit_code == 0
    assert "(invalid)" in listed.output


def test_add_rejects_extra_targets_for_a_file(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    first = _write(tmp_path, "one.md", "hello\n")
    second = _write(tmp_path, "two.md", "hello\n")

    added = runner.invoke(
        app,
        ["bookmark", "add", "my-note", "file", str(first), str(second), "--description", DESCRIPTION],
    )

    assert added.exit_code == 1
    assert "exactly one target" in added.output


def test_group_rejects_a_duplicate_member(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    members = [f"note-{index}" for index in range(1, 6)]
    for member in members:
        _add_file(runner, member, _write(tmp_path, f"{member}.md", "hello\n"))

    added = _add_group(runner, "my-group", [members[0]] * 5)

    assert added.exit_code == 1
    assert "same member twice" in added.output


def test_force_cannot_make_a_group_contain_itself(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    _add_file(runner, "my-group", _write(tmp_path, "note.md", "hello\n"))
    members = [f"note-{index}" for index in range(1, 5)]
    for member in members:
        _add_file(runner, member, _write(tmp_path, f"{member}.md", "hello\n"))
    arguments = ["bookmark", "add", "my-group", "group", "my-group"]
    for member in members:
        arguments += [member]
    arguments += ["--description", DESCRIPTION, "--force"]

    added = runner.invoke(app, arguments)

    assert added.exit_code == 1
    assert "cannot contain itself" in added.output


def test_force_cannot_create_a_group_cycle(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    members = [f"note-{index}" for index in range(1, 6)]
    for member in members:
        _add_file(runner, member, _write(tmp_path, f"{member}.md", "hello\n"))
    _add_group(runner, "group-a", members)
    _add_group(runner, "group-b", ["group-a", *members[1:]])
    arguments = ["bookmark", "add", "group-a", "group", "group-b"]
    for member in members[1:]:
        arguments += [member]
    arguments += ["--description", DESCRIPTION, "--force"]

    added = runner.invoke(app, arguments)

    assert added.exit_code == 1
    assert "cycle" in added.output


def test_use_group_reports_the_member_status(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    members = [f"note-{index}" for index in range(1, 6)]
    targets = {}
    for member in members:
        targets[member] = _write(tmp_path, f"{member}.md", "hello\n")
        _add_file(runner, member, targets[member])
    _add_group(runner, "my-group", members)
    targets["note-1"].write_text("changed\n", encoding="utf-8")

    used = runner.invoke(app, ["bookmark", "use", "my-group"])

    assert used.exit_code == 0
    assert "- [note-1] file" in used.output
    assert "(invalid)" in used.output


def test_remove_keeps_the_field_set_of_a_non_group_entry(
    isolated_home: Path,
    project_cwd: Path,
    tmp_path: Path,
) -> None:
    target = _write(tmp_path, "note.md", "hello\n")
    runner = CliRunner()
    _add_file(runner, "my-note", target)

    runner.invoke(app, ["bookmark", "remove", "my-note"])

    payload = json.loads((project_cwd / ".apiscope" / "bookmarks.json").read_text(encoding="utf-8"))
    entry = payload["bookmarks"]["my-note"]
    assert entry["removed"] is True
    assert "members" not in entry
