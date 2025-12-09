# Contract: Query Correctness

**Type**: Behavioral Contract
**Feature**: 003-fix-structural-query-bugs
**Status**: Required

## Purpose

This contract defines the correctness requirements for Cypher queries and test data to achieve 100% test pass rate by fixing bugs in query logic and test assertions.

---

## Contract 1: Module Exports Query Sorting

**Applies to**: `query_module_exports` tool

### Current Bug

The query attempts to sort by `labels(export)` which returns a list, causing Cypher error:
```
"Comparison is not defined for values of type list"
```

### Requirements

**MUST fix** ORDER BY clause to handle label lists correctly.

**Option 1**: Extract first label for sorting
```cypher
ORDER BY labels(export)[0], short_name
```

**Option 2**: Remove ORDER BY entirely (results still valid, just unsorted)
```cypher
-- No ORDER BY clause
```

**MUST return** all exports without Cypher errors.

**MUST respect** `include_private` parameter filtering.

### Test Cases

```python
# TC-QC-01: Module exports with mixed types (functions + classes)
await query_module_exports(
    module_name="ai-gateway-mcp.src.core.router",
    include_private=False
)
# MUST return results without Cypher errors
# MUST include all public functions and classes
# MUST NOT include private members (names starting with _)

# TC-QC-02: Module exports including private members
await query_module_exports(
    module_name="ai-gateway-mcp.src.core.router",
    include_private=True
)
# MUST return results without Cypher errors
# MUST include private members (names starting with _)

# TC-QC-03: Empty module (no exports)
await query_module_exports(module_name="ai-gateway-mcp.empty.module")
# MUST return 0 results without errors
# MUST distinguish from non-existent module (which should raise NodeNotFoundError)
```

---

## Contract 2: Target Existence Verification

**Applies to**: All structural query tools

### Requirements

**MUST verify** target entity exists in graph when query returns 0 results.

**MUST distinguish** between:
- **Legitimate empty results**: Target exists but has no relationships (return 0 results)
- **Non-existent target**: Target doesn't exist in graph (raise NodeNotFoundError)

**MUST use** two-phase query pattern:
```python
# Phase 1: Execute main query
results = execute_structural_query(main_query, params)

# Phase 2: If 0 results, verify target exists
if not results:
    check_query = "MATCH (n:<NodeType> {qualified_name: $name}) RETURN n"
    exists = ingestor.fetch_all(check_query, {"name": target_name})
    if not exists:
        raise NodeNotFoundError(target_name, "<NodeType>")
    # If we reach here, 0 results is legitimate
```

### Test Cases

```python
# TC-QC-04: Function with no callers (legitimate empty result)
await query_callers(
    function_name="ai-gateway-mcp.src.utils.leaf_function"
)
# MUST return 0 results without error (function exists but has no callers)
# MUST NOT raise NodeNotFoundError

# TC-QC-05: Non-existent function
await query_callers(function_name="ai-gateway-mcp.nonexistent.function")
# MUST return error with error_code="NODE_NOT_FOUND"
# MUST suggest checking qualified name or re-indexing

# TC-QC-06: Class with no subclasses (legitimate empty result)
await query_hierarchy(
    class_name="ai-gateway-mcp.src.models.LeafClass",
    direction="down"
)
# MUST return 0 descendants without error
```

---

## Contract 3: Qualified Name Accuracy

**Applies to**: All structural query tools and stress tests

### Requirements

**MUST use** correct qualified name format:
```
{project_name}.{module_path}.{entity_name}
```

**MUST match** the actual qualified names stored in Memgraph graph.

**MUST verify** test project is indexed before running tests:
```python
check_query = """
MATCH (p:Project {name: $project_name})-[:CONTAINS]->(n)
RETURN count(n) AS node_count
"""
result = ingestor.fetch_all(check_query, {"project_name": "ai-gateway-mcp"})
if result[0]["node_count"] == 0:
    raise ValueError("Test project not indexed")
```

### Test Cases

```python
# TC-QC-07: Verify test project is indexed
# Before running any stress tests:
node_count = await get_project_node_count("ai-gateway-mcp")
# MUST have node_count > 0

# TC-QC-08: Query with correct qualified name
await query_callers(
    function_name="ai-gateway-mcp.scripts.benchmark.main"  # Correct format
)
# MUST return results (if callers exist) or legitimate empty result

# TC-QC-09: Query with incorrect qualified name
await query_callers(
    function_name="ai_gateway_mcp.scripts.benchmark.main"  # Wrong: underscore instead of dash
)
# MUST return NODE_NOT_FOUND error (name doesn't match indexed format)
```

