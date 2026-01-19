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
