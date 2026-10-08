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
.PHONY: test golden e2e
test:
	pdm run pytest

# rewrite the golden output files from the current behavior
golden:
	UPDATE_GOLDEN=1 pdm run pytest

# run the installed console script end to end, apart from the fast suite
e2e:
	pdm run pytest tests/e2e -o addopts="--import-mode=importlib"

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
