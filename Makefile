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

# Recipe names are checked against RECIPES inside make, and only printed with
# $(info), so a name never reaches the shell unless it's a real recipe.
check-recipe = $(if $(and $(filter 1,$(words $(1))),$(filter $(1),$(RECIPES))),,\
	$(error Unknown recipe '$(1)'. Run 'make list-recipes' to see them))

.DEFAULT_GOAL := help
.PHONY: help _help-targets lint format contract sync-check test check playground \
	install-dev install-playground test-recipe test-playground list-recipes

# $(info) runs before a target's shell lines, so the recipe list lives in
# `help` and the target list in a prerequisite that runs first.
help: _help-targets ## List available targets
	$(info Recipes: $(RECIPES))
	@:

_help-targets:
	@echo "Usage: make <target>"
	@echo ""
	@grep -hE '^[a-zA-Z_%-]+:.*## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  %-20s %s\n", $$1, $$2}'
	@echo ""

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
	$(call check-recipe,$*)
	$(PYTHON) -m pip install -r recipes/$*/requirements.txt

install-playground: ## Install the playground's dependencies
	$(PYTHON) -m pip install -r playground/requirements.txt

test-recipe: ## Run one recipe's tests, e.g. make test-recipe RECIPE=faq-bot
	$(if $(RECIPE),,$(error Usage: make test-recipe RECIPE=<name>))
	$(call check-recipe,$(RECIPE))
	cd recipes/$(RECIPE) && LLM_API_KEY=test-key pytest -v

test-playground: ## Run the playground's tests
	cd playground && LLM_API_KEY=test-key pytest -v

playground: ## Start the local web playground on http://127.0.0.1:8000
	cd playground && uvicorn main:app --reload

list-recipes: ## List all recipes
	$(foreach r,$(RECIPES),$(info $(r)))
	@:
