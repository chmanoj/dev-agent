.PHONY: help install dev test lint format type-check security clean build publish

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	uv sync

dev: ## Install development dependencies
	uv sync --all-extras --dev
	uv run pre-commit install

test: ## Run tests with coverage
	uv run pytest --cov=dev_agent --cov-report=term-missing --cov-report=html

test-fast: ## Run tests without coverage
	uv run pytest -x

lint: ## Run linting checks
	uv run ruff check dev_agent tests

lint-fix: ## Run linting with auto-fix
	uv run ruff check --fix dev_agent tests

format: ## Format code
	uv run ruff format dev_agent tests

format-check: ## Check code formatting
	uv run ruff format --check dev_agent tests

type-check: ## Run type checking
	uv run mypy dev_agent

security: ## Run security checks
	uv run ruff check --select=S dev_agent tests

check-all: lint format-check type-check ## Run all code quality checks

quality: format lint type-check security ## Run all code quality checks

ci: quality test ## Run all CI checks locally

clean: ## Clean build artifacts and temporary files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf demo_project/
	rm -f MODERNIZATION_SUMMARY.md
	rm -f MANIFEST.in
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.tmp" -delete
	find . -type f -name "*.temp" -delete
	find . -type f -name ".DS_Store" -delete

build: clean ## Build package
	uv build

publish: build ## Publish to PyPI (requires PYPI_TOKEN)
	uv publish

run: ## Run the CLI in interactive mode
	uv run dev-agent

run-init: ## Initialize a new project
	uv run dev-agent init

run-resume: ## Resume existing project
	uv run dev-agent resume

docs-serve: ## Serve documentation locally
	uv run mkdocs serve

docs-build: ## Build documentation
	uv run mkdocs build

docs-deploy: ## Deploy documentation to GitHub Pages
	uv run mkdocs gh-deploy

docs-install: ## Install documentation dependencies
	uv sync --group docs