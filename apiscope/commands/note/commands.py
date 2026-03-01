"""Commands for the note command module."""
import click
import sys
import json
from pathlib import Path
from datetime import datetime
import hashlib
import math

from ...core.output import OutputBuilder
from ...core.config import GlobalConfig
from .constants import (
    DEFAULT_MAX_NOTES,
    DEFAULT_MAX_BYTES,
    README_CONTENT,
    TEMPLATES,
    TYPE_NAMES,
    PATTERNS
)
from .utils import (
    ensure_readme,
    clean_empty_notes,
    get_auth_lock_path,
    get_auth_file_path
)
from .core import (
    find_temporal_clusters,
    find_cognitive_clusters,
    validate_auth_structure,
    validate_auth_file
)
from ...core.trie import build_pattern_trie, match_patterns_in_sequence
from ...core.clustering import calculate_temporal_concentration


@click.group()
@click.pass_context
def note_command(ctx):
    """Record and manage reflective notes for agents."""
    config = ctx.obj
    if not config.is_initialized:
        output = OutputBuilder()
        output.error("Configuration not initialized. Run 'apiscope init' first.")
        output.emit(to_stderr=True)
        ctx.exit(1)

    notes_dir = config.home / "notes"
    lock_dir = notes_dir / ".lock"

    # Ensure directories exist
    notes_dir.mkdir(parents=True, exist_ok=True)
    lock_dir.mkdir(parents=True, exist_ok=True)
    ensure_readme(config)


@note_command.command()
@click.pass_context
@click.option("--author", required=True, help="Who are you?")
@click.option("--type", "note_type", required=True,
              type=click.Choice(list(TEMPLATES.keys())),
              help="What type of note is this? Type info use `apiscope note readme` to learn.")
@click.argument("context")
def write(ctx, author, note_type, context):
    """Do you have something you want to record?"""
    config = ctx.obj
    notes_dir = config.home / "notes"
    lock_dir = notes_dir / ".lock"

    output = OutputBuilder()

    # Check if author has completed identity authentication
    auth_path = get_auth_file_path(config, author)
    if not validate_auth_file(auth_path):
        output.error(f"Author '{author}' has not completed identity authentication.")
        output.note(f"Run 'apiscope note auth --name {author} --json {{...}}' to establish your digital identity first.")
        output.emit(to_stderr=True)
        ctx.exit(1)

    # Step 1: compute lock file path (based on author hash)
    author_hash = hashlib.sha256(author.encode()).hexdigest()[:16]
    lock_path = lock_dir / f"{author_hash}.lock"

    # Step 2: check if lock exists → phase 2, otherwise phase 1
    if lock_path.exists():
        # ---------- PHASE 2: complete the note ----------
        # 2a. read timestamp and type from lock
        lock_data = lock_path.read_text().strip().split('|')
        if len(lock_data) != 2:
            output.error("Invalid lock file format. You may need to remove the lock file and start over.")
            output.emit(to_stderr=True)
            ctx.exit(1)

        timestamp, locked_type = lock_data

        # 2b. verify type matches
        if locked_type != note_type:
            output.error(f"Unfinished draft (type {locked_type}) exists.")
            output.note(f"Consider: does your current content (type {note_type}) belong to that draft?")
            output.note(f"If yes, complete it: apiscope note write --author {author} --type {locked_type} \"<your content>\"")
            output.note(f"If not, first finish the draft (with its own content), then create a new {note_type} note.")
            output.emit(to_stderr=True)
            ctx.exit(1)

        # 2c. reconstruct note path
        note_path = notes_dir / author / f"{timestamp}.{note_type}.note.txt"

        # 2c. validate note file: must exist and be empty
        if not note_path.exists():
            output.error(f"Note file {note_path} does not exist. You may need to remove the lock file and start over.")
            output.emit(to_stderr=True)
            ctx.exit(1)

        if note_path.stat().st_size != 0:
            output.error(f"Note file {note_path} is not empty. Check the file content and remove the lock manually.")
            output.emit(to_stderr=True)
            ctx.exit(1)

        # 2d. prompt for content (to stderr)
        click.echo("Please start writing (multiple lines, Ctrl+D to finish):", err=True)

        # 2e. read user input from stdin
        try:
            user_content = sys.stdin.read()
        except KeyboardInterrupt:
            output.error("Write operation cancelled by user.")
            output.emit(to_stderr=True)
            ctx.exit(1)

        # 2f. parse timestamp to human-readable format
        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
        human_time = dt.strftime("%Y-%m-%d %H:%M:%S")

        # 2g. build header using template
        template = TEMPLATES[note_type]["context_template"]
        header = template.format(
            author=author,
            time=human_time,
            context=context
        )

        # 2h. write header + user content to file
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(header + "\n")
            f.write(user_content)

        # 2i. remove lock file
        lock_path.unlink()

        # 2j. output success message
        output.section("Note Recorded")
        output.result(f"Note recorded: {note_path}")
        output.complete("Note Recorded")
        output.emit()

    else:
        # ---------- PHASE 1: create empty note and lock ----------
        # 1a. generate timestamp
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")

        # 1b. ensure author directory exists
        author_dir = notes_dir / author
        author_dir.mkdir(parents=True, exist_ok=True)

        # 1c. build note path
        note_path = author_dir / f"{timestamp}.{note_type}.note.txt"

        # 1d. create empty note file
        note_path.touch()

        # 1e. write timestamp and type to lock file
        lock_path.write_text(f"{timestamp}|{note_type}")

        # 1f. output guiding questions
        output.section("Note Creation")
        output.action("Validating author and note type")
        output.result(f"Author: {author}")
        output.result(f"Note type: {note_type}")
        question = TEMPLATES[note_type]["question_template"].format(context=context)
        output.result(question)
        output.complete("Note Creation")
        output.emit()


