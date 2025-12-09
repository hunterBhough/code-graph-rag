# Quickstart: Fix Async Handlers for Structural Query Tools

**Feature**: 001-fix-async-handlers
**Date**: 2025-12-09
**Status**: Ready for Implementation

## Quick Summary

Add `async` keyword to 7 handler functions in `structural_queries.py` to fix MCP server await errors.

---

## Prerequisites

- Python 3.12+
- Memgraph running on `localhost:7687`
- Repository indexed (for testing)

---

## Implementation Steps

### Step 1: Locate the File

```bash
# Target file
codebase_rag/tools/structural_queries.py
```

### Step 2: Modify Each Handler

Find each `create_*_tool()` function and add `async` to the inner handler function.

#### 2.1 find_callers (~line 554)

```python
# Before
def find_callers(
    function_name: str, max_depth: int = 1, include_paths: bool = True
) -> dict[str, Any]:

# After
async def find_callers(
    function_name: str, max_depth: int = 1, include_paths: bool = True
) -> dict[str, Any]:
```

#### 2.2 dependency_analysis (~line 926)

```python
# Before
def dependency_analysis(
    target: str,
    dependency_type: Literal["imports", "calls", "all"] = "all",
    include_transitive: bool = False,
) -> dict[str, Any]:

# After
async def dependency_analysis(
    target: str,
    dependency_type: Literal["imports", "calls", "all"] = "all",
    include_transitive: bool = False,
) -> dict[str, Any]:
```

#### 2.3 interface_implementations (~line 1229)

```python
# Before
def interface_implementations(
    interface_name: str,
    include_indirect: bool = False,
) -> dict[str, Any]:

# After
async def interface_implementations(
    interface_name: str,
    include_indirect: bool = False,
) -> dict[str, Any]:
```

#### 2.4 expert_mode_cypher (~line 1501)

```python
# Before
def expert_mode_cypher(
    query: str,
    parameters: dict[str, Any] | None = None,
    limit: int = 50,
) -> dict[str, Any]:

# After
async def expert_mode_cypher(
    query: str,
    parameters: dict[str, Any] | None = None,
    limit: int = 50,
) -> dict[str, Any]:
```

#### 2.5 call_graph_generator (~line 1835)

```python
# Before
def call_graph_generator(
    entry_point: str,
    max_depth: int = 3,
    max_nodes: int = 50,
) -> dict[str, Any]:

# After
async def call_graph_generator(
    entry_point: str,
    max_depth: int = 3,
    max_nodes: int = 50,
) -> dict[str, Any]:
```

#### 2.6 class_hierarchy (~line 2107)

```python
# Before
def class_hierarchy(
    class_name: str,
    direction: Literal["up", "down", "both"] = "both",
    max_depth: int = 10,
) -> dict[str, Any]:

# After
async def class_hierarchy(
    class_name: str,
    direction: Literal["up", "down", "both"] = "both",
    max_depth: int = 10,
) -> dict[str, Any]:
```

#### 2.7 module_exports (~line 2269)

```python
# Before
def module_exports(
    module_name: str, include_private: bool = False
) -> dict[str, Any]:

# After
async def module_exports(
    module_name: str, include_private: bool = False
) -> dict[str, Any]:
```

---

## Validation

### Run Stress Test

```bash
uv run stress_test.py
```

### Expected Results

| Test Category | Before | After |
|---------------|--------|-------|
| Structural (S1-S7) | 0/7 | 7/7 |
| Concurrent (CONC1-4) | 0/4 | 4/4 |
| Edge Cases (E6-E15) | 0/10 | 10/10 |
| Overall Pass Rate | ~37.7% | ≥80% |

---

## Verification Checklist

- [ ] All 7 handlers have `async def` instead of `def`
- [ ] No other code changes required
- [ ] Stress test S1-S7 pass
- [ ] Stress test CONC1-4 pass
- [ ] MCP server can invoke all structural query tools

---

## Common Issues

### Issue: "object dict can't be used in 'await' expression"

**Cause**: Handler is still defined as `def` instead of `async def`
**Fix**: Ensure `async` keyword is added before `def`

### Issue: "unhashable type: 'dict'"

**Cause**: `asyncio.gather()` receiving dict instead of coroutine
**Fix**: Same as above - handler must be async to return coroutine

---

## Files Changed

| File | Change |
|------|--------|
| `codebase_rag/tools/structural_queries.py` | Add `async` to 7 handler functions |

**Total lines changed**: ~7 (one word per function)
