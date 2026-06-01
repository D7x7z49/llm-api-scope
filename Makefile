# Code quality
# ------------
.PHONY: lint format typecheck
lint:
	pdm run ruff check apiscope/ tests/
format:
	pdm run ruff format apiscope/ tests/
typecheck:
	pdm run mypy apiscope/ tests/

# Testing
# -------
.PHONY: test
test:
	pdm run pytest

# All-in-one
# ----------
.PHONY: check
check:
	pdm run pre-commit run --all-files

# Housekeeping
# ------------
.PHONY: clean
clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache
