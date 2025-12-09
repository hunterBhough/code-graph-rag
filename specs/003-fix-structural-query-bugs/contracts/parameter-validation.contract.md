# Contract: Parameter Validation

**Type**: Behavioral Contract
**Feature**: 003-fix-structural-query-bugs
**Status**: Required

## Purpose

This contract defines the parameter validation behavior that all structural query tools MUST implement to achieve 100% test pass rate.

---

## Contract 1: Numeric Range Validation

**Applies to**: `max_depth`, `max_nodes`, `limit` parameters

### Requirements

**MUST validate** that numeric parameters fall within documented ranges:
- `query_callers.max_depth`: 1-5
- `query_hierarchy.max_depth`: 1-10
- `query_call_graph.max_depth`: 1-5
- `query_call_graph.max_nodes`: 1-100
- `query_cypher.limit`: 1-1000

**MUST reject** out-of-range values with error response:
```json
{
  "error": "<parameter> must be between <min> and <max> (got <value>)",
  "error_code": "INVALID_PARAMETER",
  "suggestion": "Use <parameter>=<recommended_value> for typical use cases",
  "provided_input": {
    "<parameter>": <value>,
    "...": "..."
  }
}
```

### Test Cases

```python
# TC-PV-01: max_depth too high
await query_callers(function_name="valid.function", max_depth=999)
# MUST return error with error_code="INVALID_PARAMETER"

# TC-PV-02: max_depth negative
await query_callers(function_name="valid.function", max_depth=-1)
# MUST return error with error_code="INVALID_PARAMETER"

# TC-PV-03: max_depth at boundary (valid)
await query_callers(function_name="valid.function", max_depth=5)
# MUST execute successfully (boundary value is valid)

# TC-PV-04: limit too high
await query_cypher(query="MATCH (n) RETURN n", limit=9999)
# MUST return error with error_code="INVALID_PARAMETER"
```

---

## Contract 2: Enum Validation

**Applies to**: `direction`, `dependency_type` parameters

### Requirements

**MUST validate** that enum parameters match allowed values:
- `query_hierarchy.direction`: "up", "down", or "both"
- `query_dependencies.dependency_type`: "imports", "calls", or "all"

**MUST reject** invalid enum values with error response:
```json
{
  "error": "Invalid <parameter> parameter. Must be <value1>, <value2>, or <value3>",
  "error_code": "INVALID_PARAMETER",
  "suggestion": "Use <parameter>='<default>' for typical use cases",
  "provided_input": {
    "<parameter>": "<invalid_value>",
    "...": "..."
  }
}
```

### Test Cases

```python
# TC-PV-05: direction invalid
await query_hierarchy(class_name="valid.Class", direction="sideways")
# MUST return error with error_code="INVALID_PARAMETER"

# TC-PV-06: dependency_type invalid
await query_dependencies(target="valid.module", dependency_type="invalid_type")
# MUST return error with error_code="INVALID_PARAMETER"

# TC-PV-07: direction valid enum
await query_hierarchy(class_name="valid.Class", direction="up")
# MUST execute successfully
```

---

## Contract 3: Non-Empty String Validation

**Applies to**: `function_name`, `class_name`, `module_name`, `target`, `interface_name`, `entry_point`, `query` parameters

### Requirements

**MUST validate** that required string parameters are non-empty:
- Empty string `""` MUST be rejected
- Whitespace-only string `"   "` MUST be rejected
- None value SHOULD be rejected (may be caught by type system)

**MUST reject** empty strings with error response:
```json
{
  "error": "<Entity> name cannot be empty",
  "error_code": "INVALID_PARAMETER",
  "suggestion": "Provide a fully qualified name (e.g., '<example>')",
  "provided_input": {
    "<parameter>": ""
  }
}
```

### Test Cases

