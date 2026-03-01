# LLM API Scope (apiscope)

A command-line tool designed for Large Language Models (LLMs) and developers to index, search, and query structured API documentation (e.g., OpenAPI specifications). It assists LLMs in obtaining API information quickly and accurately within automated workflows.

## Installation

apiscope is a command-line tool, not a Python library. For isolated installation without affecting your system Python, we recommend using pipx:

```bash
# don't use pip
pipx install llm-api-scope
```

## Command Usage

### `apiscope init`
Initialize the project by creating a configuration file (`apiscope.ini`) and cache directory (`.apiscope/cache/`). It automatically adds `.apiscope/` to your project's `.gitignore`.

### `apiscope list`
List all configured API specifications by displaying the `<name> = <source>` pairs from the configuration file.

### `apiscope search <name> <keywords> [--force]`
Search within a specific API specification (`<name>`) for endpoints matching the given keywords. Returns the total count and displays up to 10 matching `<path>:<method>` identifiers.

### `apiscope describe <name> <path:method> [--force]`
Generate and output a concise Markdown guide for using the specified endpoint (`<path:method>`) from the API specification (`<name>`). The guide includes essential calling information such as parameters, request body, and response structure.

### `apiscope note`
Manage reflective notes for agent reasoning and knowledge capture. This command provides a structured notebook system with six cognitive note types: Observation (OBS), Reasoning (REA), Action (ACT), Reflection (REF), Question (QUE), and Inspiration (INS).

Available subcommands:
- `auth`: Establish and manage agent identity authentication through three philosophical dimensions (Name, Role, Story). Required before creating notes to ensure the agent has a defined sense of self.
- `write`: Create a new note with specified author and type (uses two-phase write mechanism)
- `read`: Display notes for a specific author with pagination and size limits
- `add`: Append annotations (REFERENCE, NOTE, or TIP) to existing notes
- `stats`: Analyze note-taking patterns, temporal concentration, and thinking segments
- `readme`: Display comprehensive documentation about the note system

Notes are stored in `.apiscope/notes/` with automatic organization by author and timestamp. The system supports pattern recognition for classical thinking sequences like Empirical Induction, Hypothetico-Deductive reasoning, and Experimental Science. For complete documentation, run `apiscope note readme`.
