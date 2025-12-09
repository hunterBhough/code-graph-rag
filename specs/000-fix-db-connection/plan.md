# Implementation Plan: Fix Database Connection Architecture

**Branch**: `001-fix-db-connection` | **Date**: 2025-12-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-fix-db-connection/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature adds multi-database support to the MemgraphIngestor class, enabling isolated database contexts for multiple projects and test environments. The primary requirement is to support the `USE DATABASE` command in Memgraph, allowing the system to switch database contexts immediately after connection establishment. This resolves stress test failures where queries could not execute against named databases (e.g., `codegraph_code-graph-rag`), currently resulting in 21 out of 26 tests failing with "Not connected to Memgraph" errors.

## Technical Context

**Language/Version**: Python 3.14.2 (requires-python >= 3.12)
**Primary Dependencies**: pymgclient 1.4.0, loguru 0.7.3, pydantic-settings 2.0.0
**Storage**: Memgraph graph database (via mgclient connection, host:port 7687)
**Testing**: pytest 8.4.1 with pytest-asyncio 1.0.0
**Target Platform**: Linux/macOS servers with Memgraph Docker container
**Project Type**: Single Python package (codebase_rag) with MCP server interface
**Performance Goals**: Database switching < 100ms, support concurrent test execution
**Constraints**: Memgraph `USE DATABASE` command compatibility, environment variable config pattern
**Scale/Scope**: 300+ files indexed, 2300+ graph nodes, support 5-10 concurrent databases per Memgraph instance

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principles Alignment

**I. Graph-First Intelligence**: ✅ PASS
- This feature enhances graph access by enabling proper database context switching
- All queries continue to flow through the graph database
- Does not bypass or circumvent the graph as authoritative source

**II. Multi-Language Universality**: ✅ N/A
- No language-specific changes required
- Graph schema remains unchanged

**III. AI-Native Interface**: ✅ PASS
- MCP tools continue to access the graph through MemgraphIngestor
- Transparent to AI consumers - no API changes to MCP tools
- Enables proper testing and validation of MCP tool responses

**IV. Parse Precision**: ✅ N/A
- No parser changes required
- AST extraction remains Tree-sitter-based

**V. Safe Code Operations**: ✅ PASS
- Read-only infrastructure change (connection management)
- No file writes or code modifications involved
- Isolated database contexts improve safety by preventing cross-project interference

### Technical Standards Compliance

**Database Requirements**: ✅ PASS
- Memgraph remains the required graph database
- Preserves per-project database naming: `codegraph_<project-name>`
- Maintains group-level database support: `codegraph_<group>`
- No changes to atomic graph update behavior

**Embedding Requirements**: ✅ N/A
- No changes to embedding storage or retrieval

**Configuration Standards**: ✅ PASS
- Uses `MEMGRAPH_DATABASE` environment variable (explicit config pattern)
- No hardcoded database names in source code
- Maintains existing provider configuration patterns

### Gate Status: ✅ APPROVED

No violations detected. This feature aligns with all applicable Core Principles and Technical Standards.

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

```text
codebase_rag/                     # Main Python package
├── services/
│   ├── graph_service.py          # MemgraphIngestor class (PRIMARY CHANGE)
│   └── llm.py
├── config.py                     # AppConfig settings (ADD MEMGRAPH_DATABASE)
├── embedder.py
├── vector_store.py
├── mcp/
│   └── tools.py                  # MCP tool registry (testing validation)
└── tests/                        # Test directory (NEW - per pyproject.toml)
    ├── unit/                     # Unit tests for MemgraphIngestor
    ├── integration/              # Integration tests with Memgraph
    └── fixtures/                 # Test fixtures and sample data

stress_test.py                    # Stress test harness (UPDATE to use database_name)
infrastructure/
├── registry/
│   └── projects.toon             # Project registry with database mappings
└── logs/                         # Group-level logs
```

**Structure Decision**: Single Python package architecture. Changes are localized to:
1. **codebase_rag/services/graph_service.py**: Add `database_name` parameter and `USE DATABASE` logic to MemgraphIngestor
2. **codebase_rag/config.py**: Add `MEMGRAPH_DATABASE` environment variable to AppConfig
3. **stress_test.py**: Update to pass `database_name` parameter
4. **codebase_rag/tests/**: Create test directory structure (currently missing, referenced in pyproject.toml line 83)

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No constitutional violations detected.

## Post-Phase 1 Constitution Check

*Re-evaluation after design artifacts (research.md, data-model.md, contracts/, quickstart.md) completed.*

### Design Validation

**Graph-First Intelligence**: ✅ MAINTAINED
- Data model confirms all operations flow through graph database
- No alternative data access paths introduced
- Database isolation enhances graph reliability (prevents cross-contamination)

**AI-Native Interface**: ✅ MAINTAINED
- API contracts confirm MCP tools remain unchanged
- Transparent database switching preserves AI consumption patterns
- Test contracts verify MCP tool functionality with database contexts

**Safe Code Operations**: ✅ MAINTAINED
- Data model shows database switching occurs before any queries execute
- Clean error messages (FR-005) prevent confusion
- Isolation prevents accidental data corruption across projects

**Database Requirements**: ✅ MAINTAINED
- Database naming conventions preserved: `codegraph_<project-name>`
- Group-level databases remain supported
- Per-project isolation enhanced by explicit database contexts

**Configuration Standards**: ✅ MAINTAINED
- `MEMGRAPH_DATABASE` follows existing env var pattern
- No hardcoded values in implementation
- Backward compatible (database_name optional)

### Implementation Risks Identified

**Risk 1**: None - Design is straightforward, low-risk change
**Risk 2**: None - Backward compatibility ensures no breaking changes
**Risk 3**: None - Test coverage validates all edge cases

### Final Gate Status: ✅ APPROVED FOR IMPLEMENTATION

All constitutional principles maintained post-design. Ready to proceed to Phase 2 (tasks.md generation via `/speckit.tasks` command).
