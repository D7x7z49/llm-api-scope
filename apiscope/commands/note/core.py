"""Core functions for the note command module."""
import json
from datetime import datetime
from pathlib import Path
import hashlib
from ...core.clustering import analyze_temporal_patterns, calculate_temporal_concentration
from ...core.trie import build_pattern_trie, match_patterns_in_sequence
from .constants import PATTERNS, TYPE_NAMES


def find_temporal_clusters(notes):
    """Find temporal clusters based on time gaps between notes.

    Args:
        notes: List of (datetime, type) tuples

    Returns:
        List of segments where each segment contains notes that are temporally close
    """
    if not notes:
        return []

    # Convert to the format expected by clustering module
    data_points_with_type = [{'time': t, 'data': typ} for t, typ in notes]
    analysis_result = analyze_temporal_patterns(data_points_with_type, time_key='time', data_key='data')
    segments_data = analysis_result['clusters']

    # Convert back to the format expected by existing code
    segments = []
    for segment in segments_data:
        seg_notes = [(point['time'], point['data']) for point in segment['points']]
        seg_start = segment['start_time']
        seg_end = segment['end_time']
        segments.append((seg_notes, seg_start, seg_end))

    return segments


def find_cognitive_clusters(notes):
    """Find cognitive clusters based on thinking patterns across all notes.

    Args:
        notes: List of (datetime, type) tuples

    Returns:
        List of matched pattern names across all notes
    """
    if not notes:
        return []

    # Extract types from all notes
    all_types = [typ for _, typ in notes]

    # Build trie and match patterns across all notes
    trie_root = build_pattern_trie(PATTERNS)
    matches = match_patterns_in_sequence(all_types, trie_root)

    return matches


# Authentication validation functions
def validate_auth_structure(auth_data: dict) -> bool:
    """Validate the structure of auth JSON data."""
    required_fields = ['name', 'role', 'story']
    if not all(field in auth_data for field in required_fields):
        return False

    # Validate name structure
    if not isinstance(auth_data['name'], dict):
        return False
    if not all(key in auth_data['name'] for key in ['value', 'meaning']):
        return False
    if not all(isinstance(auth_data['name'][key], str) for key in ['value', 'meaning']):
        return False

    # Validate role structure
    if not isinstance(auth_data['role'], dict):
        return False
    if not all(key in auth_data['role'] for key in ['title', 'description']):
        return False
    if not all(isinstance(auth_data['role'][key], str) for key in ['title', 'description']):
        return False

    # Validate story
    if not isinstance(auth_data['story'], str):
        return False

    return True


def calculate_checksum(auth_data: dict) -> str:
    """Calculate checksum for auth data to prevent tampering."""
    # Create a clean copy with only the core identity fields
    clean_data = {
        'name': auth_data['name'],
        'role': auth_data['role'],
        'story': auth_data['story']
    }
    data_str = json.dumps(clean_data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(data_str.encode()).hexdigest()


def verify_checksum(auth_data: dict) -> bool:
    """Verify the checksum of auth data."""
    if 'checksum' not in auth_data:
        return False
    expected_checksum = calculate_checksum(auth_data)
    return auth_data['checksum'] == expected_checksum


def validate_auth_file(auth_path: Path) -> bool:
    """Validate auth.json file integrity and completeness."""
    if not auth_path.exists():
        return False

    try:
        data = json.loads(auth_path.read_text())

        # Check basic structure
        if not validate_auth_structure(data):
            return False

        # Check verification status
        if not data.get('verified', False):
            return False

        # Check checksum
        if not verify_checksum(data):
            return False

        return True
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return False
