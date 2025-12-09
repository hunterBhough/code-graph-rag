# Data Model: Fix Structural Query Bugs

**Feature**: 003-fix-structural-query-bugs
**Date**: 2025-12-09

## Overview

This feature is a bug fix that does not introduce new entities or change the graph schema. The data model documented here represents the **existing** structures that will be validated and corrected, not new additions.

---

## Graph Schema (Existing - No Changes)

The Memgraph graph database schema remains unchanged. This section documents the existing schema for reference during bug fixes.

### Node Types

```cypher
// Project node (for project isolation)
(:Project {
  name: String  // e.g., "ai-gateway-mcp"
})

// Code entities
(:Module {
  qualified_name: String,  // e.g., "ai-gateway-mcp.src.core.router"
  name: String,
  path: String,
  extension: String
})

(:Class {
  qualified_name: String,  // e.g., "ai-gateway-mcp.src.models.User"
  name: String,
  file_path: String,
  line_start: Integer,
  line_end: Integer,
  base_classes: List<String>
})

(:Function {
  qualified_name: String,  // e.g., "ai-gateway-mcp.src.utils.validate_input"
  name: String,
  file_path: String,
  line_start: Integer,
  line_end: Integer,
  decorators: List<String>
})

(:Method {
  qualified_name: String,  // e.g., "ai-gateway-mcp.src.models.User.save"
  name: String,
  class_name: String,
  file_path: String,
  line_start: Integer,
  line_end: Integer,
  decorators: List<String>
})
```

### Relationship Types

```cypher
// Project isolation
(Project)-[:CONTAINS]->(Module|Class|Function|Method)

// Code structure
(Module)-[:DEFINES]->(Function|Class|Method)
(Module)-[:IMPORTS]->(Module|ExternalPackage)

// Function relationships
(Function|Method)-[:CALLS]->(Function|Method)

// Class relationships
(Class)-[:INHERITS]->(Class)
(Class)-[:IMPLEMENTS]->(Class)
```

---

## Query Result Data Structures (Existing - Validated)

These are the existing result structures that will have improved validation and error handling.

### 1. StandardQueryResult

**Description**: Base result format for all structural queries

```python
{
  "query": str,                    # Human-readable query description
  "results": List[Dict[str, Any]], # Query result rows
  "metadata": {
    "row_count": int,              # Number of results returned
    "total_count": int,            # Total results before truncation
    "truncated": bool,             # Whether results were truncated
    "execution_time_ms": float,    # Query execution time
    "query_type": str              # "structural" or "expert_cypher"
  }
}
```

**Validation Rules**:
- `row_count` <= `total_count`
- `truncated` = True if `row_count` < `total_count`
- `execution_time_ms` >= 0

**State Transitions**: None (immutable result)

### 2. ErrorResponse

**Description**: Standardized error format for all validation and query failures

```python
{
  "error": str,                    # Human-readable error message
  "error_code": str,               # Error type code
  "suggestion": str | None,        # Optional resolution suggestion
  "provided_input": Dict[str, Any] | None  # Input that caused error
}
```

**Error Codes** (existing, will be used consistently):
- `INVALID_PARAMETER`: Parameter validation failure
- `FORBIDDEN_OPERATION`: Blocked write operation in expert mode
- `NODE_NOT_FOUND`: Target entity doesn't exist in graph
- `QUERY_TIMEOUT`: Query exceeded time limit
- `UNKNOWN_ERROR`: Unexpected error

**Validation Rules**:
- `error_code` must be one of defined codes
- `error` must be non-empty string
- `suggestion` should provide actionable guidance

### 3. ParameterConstraints (New Documentation)

**Description**: Defines valid parameter ranges for each query tool

```python
# query_callers
{
  "function_name": {
    "type": str,
    "constraints": ["non-empty"],
    "example": "ai-gateway-mcp.src.core.router.handle_request"
  },
  "max_depth": {
    "type": int,
    "constraints": ["range: 1-5"],
    "default": 1
  },
  "include_paths": {
    "type": bool,
    "default": True
  }
}

# query_hierarchy
{
  "class_name": {
    "type": str,
    "constraints": ["non-empty"],
    "example": "ai-gateway-mcp.src.models.BaseModel"
  },
  "direction": {
    "type": str,
    "constraints": ["enum: up, down, both"],
    "default": "both"
  },
  "max_depth": {
    "type": int,
    "constraints": ["range: 1-10"],
    "default": 10
  }
}

# query_dependencies
{
  "target": {
    "type": str,
    "constraints": ["non-empty"],
    "example": "ai-gateway-mcp.src.services.auth"
  },
  "dependency_type": {
    "type": str,
    "constraints": ["enum: imports, calls, all"],
    "default": "all"
  },
  "include_transitive": {
    "type": bool,
    "default": False
  }
}

# query_implementations
{
  "interface_name": {
    "type": str,
    "constraints": ["non-empty"],
    "example": "ai-gateway-mcp.src.interfaces.PaymentProvider"
  },
  "include_indirect": {
    "type": bool,
    "default": False
  }
}

# query_call_graph
{
  "entry_point": {
    "type": str,
    "constraints": ["non-empty"],
    "example": "ai-gateway-mcp.src.main.app"
  },
  "max_depth": {
    "type": int,
    "constraints": ["range: 1-5"],
    "default": 3
  },
  "max_nodes": {
    "type": int,
    "constraints": ["range: 1-100"],
    "default": 50
  }
}

# query_module_exports
{
  "module_name": {
    "type": str,
    "constraints": ["non-empty"],
    "example": "ai-gateway-mcp.src.utils.validation"
  },
  "include_private": {
    "type": bool,
    "default": False
  }
}

# query_cypher (expert mode)
{
  "query": {
    "type": str,
    "constraints": ["non-empty", "no CREATE/DELETE/SET/MERGE"],
    "example": "MATCH (f:Function) WHERE f.name CONTAINS 'auth' RETURN f.qualified_name LIMIT 10"
  },
  "parameters": {
    "type": Dict[str, Any],
    "default": {}
  },
  "limit": {
    "type": int,
    "constraints": ["range: 1-1000"],
    "default": 50
  }
}
```

