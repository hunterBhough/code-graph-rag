# Implementation Plan: Fix Async Handlers for Structural Query Tools

**Branch**: `001-fix-async-handlers` | **Date**: 2025-12-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-fix-async-handlers/spec.md`

## Summary

Convert 7 synchronous structural query tool handler functions to async functions to fix "object dict can't be used in 'await' expression" errors when the MCP server awaits these handlers. The fix is straightforward: add `async` keyword to each handler function definition while keeping the return type (`dict[str, Any]`) unchanged.

## Technical Context

**Language/Version**: Python 3.12+ (requires-python >= 3.12)
**Primary Dependencies**: mcp>=1.21.1, pymgclient>=1.4.0, loguru>=0.7.3, pydantic-ai-slim>=0.2.18
**Storage**: Memgraph (graph database at localhost:7687)
**Testing**: pytest, stress_test.py (primary validation)
**Target Platform**: Linux/macOS server (MCP stdio transport)
**Project Type**: Single project (Python package)
**Performance Goals**: Stress test pass rate ≥80% (currently 37.7%)
**Constraints**: Handlers must be awaitable by MCP server's `call_tool()` method
**Scale/Scope**: 7 handler functions to modify, 23 failing tests to fix

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Check (Phase 0)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Graph-First Intelligence | ✅ PASS | Query handlers access Memgraph via ingestor, no changes to graph access patterns |
| II. Multi-Language Universality | ✅ N/A | No language support changes |
| III. AI-Native Interface | ✅ PASS | Fix ensures MCP tools work correctly for AI consumption |
| IV. Parse Precision | ✅ N/A | No parser changes |
| V. Safe Code Operations | ✅ N/A | All handlers are read-only queries |

**Pre-Design Gate Result**: ✅ PASS - All applicable principles satisfied

### Post-Design Check (Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Graph-First Intelligence | ✅ PASS | Design confirms no changes to graph queries or access patterns |
| II. Multi-Language Universality | ✅ N/A | Design confirms no language parser changes |
| III. AI-Native Interface | ✅ PASS | Design ensures all MCP tools remain awaitable with unchanged response formats |
| IV. Parse Precision | ✅ N/A | Design confirms no AST/parser changes |
| V. Safe Code Operations | ✅ N/A | Design confirms all handlers remain read-only |

**Post-Design Gate Result**: ✅ PASS - Design validated against all principles

## Project Structure

### Documentation (this feature)

```text
specs/001-fix-async-handlers/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
codebase_rag/
├── mcp/
│   ├── __init__.py
│   ├── server.py         # MCP server (call_tool awaits handlers)
│   └── tools.py          # MCPToolsRegistry (unchanged)
├── tools/
│   └── structural_queries.py  # TARGET: 7 handler functions to fix
└── services/
    └── graph_service.py  # MemgraphIngestor (unchanged)

# Tests
stress_test.py            # Primary validation (S1-S7, CONC1-4, E6-15)
```

**Structure Decision**: Single project layout. All changes are isolated to `codebase_rag/tools/structural_queries.py` where the 7 handler functions are defined.

## Complexity Tracking

> No constitution violations to justify - this is a minimal fix.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Affected Components

### Files to Modify

1. **`codebase_rag/tools/structural_queries.py`** - Add `async` to 7 handler functions:
   - `find_callers()` (line ~554-567)
   - `class_hierarchy()` (line ~2107-2122)
   - `dependency_analysis()` (line ~926-941)
   - `interface_implementations()` (line ~1229-1242)
   - `expert_mode_cypher()` (line ~1501-1516)
   - `call_graph_generator()` (line ~1835-1850)
   - `module_exports()` (line ~2269-2281)

### Files NOT Modified

- `codebase_rag/mcp/tools.py` - MCPToolsRegistry already stores handlers, no changes needed
- `codebase_rag/mcp/server.py` - Already uses `await handler(**arguments)` correctly
- `*Query` classes (FindCallersQuery, etc.) - Execute methods stay synchronous

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Async handler breaks sync callers | Low | Medium | No sync callers exist - all calls via MCP server |
| Performance regression | Very Low | Low | Adding async to sync code has negligible overhead |
| Incomplete fix (missing handlers) | Low | High | Stress test validates all 7 tools |

## Validation Plan

1. **Pre-fix baseline**: Run `uv run stress_test.py`, expect ~37.7% pass rate
2. **Post-fix validation**: Run `uv run stress_test.py`, expect ≥80% pass rate
3. **Specific tests to verify**:
   - S1-S7 (structural queries): All should pass
   - CONC1-CONC4 (concurrent operations): All should pass
   - E6-E15 (edge cases with async): All should pass
   - MCP4 (return type consistency): Should pass
