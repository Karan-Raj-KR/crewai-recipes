# crewai-recipes developer automation Makefile
# Mirrors commands executed in .github/workflows/ci.yml

.DEFAULT_GOAL := help

.PHONY: help lint format test test-contract sync-llm sync-llm-check playground build-site check

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Development targets:"
	@echo "  lint             Run ruff lint and format check (matches CI)"
	@echo "  format           Apply ruff auto-formatting"
	@echo "  test             Run root contract and provider fallback test suites"
	@echo "  test-contract    Run recipe contract test suite only"
	@echo "  sync-llm         Sync llm.py across all recipes from _template"
	@echo "  sync-llm-check   Verify all recipe llm.py copies are identical"
	@echo "  playground       Start the local FastAPI playground server"
	@echo "  build-site       Build gallery static bundle"
	@echo "  check            Run lint, format check, sync check, and root tests"

lint:
	ruff check recipes/ playground/ tools/ tests/
	ruff format --check recipes/ playground/ tools/ tests/

format:
	ruff format recipes/ playground/ tools/ tests/

test:
	pytest tests/test_recipe_contract.py tests/test_provider_fallback.py -v

test-contract:
	pytest tests/test_recipe_contract.py -v

sync-llm:
	python tools/sync_llm.py

sync-llm-check:
	python tools/sync_llm.py --check

playground:
	cd playground && uvicorn main:app --reload

build-site:
	python tools/build_site.py

check: lint sync-llm-check test
