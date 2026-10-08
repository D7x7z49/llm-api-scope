<!-- tests/AGENTS.md -->
<!-- scope rules for the test tree -->

PURPOSE
- treat the test tree as a scope that observes the package from the outside
- let a reader find a test by the package path and its setup by the same name
- keep simulation in two places: a conftest fixture and a fixture file

FORMS
- a test scope mirrors an apiscope scope of the same path
- a test file is `topic.kind.test.py`
- a fixtures directory holds inputs and expected output
- e2e is its own scope and mirrors nothing
- a python file is a conftest or a test file; the tree holds no `__init__.py`

FIXTURES
- a conftest is the root conftest or sits inside a mirror scope
- a conftest holds the fixtures for its scope
- a test module defines no fixture
- an autouse fixture is rare and carries a one line reason

KINDS
- a unit test covers one function or class with no process, no network, and no real home
- a component test drives the typer app through a runner with an isolated home
- an integration test uses a real local resource such as git or the lock file
- an e2e test runs the installed console script in a throwaway home

E2E
- `tests/e2e` is its own scope and mirrors nothing
- an e2e test runs the installed console script in a throwaway home
- a network path uses a loopback server, never the public network
- the scope runs with `make e2e`, apart from the fast suite

SIMULATION
- a unit test and a component test use an in-process mock transport
- an integration test and an e2e test may use a loopback server, never the public network
- a fixture provides an input; a test makes the assertion

DATA
- a large or shared input document lives under `fixtures/documents`
- a small single input stays inline
- a large or reused output lives under `fixtures/golden`
- a short one line message stays inline
- the `golden` fixture checks an output file, and `make golden` rewrites it

GRAMMAR
- this file states the rules; `tests/layout.txt` holds the shape
- `scripts/ci/tests_layout.py` enforces the shape

---