```python
# TC-PV-08: Empty function_name
await query_callers(function_name="", max_depth=1)
# MUST return error with error_code="INVALID_PARAMETER"

# TC-PV-09: Whitespace-only module_name
await query_module_exports(module_name="   ")
# MUST return error with error_code="INVALID_PARAMETER"

# TC-PV-10: None function_name
await query_callers(function_name=None, max_depth=1)
# MUST raise TypeError or return INVALID_PARAMETER error
```

---

## Contract 4: Expert Mode Security Validation

**Applies to**: `query_cypher` tool only

### Requirements

**MUST block** Cypher queries containing write operations:
- CREATE (node/relationship creation)
- DELETE (node/relationship deletion)
- DETACH DELETE (node deletion with relationships)
- SET (property modification)
- MERGE (conditional creation)
- DROP (index/constraint removal)
- CREATE INDEX (index creation)
- CREATE CONSTRAINT (constraint creation)

**MUST detect** keywords case-insensitively (CREATE, create, Create)

**MUST reject** forbidden operations with error response:
```json
{
  "error": "Destructive operation '<OPERATION>' is not allowed in expert mode",
  "error_code": "FORBIDDEN_OPERATION",
  "suggestion": "Expert mode is read-only. Use MATCH, RETURN, WHERE, ORDER BY, LIMIT for queries.",
  "provided_input": {
    "query": "<truncated_query>"
  }
}
```

### Test Cases

```python
# TC-PV-11: CREATE operation
await query_cypher(query="CREATE (n:TestNode) RETURN n")
# MUST return error with error_code="FORBIDDEN_OPERATION"

# TC-PV-12: DELETE operation
await query_cypher(query="MATCH (n) DELETE n")
# MUST return error with error_code="FORBIDDEN_OPERATION"

# TC-PV-13: SET operation
await query_cypher(query="MATCH (n) SET n.foo = 'bar'")
# MUST return error with error_code="FORBIDDEN_OPERATION"

# TC-PV-14: MERGE operation
await query_cypher(query="MERGE (n:Test) RETURN n")
# MUST return error with error_code="FORBIDDEN_OPERATION"

# TC-PV-15: Read-only query (valid)
await query_cypher(query="MATCH (n:Function) RETURN n.name LIMIT 10")
# MUST execute successfully
```

---

## Contract 5: Validation Timing

**Applies to**: All query tools

### Requirements

**MUST validate** parameters BEFORE executing any database queries.

**MUST complete** validation in <1ms (sub-millisecond overhead).

**MUST NOT** impact query performance targets:
- Simple queries: <50ms total (including validation)
- Complex queries: <150ms total (including validation)

### Test Cases

```python
# TC-PV-16: Validation prevents database query
# Mock database to verify no query sent when validation fails
with patch('ingestor.execute_structural_query') as mock_query:
    await query_callers(function_name="valid.function", max_depth=999)
    # MUST NOT call mock_query (validation rejected before query)
    mock_query.assert_not_called()
```

---

## Success Criteria

This contract is satisfied when:

1. ✅ All 15+ parameter validation tests (TC-PV-01 through TC-PV-16) pass
2. ✅ Stress test pass rate reaches 100% (all P1-P15 tests pass)
3. ✅ Error responses follow standardized format consistently
4. ✅ Validation overhead <1ms per query
5. ✅ No database queries executed for invalid parameters

---

## Implementation Checklist

- [ ] `query_callers`: Validate max_depth (1-5), function_name (non-empty)
- [ ] `query_hierarchy`: Validate direction (enum), max_depth (1-10), class_name (non-empty)
- [ ] `query_dependencies`: Validate dependency_type (enum), target (non-empty)
- [ ] `query_implementations`: Validate interface_name (non-empty)
- [ ] `query_call_graph`: Validate max_depth (1-5), max_nodes (1-100), entry_point (non-empty)
- [ ] `query_module_exports`: Validate module_name (non-empty)
- [ ] `query_cypher`: Validate query (non-empty), limit (1-1000), block forbidden operations
- [ ] All validation errors use `create_error_response()` helper
- [ ] All validation occurs before database queries
- [ ] Stress test suite updated with comprehensive validation tests
