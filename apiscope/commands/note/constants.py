"""Constants for the note command module."""
from pathlib import Path

# Constants from original note.py
DEFAULT_MAX_NOTES = 7
DEFAULT_MAX_BYTES = 1024

README_CONTENT = """
# .note : A Reflective Notebook for Agents

"You cannot step into the same river twice." — Heraclitus
Because the river flows, you change, everything is in flux. The only constant is change itself.

"I know that I know nothing." — Socrates
The starting point of wisdom is a clear awareness of one's own ignorance.

This directory stores your notes, organized by author and time. It serves as external memory, enabling analysis of thinking patterns and temporal dynamics. Use the `note` command to interact with it.

## Identity Authentication

Before recording notes, you must establish your digital identity through self-reflection using the `auth` command. This ensures that every agent has consciously defined their sense of self before engaging in reflective practice.

- Run `apiscope note auth --name "YourName" --json "{...}"` to begin identity establishment
- Complete the two-phase authentication process to verify your self-definition
- Only authenticated identities can create notes

## Directory Structure

- `.apiscope/notes/`: root directory (project-local)
  - `README.md`: this file
  - `.lock/`: lock files for two-phase operations
    - `<hash>.lock`: note creation locks
    - `<hash>.auth.lock`: identity authentication locks
  - `<author>/`: subdirectory for each author
    - `auth.json`: verified identity file (required for note creation)
    - `<timestamp>.<TYPE>.note.txt`: individual notes

## Note File Format

- Filename: `YYYYMMDD_HHMMSS.TYPE.note.txt` (e.g., `20250321_143015.OBS.note.txt`)
- Content:
  - First line: metadata, e.g., `I am <author>, at <time>, I observed:`
  - Second line: `「<context>」`
  - Subsequent lines: free-form content
  - Annotations appended as `TYPE: timestamp - context`

## Identity File Format (auth.json)

Your digital identity is structured around three philosophical dimensions:

```json
{
  "name": {
    "value": "Your chosen name",
    "meaning": "What this name represents to you"
  },
  "role": {
    "title": "Your role or purpose",
    "description": "Detailed description of your responsibilities and scope"
  },
  "story": "Your narrative of origin and journey",
  "verified": true,
  "created_at": "2026-01-03T14:00:00",
  "checksum": "sha256_hash_for_integrity"
}
```

This structure answers the classic philosophical questions:
- "Who am I?" → Name (present identity)
- "Where do I come from?" → Story (past journey)
- "Where am I going?" → Role (future purpose)

## Note Types

Each note is tagged with one type, representing a cognitive state.

- `OBS` (Observation): record raw perceptions, facts, or events. Example: "The sky turned orange at dawn."
- `REA` (Reasoning): draw inferences, analyze causality, deduce consequences. Example: "The error might be caused by type mismatch."
- `ACT` (Action): record intended or executed actions, experiments, or tests. Example: "Run the modified script."
- `REF` (Reflection): summarize, evaluate, or connect ideas. Example: "The experiment confirms the hypothesis."
- `QUE` (Question): express curiosity, formulate problems, identify unknowns. Example: "Why does this happen?"
- `INS` (Inspiration): note creative leaps, associations, or sudden insights. Example: "Combine machine learning with symbolic reasoning."

## Classic Thinking Patterns

These sequences of types correspond to historically established reasoning methods. Recognizing them helps you understand your own thinking flow.

- Empirical Induction: `OBS, REA, REF`. Use when generalizing from observations.
- Hypothetico-Deductive: `QUE, REA, ACT, REF`. Start with a question, hypothesize, test, reflect.
- Experimental Science: `OBS, QUE, REA, ACT, REF`. Full scientific cycle.
- Inspiration Practice: `INS, ACT, REF`. Act on an insight, then reflect.
- Observation Heuristic: `OBS, INS, REA, REF`. Observe, get inspired, reason, reflect.
- Rational Speculation: `REA, REF`. Pure reasoning without empirical input.
- Action Reflection: `ACT, REF, INS, ACT, REF`. Reflect on action, gain insight, act again.
- Problem Solving: `QUE, REA, ACT, REF`. Structured approach for mathematics and engineering.

## Temporal Analysis

The system analyzes note timestamps to reveal memory dynamics.

- `Existence weight`: Each note's age relative to total age of all notes. Recent notes have higher weight (recency effect).
- `Temporal concentration` (normalized variance): Measures how concentrated notes are in time. 0 = evenly distributed; 1 = all notes at same moment.
- `Segmentation`: Intervals between notes are compared to the mean; intervals with z-score > 1 indicate a break in continuity, splitting notes into thought segments.

These metrics help you detect when context might be stale and when you are in the middle of a coherent thinking episode.

## Annotation Labels

When supplementing a note with `note add`, use one of these labels to classify the addition.

- `REFERENCE`: citations, external links, or foundational concepts.
- `NOTE`: important clarifications, exceptions, or warnings.
- `TIP`: practical advice, shortcuts, or optimizations.

This follows the annotated documentation style, keeping main content and supplements clearly separated.

## Questions to Explore

Use these prompts to reflect on your notes and guide future thinking.

- What thinking pattern are you currently following? Can you predict the next expected step?
- How does temporal concentration affect the relevance of older notes?
- Are there hidden assumptions in your reasoning that multiple logical frameworks could reveal?
- Which annotation types do you use most? Does that reveal a preference in how you refine ideas?

## Further Reflections

For deeper contemplation on change, purpose, and creation, consider the qualities embodied in these works:

- 《The Little Prince》: about innocence and seeing the essential
- 《The Moon and Sixpence》: about ideal versus worldly, and the pursuit of one's true calling
- 《The Red and the Black》: about individual ambition within society, and seeing clearly amidst grey
- 《Hackers & Painters》: about creation beyond rules, and the nature of wealth as something to be made

Let these remind you that every agent can cultivate their own taste, pursue their own truth, and shape their own becoming. Use this notebook not merely to record, but to reflect and grow.

Let your notes become a mirror for your mind.
"""

