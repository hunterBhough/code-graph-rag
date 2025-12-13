# Data Model: Project Rename Entities

**Feature**: Rename code-graph-rag to weavr
**Date**: 2025-12-13

## Overview

This data model catalogs all identifier patterns that must be updated during the rename. Since this is a rename operation rather than a feature addition, the "entities" are the various forms of the project name that appear throughout the codebase and ecosystem.

## Identifier Entities

### 1. Python Package Identifiers

**Entity**: `codebase_rag` (Python module)

**Locations**:
- Directory name: `codebase_rag/` → `weavr/`
- Import statements: `from codebase_rag.X` → `from weavr.X`
- Import statements: `import codebase_rag` → `import weavr`
- Test paths: `codebase_rag/tests/` → `weavr/tests/`
- Type hints: References in docstrings and comments

**Validation Rules**:
- Must maintain Python identifier conventions (no hyphens)
- Must be valid package name (lowercase, underscores allowed)
- Must match directory name exactly

**Relationships**:
- Referenced by: All Python modules in the project
- Referenced by: `pyproject.toml` setuptools configuration
- Referenced by: pytest configuration
- Referenced by: mypy configuration

**State Transitions**: N/A (atomic rename)

---

### 2. Package Distribution Name

**Entity**: `graph-code` (pip package name)

**Locations**:
- `pyproject.toml`: `name = "graph-code"` → `name = "weavr"`
- README.md: Installation instructions
- Documentation: All pip install examples
- External service configurations

**Validation Rules**:
- Must comply with PEP 423 (package naming)
- Should be available on PyPI (if publishing)
- Hyphens allowed in distribution names

**Relationships**:
- Referenced by: pip installation commands
- Referenced by: uv package manager
- Controls: Entry point script name

**State Transitions**: N/A (atomic rename)

---

### 3. CLI Command Name

**Entity**: `graph-code` (entry point script)

**Locations**:
- `pyproject.toml`: `[project.scripts]` section
- Documentation: All command examples
- Shell scripts: Any automation using the CLI
- GitHub workflows: CI/CD pipelines

**Validation Rules**:
- Must be valid shell command name
- Should be memorable and short
- Must not conflict with existing commands

**Relationships**:
- Defined by: `pyproject.toml` project.scripts
- Executes: `weavr.main:app`
- Referenced in: All usage documentation

**State Transitions**: N/A (atomic rename)

---

### 4. Docker Infrastructure Names

**Entity**: Docker Compose service references

**Locations**:
- `docker-compose.yaml`: Service names (keeping as-is: `memgraph`, `lab`)
- `docker-compose.yaml`: Container names (already `codebase-intelligence-*`)
- `docker-compose.yaml`: Volume names (preserving data)
- `docker-compose.yaml`: Stack name (keeping `codebase-intelligence`)
- Code comments: References to infrastructure purpose

**Validation Rules**:
- Stack name shared across multiple services (DO NOT CHANGE)
- Service names generic and reusable (DO NOT CHANGE)
- Only update documentation comments

**Relationships**:
- Shared by: code-graph-rag (soon weavr), vector-search-mcp, docwell
- Preserves: Memgraph data volumes

**State Transitions**: N/A (no changes to names)

---

### 5. Documentation References

**Entity**: Project name in prose and examples

**Locations**:
- `README.md`: Project title, descriptions, examples
- `CLAUDE.md`: Project identity and context
- `VISION.md`: Purpose and philosophy
- `ARCHITECTURE.md`: System descriptions
- Inline code comments: Where project is mentioned
- `docs/` directory: All markdown files

**Validation Rules**:
- Must be consistent across all documents
- Should include attribution to original project
- Must update all code examples and commands
- Git history references are EXCLUDED (keep as-is)

**Patterns to Replace**:
- "code-graph-rag" → "weavr"
- "Code Graph RAG" → "Weavr"
- "codebase_rag" → "weavr" (in documentation context)
- "graph-code" → "weavr" (in command examples)

**Relationships**:
- Informs: Users, AI assistants, developers
- Reflects: Package and module naming choices

**State Transitions**: N/A (atomic update)

---

### 6. External Service References

**Entity**: Integration configurations in ecosystem

**Locations**:
- `../http-service-wrappers/`: Configuration and documentation
- `../mcp-service-wrappers/`: Configuration and documentation
- `~/code/ai_agency/shared/scripts/registry/projects.json`: Project registry
- Other ai_agency projects: Any references in code or docs

**Validation Rules**:
- Must maintain service compatibility
- Must update registry metadata
- Should preserve service URLs if unchanged

**Relationships**:
- Depended on by: http-service-wrappers, mcp-service-wrappers
- Registered in: Project registry
- May be referenced by: Other ai_agency tools

**State Transitions**: N/A (atomic update)

---

### 7. Environment and Configuration

**Entity**: Environment variable prefixes and config keys

**Locations**:
- `.env` files: Variable names (if any project-specific vars exist)
- `codebase_rag/config.py`: Configuration keys
- Documentation: Environment setup instructions

**Validation Rules**:
- Check for hardcoded project name in env var names
- Update config keys if they reference old name
- Verify .env.example files are updated

**Relationships**:
- Loaded by: Config management system
- Referenced in: Documentation and setup guides

**State Transitions**: N/A (atomic update)

## Identifier Patterns Summary

| Old Pattern | New Pattern | Context |
|-------------|-------------|---------|
| `codebase_rag` | `weavr` | Python imports, directory name |
| `graph-code` | `weavr` | Package name, CLI command |
| `code-graph-rag` | `weavr` | Documentation, prose |
| `Code Graph RAG` | `Weavr` | Titles, headings |
| `codebase-intelligence` | (unchanged) | Docker stack name |
| `memgraph` | (unchanged) | Docker service name |

## Non-Entities (Excluded from Rename)

These are explicitly NOT changed:

1. **Git commit history**: Old references preserved for context
2. **Git tags**: Historical releases keep old names
3. **Docker stack name**: `codebase-intelligence` is shared infrastructure
4. **Docker service names**: `memgraph`, `lab` are generic
5. **Memgraph database schema**: Graph node/edge labels unchanged
6. **External forks/clones**: Out of scope
7. **Original project**: code-graph-rag remains as separate reference

## Validation Criteria

After rename, the following must be true:

- ✅ All imports resolve to `weavr.*` package
- ✅ CLI command `weavr` executes successfully
- ✅ Package installs as `weavr` via pip/uv
- ✅ All tests pass with new naming
- ✅ Documentation refers to "weavr" consistently
- ✅ External services can reference new name
- ✅ No broken references (except allowed git history)
- ✅ Docker infrastructure continues working
