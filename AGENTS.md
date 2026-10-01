<!-- AGENTS.md -->
<!-- project conventions for ai coding agents -->

TOOL STACK
- version control: `git` and GitHub CLI (`gh`)
- package management: `pdm`
- task automation: `make` (see Makefile)

SAFETY RULES
- check first: run `--help` before using an unfamiliar command or flag
- confirm context: ensure you are in the correct project directory
- use `APISCOPE_HOME` for all experiments and CLI tests
- use `pdm run apiscope` for the development CLI
- do not modify data owned by a global or pipx-installed `apiscope`
- use global installations only for official reference data
- treat `archive/` and `tmp/design/refactor/` as reference material
- never import runtime code from archived or reference material

VALIDATION
- read `tests/README.md` before adding or changing tests
- use `make test`, `make lint`, `make typecheck`, and `make check` as applicable
- run the smallest relevant checks first, then run the full required checks

EXPERIENCE FILES
- select only experience files relevant to the current task
- use `.pi/experience/git/commit-draft.exp.md` when preparing a commit
- keep reusable guidance in `.pi/experience/` and repository rules in this file
- write experience files with `.pi/prompts/pi/core/gen-exp-file.ebnf`
- keep one reusable topic per experience file and avoid one-off task notes

---