---

## Contract 4: Dependency Query Aggregation

**Applies to**: `query_dependencies` with `dependency_type="all"`

### Current Bug

The query may not correctly combine results from both "imports" and "calls" queries when `dependency_type="all"`.

### Requirements

**MUST query** both import and call dependencies separately.

**MUST combine** results from both queries into unified result set.

**MUST deduplicate** if same dependency appears in both queries.

**MUST return** aggregated results with correct metadata:
```python
{
  "imports": [...],      # Import dependencies
  "calls": [...],        # Call dependencies
  "dependency_graph": {  # Combined adjacency list
    "target": ["dep1", "dep2", ...]
  },
  "metadata": {
    "row_count": len(imports) + len(calls),  # Total combined
    ...
  }
}
```

### Test Cases

```python
# TC-QC-10: Dependencies with type="imports"
await query_dependencies(
    target="ai-gateway-mcp.src.core.router",
    dependency_type="imports"
)
# MUST return only import dependencies
# MUST have imports populated, calls empty

# TC-QC-11: Dependencies with type="calls"
await query_dependencies(
    target="ai-gateway-mcp.src.core.router.handle_request",
    dependency_type="calls"
)
# MUST return only call dependencies
# MUST have calls populated, imports empty

# TC-QC-12: Dependencies with type="all"
await query_dependencies(
    target="ai-gateway-mcp.src.core.router",
    dependency_type="all"
)
# MUST return both import AND call dependencies
# MUST have both imports and calls populated
# MUST aggregate row_count = len(imports) + len(calls)
```

---

## Contract 5: Test Assertion Logic

**Applies to**: Stress test suite

### Requirements

**MUST update** test assertions to distinguish:
- **"pass"**: Expected behavior occurred (results found, or legitimate empty result)
- **"fail"**: Unexpected error or behavior (bug detected)
- **"partial"**: REMOVE this status entirely (was indicating bugs, now should be "pass" or "fail")

**MUST verify** assumptions before asserting:
```python
# Bad assertion (current):
if row_count == 0:
    status = "partial"  # Assumes 0 results = bug

# Good assertion (fixed):
if "error_code" == "NODE_NOT_FOUND":
    status = "fail"  # Test data missing
elif row_count == 0:
    status = "pass"  # Legitimate empty result (function exists but has no callers)
elif row_count > 0:
    status = "pass"  # Found relationships as expected
```

### Test Cases

```python
# TC-QC-13: Stress test with legitimate empty result
# Test a function known to have no callers
result = await query_callers(function_name="ai-gateway-mcp.src.utils.unused_function")
# Stress test MUST mark as "pass" (not "partial")

# TC-QC-14: Stress test with missing test data
# Test a function that should exist but doesn't (bad test data)
result = await query_callers(function_name="ai-gateway-mcp.nonexistent.function")
# Stress test MUST mark as "fail" (not "partial")

# TC-QC-15: Stress test with found relationships
# Test a function with known callers
result = await query_callers(function_name="ai-gateway-mcp.src.core.router.handle_request")
# Stress test MUST mark as "pass" if row_count > 0
```

---

## Success Criteria

This contract is satisfied when:

1. ✅ Module exports query executes without Cypher errors
2. ✅ All queries verify target existence before raising NODE_NOT_FOUND
3. ✅ All test qualified names match indexed data
4. ✅ Dependency "all" type correctly aggregates imports + calls
5. ✅ Stress test assertions distinguish pass/fail correctly (0 "partial" results)
6. ✅ All 50 stress tests achieve "pass" status

---

## Implementation Checklist

- [ ] Fix module_exports ORDER BY clause (use labels()[0] or remove)
- [ ] Add target existence verification to all query tools
- [ ] Verify test project indexed before stress tests run
- [ ] Update test qualified names to match actual indexed data
- [ ] Fix dependency_analysis "all" type to combine results correctly
- [ ] Update stress test assertions to eliminate "partial" status
- [ ] Add pre-flight check for test project node count
- [ ] Document known functions with no callers for negative test cases
