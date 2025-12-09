# Handler Function Interface Contract

**Feature**: 001-fix-async-handlers
**Date**: 2025-12-09
**Status**: Complete

## Overview

This contract defines the interface for structural query tool handler functions after the async fix.

---

## Handler Function Signature

### Before (Broken)

```python
def handler_name(
    required_param: str,
    optional_param: Type = default_value,
) -> dict[str, Any]:
    """Handler docstring."""
    return query_tool.execute(...)
```

### After (Fixed)

```python
async def handler_name(
    required_param: str,
    optional_param: Type = default_value,
) -> dict[str, Any]:
    """Handler docstring."""
    return query_tool.execute(...)
```

---

## Affected Handlers

### 1. find_callers

```python
async def find_callers(
    function_name: str,
    max_depth: int = 1,
    include_paths: bool = True,
) -> dict[str, Any]:
    """Find all functions that call a specified target function."""
```

### 2. class_hierarchy

```python
async def class_hierarchy(
    class_name: str,
    direction: Literal["up", "down", "both"] = "both",
    max_depth: int = 10,
) -> dict[str, Any]:
    """Explore class inheritance hierarchies."""
```

### 3. dependency_analysis

```python
async def dependency_analysis(
    target: str,
    dependency_type: Literal["imports", "calls", "all"] = "all",
    include_transitive: bool = False,
) -> dict[str, Any]:
    """Analyze module or function dependencies."""
```

### 4. interface_implementations

```python
async def interface_implementations(
    interface_name: str,
    include_indirect: bool = False,
) -> dict[str, Any]:
    """Find all classes that implement an interface or extend a base class."""
```

### 5. expert_mode_cypher

```python
async def expert_mode_cypher(
    query: str,
    parameters: dict[str, Any] | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Execute a custom Cypher query against the code knowledge graph."""
```

### 6. call_graph_generator

```python
async def call_graph_generator(
    entry_point: str,
    max_depth: int = 3,
    max_nodes: int = 50,
) -> dict[str, Any]:
    """Generate a call graph starting from an entry point function."""
```

### 7. module_exports

```python
async def module_exports(
    module_name: str,
    include_private: bool = False,
) -> dict[str, Any]:
    """Retrieve all public exports from a module."""
```

---

## Usage Contract

### Calling Convention

```python
# Correct usage (from MCP server)
result = await handler(**arguments)

# Correct usage (from stress test)
result = await handler(function_name="my_function")

# Incorrect usage (will return coroutine, not result)
result = handler(function_name="my_function")  # BAD: result is coroutine
```

### Return Value Structure

All handlers return the same structure:

```python
{
    "query": str,            # Description of the query executed
    "results": list[dict],   # Query results
    "metadata": {
        "row_count": int,
        "total_count": int,
        "truncated": bool,
        "execution_time_ms": float,
        "query_type": str,
    }
}
```

Or on error:

```python
{
    "error": str,
    "error_code": str,
    "suggestion": str | None,
    "provided_input": dict | None,
}
```

---

## Backward Compatibility

| Aspect | Compatibility |
|--------|---------------|
| Return type | ✅ Unchanged (`dict[str, Any]`) |
| Parameters | ✅ Unchanged |
| Error responses | ✅ Unchanged |
| MCP schema | ✅ Unchanged |

The only change is the calling convention: handlers must now be awaited.
