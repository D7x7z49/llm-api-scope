"""
apiscope/core/output.py

LogLight-style output builder for consistent, concise command output.
INFO: docs/loglight-style.md
"""
from typing import List, Optional


class OutputBuilder:
    """
    Builds structured command output following LogLight style.

    Usage:
        output = OutputBuilder()
        output.section("Initialization")
        output.action("Creating configuration")
        output.result("Configuration created")
        output.complete("Initialization")
        output.emit()
    """

    def __init__(self) -> None:
        """Initialize a new output builder with empty lines."""
        self._lines: List[str] = []

    def section(self, title: str) -> "OutputBuilder":
        """
        Start a new section.

        Args:
            title: Section title (will appear in start and complete markers)
        """
        self._lines.append(f"[=] {title} Start")
        return self

    def action(self, message: str) -> "OutputBuilder":
        """
        Add an action step.

        Args:
            message: Action description (verb phrase recommended)
        """
        self._lines.append(f"[-] {message}")
        return self

    def result(self, message: str) -> "OutputBuilder":
        """
        Add a positive result or discovery.

        Args:
            message: Result description
        """
        self._lines.append(f"[+] {message}")
        return self

    def note(self, message: str) -> "OutputBuilder":
        """
        Add a non-critical warning or informational note.

        Args:
            message: Note content
        """
        self._lines.append(f"[?] {message}")
        return self

    def error(self, message: str) -> "OutputBuilder":
        """
        Add a critical error.

        Args:
            message: Error description
        """
        self._lines.append(f"[!] {message}")
        return self

    def complete(self, title: str) -> "OutputBuilder":
        """
        Complete a section.

        Args:
            title: Section title (should match start title)
        """
        self._lines.append(f"[=] {title} Complete")
        return self

    def raw(self, line: str) -> "OutputBuilder":
        """
        Add a raw line without formatting.

        Use sparingly for special cases.
        """
        self._lines.append(line)
        return self

    def blank(self) -> "OutputBuilder":
        """Add a blank line (use sparingly for visual separation)."""
        self._lines.append("")
        return self

    def add(self, marker: str, message: str) -> "OutputBuilder":
        """
        Add a line with custom marker.

        Args:
            marker: Custom marker (e.g., "[*]" for progress)
            message: Line content
        """
        self._lines.append(f"{marker} {message}")
        return self

    def emit(self, to_stderr: bool = False) -> None:
        """
        Output all collected lines.

        Args:
            to_stderr: If True, output to stderr instead of stdout
        """
        import click

        output = "\n".join(self._lines)
        if to_stderr:
            click.echo(output, err=True)
        else:
            click.echo(output)

    def clear(self) -> "OutputBuilder":
        """Clear all collected lines."""
        self._lines.clear()
        return self

    @property
    def lines(self) -> List[str]:
        """Get the current list of output lines."""
        return self._lines.copy()

    @property
    def has_content(self) -> bool:
        """Check if any lines have been added."""
        return len(self._lines) > 0

    def __len__(self) -> int:
        """Get the number of lines in the builder."""
        return len(self._lines)


# Convenience function for one-off output
def log_output(
    marker: str,
    message: str,
    to_stderr: bool = False
) -> None:
    """
    Output a single line with the given marker.

    Args:
        marker: LogLight marker (e.g., "[+]", "[-]", "[?]", "[!]")
        message: Message content
        to_stderr: If True, output to stderr
    """
    import click

    line = f"{marker} {message}"
    if to_stderr:
        click.echo(line, err=True)
    else:
        click.echo(line)