**Validation Strategy**:
1. Type checking (Python type hints)
2. Constraint checking (ranges, enums, non-empty)
3. Early rejection before database queries
4. Standardized error responses

---

## Test Result Data Structures (Existing - Enhanced)

### TestResult

**Description**: Individual stress test outcome

```python
{
  "test_id": str,                  # e.g., "P1", "S3", "E5"
  "status": str,                   # "pass", "fail", "partial"
  "execution_time_ms": float,
  "handled_gracefully": bool,      # For error tests
  "error_message": str | None,
  "notes": str                     # Test description/context
}
```

**Status Definitions**:
- **pass**: Test succeeded, expected behavior observed
- **fail**: Test failed, unexpected behavior or error
- **partial**: Test completed but results unexpected (e.g., 0 results when relationships should exist)

**Validation Rules**:
- `status` must be one of: "pass", "fail", "partial"
- `execution_time_ms` >= 0
- If `status == "fail"`, `error_message` should be populated
- For parameter validation tests, `handled_gracefully` indicates whether error was caught properly

### TestSummary

**Description**: Aggregate test results across all categories

```python
{
  "total_tests": int,
  "passed": int,
  "failed": int,
  "partial": int,
  "pass_rate": float,              # percentage (0-100)
  "total_time_ms": float,
  "categories": {
    "parameter_validation": {
      "total": int,
      "passed": int,
      "failed": int,
      "partial": int
    },
    "structural_queries": { ... },
    "edge_cases": { ... },
    "performance": { ... },
    "concurrent_operations": { ... }
  }
}
```

**Success Criteria** (from spec):
- `pass_rate` >= 100% (all tests pass)
- `failed` == 0
- `partial` == 0 (all partial tests fixed)
- `total_time_ms` < 1000 (maintain fast execution)

---

## Forbidden Operation Patterns (Expert Mode)

**Description**: Cypher keywords that must be blocked in expert mode

```python
FORBIDDEN_OPERATIONS = {
  "CREATE": {
    "pattern": r"\bCREATE\b",
    "error_message": "Destructive operation 'CREATE' is not allowed in expert mode",
    "suggestion": "Expert mode is read-only. Use MATCH, RETURN, WHERE, ORDER BY, LIMIT for queries."
  },
  "DELETE": {
    "pattern": r"\bDELETE\b",
    "error_message": "Destructive operation 'DELETE' is not allowed in expert mode",
    "suggestion": "Expert mode is read-only. Cannot delete nodes or relationships."
  },
  "DETACH DELETE": {
    "pattern": r"\bDETACH\s+DELETE\b",
    "error_message": "Destructive operation 'DETACH DELETE' is not allowed in expert mode",
    "suggestion": "Expert mode is read-only. Cannot delete nodes or relationships."
  },
  "SET": {
    "pattern": r"\bSET\b",
    "error_message": "SET operations are not allowed in expert mode (read-only)",
    "suggestion": "Use MATCH and RETURN to query the graph. Modifications are not permitted."
  },
  "MERGE": {
    "pattern": r"\bMERGE\b",
    "error_message": "MERGE operations are not allowed in expert mode (read-only)",
    "suggestion": "Use MATCH to find existing nodes. Node creation is not permitted."
  },
  "DROP": {
    "pattern": r"\bDROP\b",
    "error_message": "Destructive operation 'DROP' is not allowed in expert mode",
    "suggestion": "Expert mode is read-only. Cannot drop indexes or constraints."
  },
  "CREATE INDEX": {
    "pattern": r"\bCREATE\s+INDEX\b",
    "error_message": "Index creation is not allowed in expert mode",
    "suggestion": "Expert mode is read-only. Cannot modify database schema."
  },
  "CREATE CONSTRAINT": {
    "pattern": r"\bCREATE\s+CONSTRAINT\b",
    "error_message": "Constraint creation is not allowed in expert mode",
    "suggestion": "Expert mode is read-only. Cannot modify database schema."
  }
}
```

**Detection Strategy**:
- Case-insensitive keyword matching
- Check before query execution
- Return standardized error response
- Log all blocked attempts for security audit

---

## Implementation Notes

### No Schema Changes
- This feature does NOT modify the Memgraph graph schema
- All node types and relationships remain unchanged
- Project-based isolation model unchanged

### Data Integrity
- Parameter validation prevents malformed queries
- Expert mode blocking prevents accidental data corruption
- Read-only enforcement maintained

### Backward Compatibility
- MCP tool schemas unchanged (existing clients unaffected)
- Result formats unchanged (only error responses improved)
- Query performance maintained (<50ms simple, <150ms complex)

---

## Summary

This data model documents:
1. ✅ Existing graph schema (no changes)
2. ✅ Query result structures (validated)
3. ✅ Parameter constraints (to be enforced)
4. ✅ Error response format (standardized)
5. ✅ Test result structures (enhanced)
6. ✅ Forbidden operation patterns (security)

All structures are existing or documented for validation purposes. No new entities introduced.
