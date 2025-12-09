# Implementation Plan: Fix Structural Query Bugs and Achieve 100% Test Pass Rate

**Branch**: `003-fix-structural-query-bugs` | **Date**: 2025-12-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-fix-structural-query-bugs/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Fix critical bugs in the structural query system to achieve 100% test pass rate (from current 68%). Add parameter validation to all query tools, block CREATE operations in expert mode, fix module_exports Cypher query sorting bug, and ensure accurate test data. This ensures the code-graph-rag MCP server provides reliable, secure, and consistent structural queries for AI-assisted code analysis.

## Technical Context

**Language/Version**: Python 3.12+ (requires-python >= 3.12)
**Primary Dependencies**: pymgclient 1.4.0 (Memgraph client), tree-sitter 0.25.0 (AST parsing), mcp 1.21.1+ (MCP protocol), pydantic-ai-slim 0.2.18+ (LLM integration), loguru 0.7.3 (logging), pytest 8.4.1+ (testing)
**Storage**: Memgraph Community Edition (graph database at localhost:7687), project-based isolation via CONTAINS relationships
**Testing**: pytest with stress test suite (50 tests across 5 categories: parameter validation, structural queries, edge cases, performance, concurrent operations)
**Target Platform**: Linux/macOS server (MCP server for Claude Code integration)
**Project Type**: Single project (Python package + MCP server)
**Performance Goals**: <50ms for simple queries, <150ms for complex traversals, maintain 0.40s total stress test execution time
**Constraints**: Read-only graph queries (no write operations), project isolation must be maintained, backward compatibility with existing MCP tool schemas
**Scale/Scope**: 7 structural query tools, 50 stress tests, support for codebases with 10K-100K nodes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principles Alignment

**I. Graph-First Intelligence** ✅
- All fixes target graph query correctness and reliability
- Parameter validation ensures queries produce valid Cypher
- No bypass of graph database for code analysis
- Maintains authoritative graph-based codebase understanding

**II. Multi-Language Universality** ✅
- Fixes apply to all supported languages uniformly
- No language-specific query logic introduced
- Schema consistency maintained across bug fixes
- Test improvements verify cross-language query patterns

**III. AI-Native Interface** ✅
- MCP tool interface remains primary AI access method
- Error messages structured for LLM consumption
- Tool schemas unchanged (backward compatible)
- Improved reliability benefits AI-assisted workflows

**IV. Parse Precision** ✅
- No changes to Tree-sitter parsing logic
- Graph data integrity preserved through read-only constraints
- AST-based code extraction unchanged
- Fixes ensure queries accurately reflect parsed structure

**V. Safe Code Operations** ✅
- Expert mode security hardened (block CREATE operations)
- Read-only enforcement strengthened
- No file system modifications
- Parameter validation prevents dangerous queries

### Technical Standards Compliance

**Database Requirements** ✅
- Memgraph remains the graph database
- Project-based isolation maintained
- No schema changes required
- Read-only query patterns preserved

**Testing Requirements** ✅
- Stress test suite expanded with parameter validation tests
- Coverage for all 7 structural query tools
- Edge case testing improved
- Performance regression tests included

### Gates Status

**PASS** - All core principles aligned, no violations. This is a bug fix and reliability improvement that strengthens constitution adherence without introducing complexity or architectural changes.

## Project Structure

### Documentation (this feature)

```text
specs/003-fix-structural-query-bugs/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
codebase_rag/
├── tools/
│   └── structural_queries.py    # Main file to modify (parameter validation, bug fixes)
├── services/
│   └── graph_service.py         # MemgraphIngestor (may need minor updates)
├── tests/
│   └── ...                      # Unit tests (if needed)

tests/stress/                     # Stress test suite (main focus)
├── __init__.py
├── base.py                      # Base test utilities
├── runner.py                    # Test runner
├── test_parameter_validation.py # Parameter validation tests (EXPAND)
├── test_structural_queries.py   # Structural query tests (FIX)
├── test_edge_cases.py           # Edge case tests (UPDATE)
├── test_performance.py          # Performance tests (MAINTAIN)
└── test_concurrent_operations.py # Concurrency tests (VERIFY)

mcp_server/
├── server.py                    # MCP server (reads tool definitions, no changes needed)
└── ...

stress_test.py                   # Main stress test runner
```

**Structure Decision**: Single Python project. This is a bug fix targeting existing structural query tools in `codebase_rag/tools/structural_queries.py` and expanding the stress test suite in `tests/stress/`. No new modules or architectural changes. All fixes are localized to parameter validation logic, Cypher query corrections, and test assertions.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations** - This feature does not introduce new complexity or violate any constitutional principles. It is a bug fix and reliability improvement that strengthens existing guarantees.
