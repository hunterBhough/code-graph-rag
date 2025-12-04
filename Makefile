.PHONY: help all install dev test clean python publish build-grammars watch test-parallel

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

all: ## Install everything for full development environment (deps, grammars, hooks, tests)
	@echo "🚀 Setting up complete development environment..."
	uv sync --all-extras
	git submodule update --init --recursive --depth 1
	uv run pre-commit install
	uv run pre-commit install --hook-type commit-msg
	@echo "🧪 Running tests in parallel to verify installation..."
	uv run pytest -n auto
	@echo "✅ Full development environment ready!"
	@echo "📦 Installed: All dependencies, grammars, pre-commit hooks"
	@echo "✓ Tests passed successfully"

install: ## Install project dependencies with full language support
	uv sync --extra treesitter-full

python: ## Install project dependencies for Python only
	uv sync

dev: ## Setup development environment (install deps + pre-commit hooks)
	uv sync --extra treesitter-full --extra dev --extra test
	uv run pre-commit install
	uv run pre-commit install --hook-type commit-msg
	@echo "✅ Development environment ready!"

test: ## Run tests
	uv run pytest

test-parallel: ## Run tests in parallel
	uv run pytest -n auto

clean: ## Clean up build artifacts and cache
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
build-grammars: ## Build grammar submodules
	git submodule update --init --recursive --depth 1
	@echo "Grammars built!"

watch: ## Watch repository for changes and update graph in real-time
	@if [ -z "$(REPO_PATH)" ]; then \
		echo "Error: REPO_PATH is required. Usage: make watch REPO_PATH=/path/to/repo"; \
		exit 1; \
	fi
	.venv/bin/python realtime_updater.py $(REPO_PATH) \
		--host $(or $(HOST),localhost) \
		--port $(or $(PORT),7687) \
		$(if $(BATCH_SIZE),--batch-size $(BATCH_SIZE),)

publish: install ## Register as user-level MCP server for Claude Code
	@echo "📦 Publishing code-graph-rag to user-level MCP servers..."
	-claude mcp remove code-graph --scope user 2>/dev/null || true
	claude mcp add code-graph --scope user -- uv run --directory $(CURDIR) graph-code mcp-server
	@echo ""
	@echo "✅ Published successfully!"
	@echo "Restart Claude Code to use the updated code-graph server."
	@echo ""
	@echo "Note: The MCP server inherits TARGET_REPO_PATH from Claude Code's working directory."
