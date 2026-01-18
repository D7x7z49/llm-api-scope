# AGENTS.md

## Tool Stack
- Version Control: `git` and GitHub CLI (`gh`)
- Project & Dependency Management: `pdm` (Python)
- Safety Check: Always use `[command] --help` or `-h` first if unsure.

## Safety Rules
1. Check First: Run `--help` before using an unfamiliar command or flag.
2. Confirm Context: Ensure you are in the correct project directory.
3. Be Cautious: Understand the impact before running commands that change history (`git rebase`, `git reset`) or remove dependencies (`pdm remove`).
