# Code quality
# ------------
.PHONY: lint format typecheck
lint:
	uv run ruff check apiscope/ tests/
format:
	uv run ruff format apiscope/ tests/
typecheck:
	uv run mypy apiscope/ tests/

# Testing
# -------
.PHONY: test
test:
	uv run pytest

# All-in-one
# ----------
.PHONY: check
check:
	uv run pre-commit run --all-files

# Housekeeping
# ------------
.PHONY: clean
clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache
