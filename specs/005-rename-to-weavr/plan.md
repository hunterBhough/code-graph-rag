# Implementation Plan: Rename Project to Weavr

**Branch**: `005-rename-to-weavr` | **Date**: 2025-12-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-rename-to-weavr/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Comprehensive project rename from "code-graph-rag" to "weavr" across all code, documentation, and external ecosystem references. This is a pure renaming task with no functional changes - all existing features must continue working after the rename. The name "weavr" reflects the project's core purpose of weaving connections between codebases through structural code graph analysis.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**:
- Tree-sitter (0.25.0) for code parsing
- Memgraph (via pymgclient 1.4.0+) for graph storage
- Pydantic AI (1.28.0+) for LLM integration
- MCP (1.21.1+) for server protocol
- FastAPI (0.115.0+) for HTTP server
- Typer (0.12.5+) for CLI
- Docker Compose for infrastructure

**Storage**: Memgraph graph database (Docker container)
**Testing**: pytest with pytest-asyncio, 100% test pass requirement
**Target Platform**: macOS/Linux development environment, Docker infrastructure
**Project Type**: Single project with multiple interfaces (CLI, MCP server, HTTP server)
**Performance Goals**: Index 100k LOC in <60s, query response <2s (per constitution)
**Constraints**:
- Zero breaking changes to functionality
- All tests must pass after rename
- No modification to Memgraph data schema
- Backwards compatibility not required (new project name)

**Scale/Scope**:
- ~150 test files covering 6 languages (Python, TypeScript, JavaScript, Rust, Java, C++, Lua)
- 2 external service integration points (http-service-wrappers, mcp-service-wrappers)
- Full ai_agency repository ecosystem (~50+ projects)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principles Alignment

✅ **Precision Over Approximation**: Rename does not affect Tree-sitter parsing or Memgraph relationships. All structural queries remain 100% accurate.

✅ **Language Agnostic Foundation**: No changes to language parsers or unified graph schema. Rename is purely cosmetic.

✅ **Structural Focus**: No change to structural query capabilities. This is an infrastructure change, not a feature change.

✅ **Multiple Indexing Targets**: Functionality unchanged. External repos can still be indexed and queried.

✅ **MCP-First Integration**: All interfaces (MCP, HTTP, CLI) remain functional with updated naming.

### Quality Standards Compliance

✅ **Code Quality**: Type hints, mypy, Pydantic models all preserved. Only identifiers change.

✅ **Testing**: All 150+ tests must pass. Gate enforced in success criteria (SC-001).

✅ **Performance**: No performance impact. Indexing and query performance unchanged.

✅ **CLI Quality**: Rich formatting, error handling, UX unchanged. Only command names update (`graph-code` → `weavr`).

✅ **Documentation Quality**: CLAUDE.md, VISION.md, ARCHITECTURE.md, README.md all require updates as per FR-010 through FR-014.

### Development Workflow Impact

✅ **Adding Features**: No impact. Tool registry, graph schema, testing framework all unchanged.

✅ **Adding Language Support**: No impact. Parser framework unchanged.

✅ **Testing Requirements**: All gates enforced through SC-001 (100% test pass rate).

### Integration Contracts

✅ **MCP Server Contract**: Tool signatures unchanged. Server functionality preserved.

✅ **HTTP Server Contract**: Endpoint patterns unchanged. Only package names in responses may reflect new name.

✅ **CLI Contract**: Command structure preserved. Only entry point name changes.

### **GATE STATUS: ✅ PASSED**

No constitutional violations. This is a pure rename with zero functional changes.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

**Current structure (to be renamed):**

```text
codebase_rag/                    → weavr/
├── __init__.py
├── main.py                      # CLI entry point (Typer app)
├── config.py                    # Configuration management
├── mcp/                         # MCP server implementation
│   ├── server.py
│   └── tools.py
├── http/                        # HTTP server implementation
│   ├── server.py
│   ├── routes/
│   ├── models/
│   └── services/
├── parsers/                     # Language-specific parsers
│   ├── factory.py
│   ├── *_utils.py              # Per-language utilities
│   └── *_type_inference.py
├── services/                    # Core services
│   ├── graph_service.py
│   └── llm.py
├── tools/                       # MCP tool implementations
│   ├── structural_queries.py
│   ├── codebase_query.py
│   └── file_*.py
├── utils/                       # Utilities
│   ├── fqn_resolver.py
│   └── dependencies.py
└── tests/                       # Test suite
    ├── integration/
    └── test_*.py               # ~150 test files

docker-compose.yaml              # Infrastructure config
pyproject.toml                   # Package config (graph-code → weavr)
```

**Structure Decision**: Single project with multiple interfaces (CLI, MCP, HTTP). The main package directory `codebase_rag/` will be renamed to `weavr/`, and all internal imports will be updated accordingly. No structural reorganization is planned - only identifier changes.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**Status**: ✅ No violations - this section is not applicable for this feature.

This is a pure rename operation with zero functional changes, zero architectural additions, and zero new complexity.

---

## Post-Phase 1 Constitution Re-Evaluation

*Re-check performed after Phase 1 design completion*

### Design Artifacts Review

**Generated**:
- `research.md`: Rename strategies and best practices
- `data-model.md`: Identifier entities and transformation rules
- `contracts/rename-contract.md`: Verification checklist and success criteria
- `quickstart.md`: Implementation guide

**Assessment**: All artifacts align with rename scope. No new complexity introduced.

### Constitution Compliance Confirmed

✅ **Precision Over Approximation**: Design maintains exact structural queries. Graph schema unchanged.

✅ **Language Agnostic Foundation**: No changes to parser framework or language support.

✅ **Structural Focus**: Rename does not affect structural query capabilities.

✅ **Multiple Indexing Targets**: Functionality preserved for both local and GitHub repo indexing.

✅ **MCP-First Integration**: All interfaces (MCP, HTTP, CLI) remain functional with updated naming only.

✅ **Quality Standards**: 100% test pass requirement enforced in success criteria and contracts.

✅ **Testing Requirements**: Comprehensive test validation required before merge (SC-001, quickstart steps).

✅ **Integration Contracts**: No breaking changes to MCP tools, HTTP endpoints, or CLI patterns.

### **FINAL GATE STATUS: ✅ PASSED**

No constitutional violations introduced during design phase. Ready to proceed to Phase 2 (tasks generation via `/speckit.tasks` command).

---

## Phase 2: Tasks Generation

**Note**: This plan ends here. The next step is to run `/speckit.tasks` to generate `tasks.md` from the design artifacts created in Phases 0 and 1.

The tasks generation command will:
1. Read this plan and all Phase 0-1 artifacts
2. Generate dependency-ordered implementation tasks
3. Create `specs/005-rename-to-weavr/tasks.md`
4. Enable execution via `/speckit.implement`
