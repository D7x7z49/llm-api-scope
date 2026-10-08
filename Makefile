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
.PHONY: test coverage golden e2e
test:
	pdm run pytest

# report branch coverage for the fast suite, apart from e2e
coverage:
	pdm run pytest --cov=apiscope --cov-branch --cov-report=term-missing

# rewrite golden output for one test path, for example: make golden GOLDEN=tests/list
golden:
	@: $${GOLDEN:?set GOLDEN to a test path, for example tests/list}
	UPDATE_GOLDEN=1 pdm run pytest $(GOLDEN)

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
