"""Generic trie (prefix tree) implementation for pattern matching."""
from typing import Dict, List, Any


def build_pattern_trie(patterns: Dict[str, List[Any]]) -> Dict[str, Any]:
    """Build a trie from pattern sequences.

    Args:
        patterns: Dictionary mapping pattern names to sequences of elements

    Returns:
        Root node of the trie structure
    """
    root = {'children': {}, 'patterns': [], 'prefix_patterns': []}
    for name, seq in patterns.items():
        node = root
        for element in seq:
            if element not in node['children']:
                node['children'][element] = {
                    'children': {},
                    'patterns': [],
                    'prefix_patterns': []
                }
            node = node['children'][element]
            node['prefix_patterns'].append(name)
        node['patterns'].append(name)
    return root


def match_patterns_in_sequence(seq: List[Any], trie_root: Dict[str, Any]) -> List[str]:
    """Greedy longest matching of patterns in a sequence.

    Args:
        seq: Input sequence to match against patterns
        trie_root: Root node of the trie built with build_pattern_trie()

    Returns:
        List of matched pattern names in order of appearance
    """
    i = 0
    matches = []
    n = len(seq)
    while i < n:
        node = trie_root
        last_match = None
        last_match_pos = -1
        j = i
        while j < n and seq[j] in node['children']:
            node = node['children'][seq[j]]
            if node['patterns']:
                last_match = node['patterns'][0]
                last_match_pos = j
            j += 1
        if last_match is not None:
            matches.append(last_match)
            i = last_match_pos + 1
        else:
            i += 1
    return matches
