# scripts/ci/usage.py

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from typer.main import get_command

from apiscope.app import app
from apiscope.usage import render_usage


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the apiscope usage reference.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", metavar="PATH", help="write the usage reference to PATH")
    group.add_argument("--check", metavar="PATH", help="fail when PATH differs from the generated usage")
    args = parser.parse_args()

    text = render_usage(get_command(app))

    if args.write is not None:
        Path(args.write).write_text(text, encoding="utf-8")
        return 0
    if args.check is not None:
        path = Path(args.check)
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        if current != text:
            sys.stderr.write(f"{args.check} is out of date; run scripts/ci/usage.py --write {args.check}\n")
            return 1
        return 0
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
