# tests/usage.unit.test.py

from typer.main import get_command

from apiscope.app import app
from apiscope.usage import render_usage


def test_render_usage_omits_the_typer_completion_options() -> None:
    text = render_usage(get_command(app))

    assert "--install-completion" not in text
    assert "--show-completion" not in text


def test_render_usage_lists_the_root_options_and_commands() -> None:
    text = render_usage(get_command(app))

    assert text.startswith("- apiscope #")
    assert "  + [--global]?" in text
    assert "  + [--json]?" in text
    assert "  - skill #" in text