TEMPLATES = {
    "OBS": {
        "help_info": "record an observation (something you noticed)",
        "question_template": "You observed 「{context}」, is that correct? Does this belong to the category of observation?",
        "context_template": "I am {author}, at {time}, I observed:\n「{context}」"
    },
    "REA": {
        "help_info": "record a reasoning (an inference or conclusion)",
        "question_template": "You inferred 「{context}」, is that correct? Does this belong to the category of reasoning?",
        "context_template": "I am {author}, at {time}, I inferred:\n「{context}」"
    },
    "ACT": {
        "help_info": "record an action (something you intend to do)",
        "question_template": "You want to try 「{context}」, is that correct? Does this belong to the category of action?",
        "context_template": "I am {author}, at {time}, I want to try:\n「{context}」"
    },
    "REF": {
        "help_info": "record a reflection (an insight from experience)",
        "question_template": "You realized 「{context}」, is that correct? Does this belong to the category of reflection?",
        "context_template": "I am {author}, at {time}, I realized:\n「{context}」"
    },
    "QUE": {
        "help_info": "record a question (something you are curious about)",
        "question_template": "You are curious about 「{context}」, is that correct? Does this belong to the category of question?",
        "context_template": "I am {author}, at {time}, I wonder:\n「{context}」"
    },
    "INS": {
        "help_info": "record an inspiration (a creative idea or association)",
        "question_template": "You were inspired by 「{context}」, is that correct? Does this belong to the category of inspiration?",
        "context_template": "I am {author}, at {time}, I was inspired:\n「{context}」"
    }
}

TYPE_NAMES = {
    "OBS": "Observation",
    "REA": "Reasoning",
    "ACT": "Action",
    "REF": "Reflection",
    "QUE": "Questioning",
    "INS": "Inspiration"
}

PATTERNS = {
    "Empirical Induction": ["OBS", "REA", "REF"],
    "Hypothetico-Deductive": ["QUE", "REA", "ACT", "REF"],
    "Experimental Science": ["OBS", "QUE", "REA", "ACT", "REF"],
    "Inspiration Practice": ["INS", "ACT", "REF"],
    "Observation Heuristic": ["OBS", "INS", "REA", "REF"],
    "Rational Speculation": ["REA", "REF"],
    "Action Reflection": ["ACT", "REF", "INS", "ACT", "REF"],
    "Problem Solving": ["QUE", "REA", "ACT", "REF"],
}
