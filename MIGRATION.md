# Migration Guide: From code-graph-rag to Weavr

This document describes the migration from the original **code-graph-rag** project to **Weavr**, a rebranded and restructured version of the codebase analysis tool.

## Overview

**Weavr** is the new name and identity for the code-graph-rag project. The rename reflects the project's evolution and emphasis on weaving together code structure, relationships, and context into a unified knowledge graph.

### Key Changes

- **Package Name**: `codebase_rag` → `weavr`
- **CLI Command**: `graph-code` → `weavr`
- **Python Package**: `pip install graph-code` → `pip install -e .` (with package name `weavr`)
- **Import Paths**: All Python imports use `weavr` instead of `codebase_rag`

## For Users

### Installation

If you've been using the development version:

```bash
# Old command (no longer works)
pip uninstall graph-code

# New command
uv sync
# or for development
pip install -e .
```

### CLI Commands

All CLI commands now use the `weavr` prefix:

```bash
# Old commands (deprecated)
graph-code index
graph-code chat
graph-code mcp
graph-code http

# New commands
weavr index      # Index a codebase
weavr chat       # Interactive query CLI
weavr mcp        # Start MCP server
weavr http       # Start HTTP server
```

### Python Imports

Update any Python code that imports from the old package:

```python
# Old imports (no longer work)
from codebase_rag.services import GraphService
from codebase_rag.tools import query_code_graph

# New imports
from weavr.services import GraphService
from weavr.tools import query_code_graph
```

## For Developers

### Repository Structure

The project structure has been updated:

```
weavr/                    # Main Python package (was: codebase_rag/)
├── main.py             # CLI entry point
├── mcp/                # MCP server implementation
├── http/               # HTTP server implementation
├── parsers/            # Language-specific parsers
├── services/           # Core services (graph, LLM)
├── tools/              # Query and manipulation tools
├── utils/              # Utility modules
└── tests/              # Test suite

docs/                   # Documentation
├── ARCHITECTURE.md     # System design and graph schema
└── VISION.md          # Project vision and philosophy

examples/              # Example scripts and usage patterns

specs/                 # Specification and planning documents
└── 005-rename-to-weavr/  # Rename specification and tasks
```

### Configuration Files

Environment variables and configuration prefixes have been updated:

```bash
# Old environment variable prefix
CODEBASE_RAG_*

# New environment variable prefix
WEAVR_*
```

### GitHub Repository

If you're managing the repository:

1. The repository will be renamed from `code-graph-rag` to `weavr`
2. Update any documentation that references the old repository name
3. Update CI/CD pipelines that reference the old package name

**Note**: The repository rename must be performed manually through GitHub settings by the repository owner.

## Breaking Changes

### Package Name Changes

- **Python Package**: Import statements must be updated from `codebase_rag` to `weavr`
- **CLI Command**: The command-line tool is now invoked with `weavr` instead of `graph-code`
- **Environment Variables**: Configuration variables use `WEAVR_` prefix instead of `CODEBASE_RAG_`

### Command-Line Interface

All CLI commands remain the same, but use the new `weavr` command prefix:

| Old | New |
|-----|-----|
| `graph-code index` | `weavr index` |
| `graph-code chat` | `weavr chat` |
| `graph-code mcp` | `weavr mcp` |
| `graph-code http` | `weavr http` |

## Verification

To verify the migration is complete:

1. **CLI Access**: Run `weavr --help` and confirm the command works
2. **Imports**: Verify your Python code imports from `weavr` package
3. **Tests**: Run `uv run pytest` and confirm all tests pass
4. **Environment**: Update any environment variables from `CODEBASE_RAG_*` to `WEAVR_*`

## Support

If you encounter issues during migration:

1. Check that you're using the correct package name (`weavr`)
2. Verify your Python imports match the new structure
3. Clear Python cache: `find . -type d -name __pycache__ -exec rm -r {} +`
4. Reinstall the package: `uv sync` or `pip install -e .`
5. Run the test suite: `uv run pytest`

## Attribution

Weavr is built upon the original **code-graph-rag** project. The rename reflects the project's evolution while maintaining all core functionality and improvements.

Original project: https://github.com/user/code-graph-rag (archived)

## Timeline

- **code-graph-rag**: Original project
- **Weavr**: Rebrand and restructure (December 2024)

---

For more information, see:
- [README.md](README.md) - Project overview
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Technical architecture
- [docs/VISION.md](docs/VISION.md) - Project vision and philosophy
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
