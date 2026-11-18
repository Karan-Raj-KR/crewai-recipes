# Shortcuts for common developer commands. Run `make` (or `make help`) to list them.
#
# KEEP IN SYNC: the `lint` and `contract` targets must run exactly the same
# commands as .github/workflows/ci.yml (the "Ruff Lint" and "Recipe Contract"
# jobs). If you change a command there, change it here too, or `make lint`
# could pass locally while CI fails.
#
# make is optional. Every target below is a plain shell command, and the raw
# commands are also listed in CONTRIBUTING.md for anyone without make.

PYTHON ?= python
LINT_PATHS := recipes/ playground/ tools/ tests/
RECIPES := $(sort $(patsubst recipes/%/crew.py,%,$(wildcard recipes/[!_]*/crew.py)))

.DEFAULT_GOAL := help
.PHONY: help lint format contract sync-check test check playground \
	install-dev install-playground test-recipe test-playground list-recipes

help: ## List available targets
	@echo "Usage: make <target>"
	@echo ""
	@grep -hE '^[a-zA-Z_%-]+:.*## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  %-20s %s\n", $$1, $$2}'
	@echo ""
	@echo "Recipes: $(RECIPES)"

lint: ## Run the same ruff checks as CI (lint + format check)
	ruff check $(LINT_PATHS)
	ruff format --check $(LINT_PATHS)

format: ## Auto-format the code with ruff
	ruff format $(LINT_PATHS)

contract: ## Run the recipe contract test (same as CI, no install needed)
	pytest tests/test_recipe_contract.py -v

sync-check: ## Check that every recipe's llm.py is identical
	$(PYTHON) tools/sync_llm.py --check

test: contract sync-check ## Run the fast checks that need no recipe installs

check: lint test ## Run everything to do before pushing

install-dev: ## Install dev tools (ruff, pytest) from requirements-dev.txt
	$(PYTHON) -m pip install -r requirements-dev.txt

install-%: ## Install one recipe's dependencies, e.g. make install-faq-bot
	@test -f recipes/$*/requirements.txt || \
		{ echo "Unknown recipe '$*'. Run 'make list-recipes' to see them."; exit 1; }
	$(PYTHON) -m pip install -r recipes/$*/requirements.txt

install-playground: ## Install the playground's dependencies
	$(PYTHON) -m pip install -r playground/requirements.txt

test-recipe: ## Run one recipe's tests, e.g. make test-recipe RECIPE=faq-bot
	@test -n "$(RECIPE)" || { echo "Usage: make test-recipe RECIPE=<name>"; exit 1; }
	@test -d recipes/$(RECIPE) || \
		{ echo "Unknown recipe '$(RECIPE)'. Run 'make list-recipes' to see them."; exit 1; }
	cd recipes/$(RECIPE) && LLM_API_KEY=test-key pytest -v

test-playground: ## Run the playground's tests
	cd playground && LLM_API_KEY=test-key pytest -v

playground: ## Start the local web playground on http://127.0.0.1:8000
	cd playground && uvicorn main:app --reload

list-recipes: ## List all recipes
	@for r in $(RECIPES); do echo $$r; done
