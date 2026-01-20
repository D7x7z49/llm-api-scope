# AGENTS.md

## TOOL STACK
- Version Control: `git` and GitHub CLI (`gh`)
- Project & Dependency Management: `pdm` (Python)
- Safety Check: Always use `[command] --help` or `-h` first if unsure.

## SAFETY RULES
1. Check First: Run `--help` before using an unfamiliar command or flag.
2. Confirm Context: Ensure you are in the correct project directory.
3. Be Cautious: Understand the impact before running commands that change history (`git rebase`, `git reset`) or remove dependencies (`pdm remove`).

## PYTHON MODULES REPO
if you need help, you can MCP (Model Context Protocol) to get help.

1. click: <https://github.com/pallets/click>
2. httpx: <https://github.com/encode/httpx>
3. openapi-core: <https://github.com/python-openapi/openapi-core>
4. python-semantic-release: <https://github.com/python-semantic-release/python-semantic-release>
