<!-- apiscope/AGENTS.md -->
<!-- scope rules for the apiscope package tree -->

PURPOSE
- treat each package directory as a scope with a stable boundary and a repeated shape
- let a reader navigate the tree and work inside one scope with local rules
- keep dependencies directed, explicit, and few

FORMS
- a command scope holds `app.py`, `constants.py`, `context.py`, `preflight.py`, and `schema.py`
- a library scope holds `constants.py`, `schema.py`, and `errors.py`
- a source scope holds one module named after the role it serves
- a library may add `protocols.py` and `registry.py`
- a source may add its own `constants.py` and helper modules

RECURSION
- a command scope embeds a private library under a leading-underscore directory
- a library scope embeds one directory per source
- a source scope ends the chain
- the repeating unit is text, contract, behavior, and child scope

DEPENDENCIES
- a library may depend on the library it consumes, never the reverse
- a leading underscore marks a private scope
- keep each implementation inside its owning scope

CONTRACT
- a command or library declares its types and payloads in its `schema.py`
- keep user-facing text in the scope `constants.py`
- keep behavior local; extract a shared helper only when the copies are identical and need no flag

GRAMMAR
- this file states the rules; `apiscope/layout.ebnf` holds the current concrete scopes
- add or rename a scope in the instance file, not here

---