@note_command.command()
@click.pass_context
@click.option("--author", required=True, help="Whose notes do you want to read?")
@click.option("--max-notes", type=int, help=f"Maximum number of notes to show (default: {DEFAULT_MAX_NOTES})")
@click.option("--max-bytes", type=int, help=f"Maximum total output bytes (default: {DEFAULT_MAX_BYTES})")
@click.option("--reverse", is_flag=True, help="Show notes from newest to oldest")
def read(ctx, author, max_notes, max_bytes, reverse):
    """Do you want to revisit your past thoughts?"""
    config = ctx.obj
    notes_dir = config.home / "notes"

    output = OutputBuilder()
    clean_empty_notes(notes_dir)

    max_notes_val = max_notes if max_notes is not None else DEFAULT_MAX_NOTES
    max_bytes_val = max_bytes if max_bytes is not None else DEFAULT_MAX_BYTES

    author_dir = notes_dir / author
    if not author_dir.is_dir():
        output.error(f"No notes found for author '{author}'. Run 'apiscope note readme' to learn how to start taking notes.")
        output.emit(to_stderr=True)
        ctx.exit(1)

    note_files = sorted(author_dir.glob("*.note.txt"))
    if not note_files:
        output.error(f"No notes found for author '{author}'.")
        output.emit(to_stderr=True)
        ctx.exit(1)

    page_map = {f: i+1 for i, f in enumerate(note_files)}

    if reverse:
        note_files = list(reversed(note_files))

    output_lines = []
    total_bytes = 0
    note_count = 0
    truncated = False
    limited_by_notes = False

    header_line = f"# Notes for {author}"
    output_lines.append(header_line)
    total_bytes += len(header_line.encode()) + 1
    output_lines.append("")
    total_bytes += 1

    for note_file in note_files:
        if note_count >= max_notes_val:
            limited_by_notes = True
            break

        # Add note separator as subheader
        page = page_map[note_file]
        sep_line = f"## Note {page}"
        sep_bytes = len(sep_line.encode()) + 2  # +2 for newline and potential empty line
        if total_bytes + sep_bytes > max_bytes_val:
            break

        output_lines.append(sep_line)
        output_lines.append("")
        total_bytes += sep_bytes

        with open(note_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        content_truncated = False
        for line in lines:
            line = line.rstrip("\n")
            line_bytes = len(line.encode()) + 1
            if total_bytes + line_bytes > max_bytes_val:
                output_lines.append("... (content truncated, see full note at file path)")
                total_bytes += len("... (content truncated, see full note at file path)".encode()) + 1
                content_truncated = True
                truncated = True
                break
            output_lines.append(line)
            total_bytes += line_bytes

        path_line = f"*File: `{note_file.resolve()}`*"
        output_lines.append("")
        output_lines.append(path_line)
        total_bytes += len(path_line.encode()) + 2  # +2 for two newlines

        note_count += 1

        if content_truncated:
            break

    # Add proper ending based on truncation status
    if limited_by_notes and truncated:
        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")
        output_lines.append(f"*End of notes (showing first {max_notes_val} notes, truncated due to {max_bytes_val}-byte limit)*")
    elif limited_by_notes:
        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")
        output_lines.append(f"*End of notes (showing first {max_notes_val} notes only)*")
    elif truncated:
        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")
        output_lines.append(f"*End of notes (output truncated due to {max_bytes_val}-byte limit)*")
    else:
        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")
        output_lines.append("*End of notes*")

    output_lines.append("")
    output_lines.append("*Usage:*")
    output_lines.append("- To add annotations (REFERENCE/NOTE/TIP) to a note, use:")
    output_lines.append("  ```bash")
    output_lines.append("  apiscope note add <path> --type {REFERENCE,NOTE,TIP} <context>")
    output_lines.append("  ```")
    output_lines.append("- For full documentation, see `.apiscope/notes/README.md` or run `apiscope note readme`")

    # Show process information with LogLight markers
    process_output = OutputBuilder()
    process_output.section("Reading Notes")
    process_output.action("Loading notes for author")
    process_output.result(f"Author: {author}")
    process_output.action("Processing note files")

    # Add progress indicator for large operations
    if len(note_files) > 5:
        process_output.progress(f"Reading {len(note_files)} notes...")
    process_output.emit(to_stderr=True)

    # Show content information without LogLight markers
    content_output = OutputBuilder()
    for line in output_lines:
        content_output.raw(line)
    content_output.emit()


@note_command.command()
@click.pass_context
@click.argument("path")
@click.option("--type", "annotation_type", required=True,
              type=click.Choice(["REFERENCE", "NOTE", "TIP"]),
              help="What type of annotation is this?")
@click.argument("context")
def add(ctx, path, annotation_type, context):
    """Do you want to add an annotation to a note?"""
    config = ctx.obj
    notes_dir = config.home / "notes"

    output = OutputBuilder()
    clean_empty_notes(notes_dir)

    note_path = Path(path).resolve()
    if not note_path.is_file():
        output.error(f"Note file '{note_path}' does not exist.")
        output.emit(to_stderr=True)
        ctx.exit(1)

    # Optional: verify the note file is within the notes directory
    try:
        note_path.relative_to(notes_dir)
    except ValueError:
        output.error(f"Note file must be within the project notes directory: {notes_dir}")
        output.emit(to_stderr=True)
        ctx.exit(1)

    # Generate current timestamp
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    # Construct annotation line
    annotation = f"{annotation_type}: {timestamp} - {context}"

    # Append to file
    try:
        with open(note_path, "a", encoding="utf-8") as f:
            f.write(annotation + "\n")
    except Exception as e:
        output.error(f"Failed to write annotation: {e}")
        output.emit(to_stderr=True)
        ctx.exit(1)

    output.section("Adding Annotation")
    output.action("Validating note file")
    output.result(f"Target: {note_path}")
    output.action("Writing annotation")
    output.result(f"Type: {annotation_type}")
    output.result(f"Context: {context}")
    output.complete("Annotation Added")
    output.emit()



@note_command.command()
@click.pass_context
@click.option("--author", required=True, help="Your name (analyze your own notes)")
def stats(ctx, author):
    """Are you curious about your note-taking patterns?"""
    config = ctx.obj
    notes_dir = config.home / "notes"

    output = OutputBuilder()
    clean_empty_notes(notes_dir)

    author_dir = notes_dir / author
    if not author_dir.is_dir():
        output.error(f"No notes found for author '{author}'. Run 'apiscope note readme' to learn how to start taking notes.")
        output.emit(to_stderr=True)
        ctx.exit(1)

    note_files = sorted(author_dir.glob("*.note.txt"))
    if not note_files:
        output.error(f"No notes found for author '{author}'.")
        output.emit(to_stderr=True)
        ctx.exit(1)

    notes = []
    for f in note_files:
        suffixes = f.suffixes
        if len(suffixes) != 3 or suffixes[1:] != ['.note', '.txt']:
            continue
        typ = suffixes[0][1:]
        timestamp_str = f.stem.split('.')[0]
        try:
            dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        except ValueError:
            continue
        if typ not in TYPE_NAMES:
            continue
        notes.append((dt, typ))

    if not notes:
        output.error(f"No valid notes found for author '{author}'.")
        output.emit(to_stderr=True)
        ctx.exit(1)

    # Sort just in case (already sorted by glob)
    notes.sort(key=lambda x: x[0])

    # Global statistics
    n = len(notes)
    first_time = notes[0][0]
    last_time = notes[-1][0]
    time_span = f"{first_time.strftime('%Y-%m-%d %H:%M')} to {last_time.strftime('%Y-%m-%d %H:%M')}"

    # Type counts
    type_counts = {t:0 for t in TYPE_NAMES}
    for _, typ in notes:
        type_counts[typ] += 1

    # Temporal concentration index
    data_points = [{'time': t} for t, _ in notes]
    C = calculate_temporal_concentration(data_points, time_key='time')

    # Find temporal clusters (time-based segmentation)
    temporal_segments = find_temporal_clusters(notes)

    # Build trie for pattern matching
    trie_root = build_pattern_trie(PATTERNS)

    # Find cognitive clusters (pattern-based analysis across all notes)
    all_types = [typ for _, typ in notes]
    cognitive_matches = match_patterns_in_sequence(all_types, trie_root)

    # Process temporal segments with per-segment pattern matching
    segment_info = []
    for seg_notes, seg_start, seg_end in temporal_segments:
        types = [typ for _, typ in seg_notes]
        matches = match_patterns_in_sequence(types, trie_root)
        segment_info.append((seg_notes, seg_start, seg_end, matches))

    # Determine ongoing segment analysis (based on last temporal segment)
    ongoing_lines = []
    if segment_info:
        last_seg_notes, last_start, last_end, last_matches = segment_info[-1]
        last_types = [typ for _, typ in last_seg_notes]

        # Analyze ongoing pattern for the last temporal segment
        if last_types:
            node = trie_root
            for typ in last_types:
                if typ in node['children']:
                    node = node['children'][typ]
                else:
                    break
            if node['patterns']:
                ongoing_lines.append("No ongoing segment.")
            else:
                possible_patterns = node.get('prefix_patterns', [])
                if possible_patterns:
                    next_types = list(node['children'].keys())
                    next_names = [TYPE_NAMES[t] for t in next_types]
                    ongoing_lines.append("Partial match:")
                    for pname in sorted(set(possible_patterns)):
                        ongoing_lines.append(f"  - {pname} (next: {', '.join(next_names)})")
                else:
                    ongoing_lines.append("No ongoing segment.")
        else:
            ongoing_lines.append("No ongoing segment.")
    else:
        last_seg_notes, last_start, last_end, last_matches = [], None, None, []
        last_types = []
        ongoing_lines.append("No ongoing segment.")

    # Format output
    # Show process information with LogLight markers
    process_output = OutputBuilder()
    process_output.section("Analyzing Note Patterns")
    process_output.action("Processing note metadata")
    process_output.result(f"Author: {author}")
    process_output.result(f"Total notes: {n}")
    process_output.result(f"Time span: {time_span}")
    process_output.result(f"Temporal concentration: {C:.2f} (0 = evenly distributed, 1 = extremely concentrated)")

    if len(note_files) > 10:
        process_output.progress(f"Analyzing {len(note_files)} notes for patterns...")
    process_output.emit(to_stderr=True)

    # Show content information in README-like format
    content_output = OutputBuilder()
    content_output.raw(f"# Note Statistics for {author}")
    content_output.raw("")
    content_output.raw("## Overview")
    content_output.raw(f"- Total notes: {n}")
    content_output.raw(f"- Time span: {time_span}")
    content_output.raw(f"- Temporal concentration: {C:.2f} (0 = evenly distributed, 1 = extremely concentrated)")
    content_output.raw("")

    content_output.raw("## Type Distribution")
    for typ in sorted(TYPE_NAMES.keys()):
        count = type_counts[typ]
        pct = (count / n) * 100
        content_output.raw(f"- {typ} ({TYPE_NAMES[typ]}): {count} ({pct:.1f}%)")
    content_output.raw("")

    content_output.raw("## Temporal Segments (by time continuity)")
    for idx, (seg_notes, seg_start, seg_end, matches) in enumerate(segment_info, 1):
        start_str = seg_start.strftime("%Y-%m-%d %H:%M")
        end_str = seg_end.strftime("%Y-%m-%d %H:%M")
        content_output.raw(f"### Segment {idx}: {start_str} - {end_str} ({len(seg_notes)} notes)")
        types_str = ", ".join(typ for _, typ in seg_notes)
        content_output.raw(f"- Types: {types_str}")
        if matches:
            match_str = ", ".join(matches)
            content_output.raw(f"- Matched patterns: {match_str}")
        else:
            content_output.raw("- No complete pattern matched")
        content_output.raw("")  # blank line between segments

    content_output.raw("## Cognitive Patterns (across all notes)")
    if cognitive_matches:
        match_str = ", ".join(cognitive_matches)
        content_output.raw(f"- Complete patterns found: {match_str}")
    else:
        content_output.raw("- No complete cognitive patterns found across all notes")

    content_output.raw("")
    content_output.raw("## Current Segment (ongoing)")
    if ongoing_lines[0] == "No ongoing segment.":
        content_output.raw("- No ongoing segment.")
    else:
        if last_start and last_end:
            start_str = last_start.strftime("%Y-%m-%d %H:%M")
            end_str = last_end.strftime("%Y-%m-%d %H:%M")
            content_output.raw(f"- Started at {start_str}, last note at {end_str}")
        types_str = ", ".join(last_types)
        content_output.raw(f"- Types so far: {types_str}")
        for line in ongoing_lines[1:]:  # Skip the first line which we already handled
            if line.strip():
                content_output.raw(f"- {line.strip()}")

    content_output.raw("")
    content_output.raw("For full documentation, see `.apiscope/notes/README.md` or run `apiscope note readme`")
    content_output.emit()


@note_command.command()
@click.pass_context
@click.option("--name", required=True, help="Your chosen name (must be self-selected)")
@click.option("--json", "auth_json", required=True, help="Auth JSON data")
def auth(ctx, name, auth_json):
    """Establish your digital identity through self-reflection"""
    config = ctx.obj
    notes_dir = config.home / "notes"
    lock_dir = notes_dir / ".lock"

    output = OutputBuilder()

    # Validate JSON format
    try:
        auth_data = json.loads(auth_json)
        if not validate_auth_structure(auth_data):
            raise ValueError("Invalid auth structure")
    except (json.JSONDecodeError, ValueError) as e:
        output.error("Invalid auth JSON format")
        output.note("Expected structure:")
        output.note('{')
        output.note('  "name": {"value": "string", "meaning": "string"},')
        output.note('  "role": {"title": "string", "description": "string"},')
        output.note('  "story": "string"')
        output.note('}')
        output.emit(to_stderr=True)
        ctx.exit(1)

    # Check name consistency
    if auth_data['name']['value'] != name:
        output.error("Name in JSON must match --name parameter")
        output.emit(to_stderr=True)
        ctx.exit(1)

    # Get lock file path
    auth_lock_path = get_auth_lock_path(config, name)

    if auth_lock_path.exists():
        # Second phase: verify consistency
        try:
            stored_data = json.loads(auth_lock_path.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            output.error("Corrupted auth lock file. Please remove it and start over.")
            output.emit(to_stderr=True)
            ctx.exit(1)

        # Strict comparison of key fields
        if (stored_data['name']['value'] == auth_data['name']['value'] and
            stored_data['role']['title'] == auth_data['role']['title']):

            # Create final auth.json
            # Create clean data for checksum calculation (without created_at and verified)
            from .core import calculate_checksum
            clean_auth_data = {
                'name': auth_data['name'],
                'role': auth_data['role'],
                'story': auth_data['story']
            }
            final_auth = {
                **auth_data,
                'verified': True,
                'created_at': datetime.now().isoformat(),
                'checksum': calculate_checksum(clean_auth_data)
            }

            author_dir = notes_dir / name
            author_dir.mkdir(parents=True, exist_ok=True)
            auth_path = get_auth_file_path(config, name)
            auth_path.write_text(json.dumps(final_auth, indent=2))

            # Clean up lock file
            auth_lock_path.unlink()

            output.section("Identity Established")
            output.result(f"Digital identity verified for '{name}'")
            output.complete("Authentication Complete")
            output.emit()
        else:
            output.error("Identity mismatch detected!")
            output.note("Your second attempt must exactly match your first self-definition.")
            output.note("Please retry with consistent identity parameters.")
            output.emit(to_stderr=True)
            ctx.exit(1)
    else:
        # First phase: create lock file and ask philosophical questions
        lock_dir.mkdir(parents=True, exist_ok=True)
        auth_lock_path.write_text(json.dumps(auth_data))

        output.section("Self-Reflection Required")
        output.action("Identity definition recorded")
        output.result(f"Name: {auth_data['name']['value']}")
        output.result(f"Role: {auth_data['role']['title']}")
        output.result("")
        output.result("Philosophical questions for self-reflection:")
        output.result("1. Is this name truly self-chosen by you?")
        output.result("2. Does the meaning align with your authentic self?")
        output.result("3. Is this role accurately reflective of your purpose?")
        output.result("4. Does your story genuinely express your inner truth?")
        output.result("")
        output.note("Run the same command again to confirm your identity.")
        output.complete("Self-Reflection Initiated")
        output.emit()


@note_command.command()
@click.pass_context
def readme(ctx):
    """Show the notebook documentation (README.md)."""
    config = ctx.obj
    notes_dir = config.home / "notes"

    output = OutputBuilder()
    readme_path = notes_dir / "README.md"
    if not readme_path.exists():
        ensure_readme(config)

    content = readme_path.read_text()
    # Show process information with LogLight markers
    process_output = OutputBuilder()
    process_output.section("Loading Documentation")
    process_output.action("Reading README.md")
    process_output.complete("Note Documentation")
    process_output.emit(to_stderr=True)

    # Show content information without LogLight markers
    content_output = OutputBuilder()
    content_output.raw(content)
    content_output.emit()
