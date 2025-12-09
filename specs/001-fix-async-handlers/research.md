# Research: Fix Async Handlers for Structural Query Tools

**Feature**: 001-fix-async-handlers
**Date**: 2025-12-09
**Status**: Complete

## Research Summary

This document consolidates findings from investigating the async/sync mismatch in structural query tool handlers.

---

## Research Question 1: Why are handlers failing?

### Decision
The MCP server's `call_tool()` function awaits all handlers (`result = await handler(**arguments)`), but the 7 structural query tool handlers are defined as synchronous functions. When Python tries to await a non-coroutine (the dict return value), it raises `TypeError: object dict can't be used in 'await' expression`.

### Rationale
- The MCP server at `codebase_rag/mcp/server.py:161` uses `await handler(**arguments)`
- Handlers registered by `create_*_tool()` functions are regular synchronous functions
- Synchronous functions return values immediately, not coroutines
- When you `await` a non-coroutine, Python raises TypeError

### Evidence

From `stress_test.py` test failures:
```
S1: FAILED - object dict can't be used in 'await' expression
S2: FAILED - object dict can't be used in 'await' expression
...
CONC1: FAILED - unhashable type: 'dict' (asyncio.gather receives dicts instead of coroutines)
```

From `codebase_rag/tools/structural_queries.py` (current sync handlers):
```python
def find_callers(  # <- Not async!
    function_name: str, max_depth: int = 1, include_paths: bool = True
) -> dict[str, Any]:
    return query_tool.execute(ingestor, function_name, max_depth, include_paths)
```

From `codebase_rag/mcp/server.py` (expects async):
```python
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    ...
    result = await handler(**arguments)  # <- Awaits the handler
```

### Alternatives Considered

1. **Make `call_tool()` check if handler is async before awaiting** - Rejected because:
   - Would require additional complexity in server code
   - Inconsistent API (some tools async, some sync)
   - Doesn't align with MCP server patterns

2. **Use `asyncio.to_thread()` to wrap sync handlers** - Rejected because:
   - Adds unnecessary thread pool overhead
   - Query execution is already fast (Memgraph queries)
   - Simpler to just make handlers async

---

## Research Question 2: What needs to change?

### Decision
Add `async` keyword to exactly 7 handler functions in `structural_queries.py`. No other files need modification.

### Rationale
- Handlers are the inner functions returned by `create_*_tool()` functions
- The `*Query.execute()` methods can remain synchronous (they do the actual work)
- Python allows calling sync functions from async context without issues
- Only the handler functions (the ones registered with MCPToolsRegistry) need the async keyword

### Files to Modify

| File | Function | Line Range |
|------|----------|------------|
| `structural_queries.py` | `find_callers` | ~554-567 |
| `structural_queries.py` | `dependency_analysis` | ~926-941 |
| `structural_queries.py` | `interface_implementations` | ~1229-1242 |
| `structural_queries.py` | `expert_mode_cypher` | ~1501-1516 |
| `structural_queries.py` | `call_graph_generator` | ~1835-1850 |
| `structural_queries.py` | `class_hierarchy` | ~2107-2122 |
| `structural_queries.py` | `module_exports` | ~2269-2281 |

### Code Pattern

Before:
```python
def find_callers(
    function_name: str, max_depth: int = 1, include_paths: bool = True
) -> dict[str, Any]:
    """..."""
    return query_tool.execute(ingestor, function_name, max_depth, include_paths)
```

After:
```python
async def find_callers(
    function_name: str, max_depth: int = 1, include_paths: bool = True
) -> dict[str, Any]:
    """..."""
    return query_tool.execute(ingestor, function_name, max_depth, include_paths)
```

### Alternatives Considered

1. **Modify `execute()` methods to be async** - Rejected because:
   - Unnecessary - the handler wrapper is the only interface to MCP
   - Would require more extensive changes
   - `execute()` doesn't do any I/O that benefits from async

---

## Research Question 3: Are there any callers expecting sync handlers?

### Decision
No. All handlers are only called through the MCP server, which expects async.

### Rationale
Analysis of the codebase shows:
1. `MCPToolsRegistry` stores handler references but doesn't call them directly
2. `stress_test.py` awaits handlers (expects async)
3. `server.py` awaits handlers (expects async)
4. No other code imports or calls these handlers directly

### Evidence

Searched for handler usage:
```bash
rg "find_callers|class_hierarchy|dependency_analysis|interface_implementations|expert_mode_cypher|call_graph_generator|module_exports" --type py
```

Results show handlers are only:
1. Defined in `structural_queries.py`
2. Registered in `tools.py` via `create_*_tool()` functions
3. Called in `server.py` and `stress_test.py` with `await`

### Alternatives Considered
None - this was a verification step, not a decision point.

---

## Research Question 4: What tests validate the fix?

### Decision
Use `stress_test.py` as the primary validation. All S1-S7, CONC1-4, E6-E15, and MCP4 tests should pass after the fix.

### Rationale
- `stress_test.py` is specifically designed to test all MCP tools
- It covers structural queries (S1-S7), concurrent operations (CONC1-4), and edge cases (E6-E15)
- Current failure rate ~37.7% should improve to ≥80%

### Test Categories

| Category | Tests | Current Status | Expected After Fix |
|----------|-------|----------------|-------------------|
| Structural Queries | S1-S7 | 0/7 PASS | 7/7 PASS |
| Concurrent Ops | CONC1-CONC4 | 0/4 PASS | 4/4 PASS |
| Edge Cases | E6-E15 | 0/10 PASS | 10/10 PASS |
| MCP Integration | MCP4 | 0/1 PASS | 1/1 PASS |
| Project Isolation | ISO1-ISO3 | Varies | All PASS |

### Validation Command
```bash
uv run stress_test.py
```

---

## Resolved Clarifications

All technical questions have been resolved through codebase analysis. No external dependencies or architectural decisions required.

| Question | Resolution |
|----------|------------|
| Where are handlers defined? | `codebase_rag/tools/structural_queries.py`, inside `create_*_tool()` functions |
| How are handlers called? | `await handler(**arguments)` in `codebase_rag/mcp/server.py:161` |
| What's the expected return type? | `dict[str, Any]` (unchanged) |
| Are there sync callers? | No, all callers use `await` |
