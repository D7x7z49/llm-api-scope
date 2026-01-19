# scripts/check_headers.py
"""
Check and fix file headers by adding relative path comments.

This script scans specified paths and ensures files have correct header comments
containing their relative paths. Supports multiple file extensions and handles
recursive directory traversal with ignore patterns.
"""

import os
import sys
from pathlib import Path

# File extension to comment marker mapping
COMMENT_MARKERS = {
    ".py": "#",
    ".sh": "#",
    ".yaml": "#",
    ".toml": "#",
    # Add more extensions as needed
}

# Relative paths to check (files or directories)
RELATIVE_PATHS = [
    "scripts",
    "apiscope",
    # Add more paths
]

# Patterns to ignore (e.g., common build dirs)
IGNORE_PATTERNS = [".git", "node_modules", ".venv", "dist", "build"]

def get_project_root():
    """Get project root directory (parent of scripts/)."""
    return Path(__file__).parent.parent

def should_ignore_path(path_parts):
    """Check if path should be ignored based on patterns."""
    path_str = str(Path(*path_parts))
    return any(pattern in path_str for pattern in IGNORE_PATTERNS)

def check_and_fix_header(file_path, relative_path):
    """Check and fix header for a single file."""
    ext = file_path.suffix
    comment_marker = COMMENT_MARKERS.get(ext)

    if not comment_marker:
        print(f"[?] No comment marker for {ext}: {relative_path}")
        return

    expected_header = f"{comment_marker} {relative_path}"

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        first_line = lines[0] if lines else ""

        # Trim whitespace
        first_line = first_line.strip()

        if first_line == expected_header:
            print(f"[+] Header correct: {relative_path}")
            return

        new_content = ""
        if first_line.startswith(comment_marker):
            # Existing comment: check for leading '/'
            path_part = first_line[len(comment_marker):].strip()
            if path_part.startswith("/"):
                # Fix: remove leading '/'
                fixed_path = path_part[1:]
                fixed_header = f"{comment_marker} {fixed_path}"
                new_content = (
                    fixed_header + "\n" +
                    content[len(first_line) + (1 if content.startswith(first_line) else 0):]
                )
                print(f"[-] Fixed leading '/': {relative_path}")
            else:
                # Replace mismatched header
                new_content = (
                    expected_header + "\n" +
                    content[len(first_line) + (1 if content.startswith(first_line) else 0):]
                )
                print(f"[-] Replaced header: {relative_path}")
        else:
            # Insert new header
            new_content = f"{expected_header}\n{content}"
            print(f"[-] Added header: {relative_path}")

        file_path.write_text(new_content, encoding="utf-8")
        print(f"[+] Updated: {relative_path}")

    except Exception as error:
        if isinstance(error, FileNotFoundError):
            print(f"[!] File not found: {relative_path}")
        else:
            print(f"[!] Error processing {relative_path}: {error}")

def check_directory_recursively(dir_path, base_path):
    """Recursively check files in a directory."""
    try:
        for item in dir_path.iterdir():
            if should_ignore_path(item.parts[len(base_path.parts):]):
                continue

            relative_path = item.relative_to(base_path)

            if item.is_file():
                ext = item.suffix
                if ext in COMMENT_MARKERS:
                    check_and_fix_header(item, str(relative_path))
            elif item.is_dir():
                check_directory_recursively(item, base_path)

    except Exception as error:
        if isinstance(error, FileNotFoundError):
            print(f"[!] Directory not found: {dir_path}")
        else:
            print(f"[!] Error processing directory {dir_path}: {error}")

def main():
    """Main execution."""
    print("[=] Header Check Start")

    project_root = get_project_root()
    print(f"[-] Project root: {project_root}")

    processed_count = 0
    updated_count = 0

    for rel_path in RELATIVE_PATHS:
        full_path = project_root / rel_path
        stats = None

        try:
            stats = full_path.stat()
        except FileNotFoundError:
            print(f"[!] Path not found: {rel_path}")
            continue

        if full_path.is_file():
            ext = full_path.suffix
            if ext in COMMENT_MARKERS:
                check_and_fix_header(full_path, rel_path)
                processed_count += 1
        elif full_path.is_dir():
            check_directory_recursively(full_path, project_root)
            # Count files processed (approximate)
            processed_count += sum(1 for _ in full_path.rglob("*") if _.suffix in COMMENT_MARKERS)

    print("[=] Header Check Complete")
    print(f"[+] Processed {processed_count} files")

if __name__ == "__main__":
    main()
