# Research: Database Connection Architecture

**Date**: 2025-12-08
**Feature**: 001-fix-db-connection

## Overview

This document consolidates research findings for implementing multi-database support in code-graph-rag's MemgraphIngestor class.

## Research Questions

### Q1: How does Memgraph's `USE DATABASE` command work?

**Decision**: Use `USE DATABASE <database_name>` immediately after connection establishment.

**Rationale**:
- Memgraph supports multi-database functionality via the `USE DATABASE` command
- Command must be executed before any other queries to set the database context
- Memgraph auto-creates databases on first use when referenced in `USE DATABASE`
- Database context persists for the entire connection lifetime
- No explicit CREATE DATABASE needed for basic use cases

**Alternatives Considered**:
1. **Connection string parameter**: Memgraph does not support database selection in connection string (only host/port)
2. **Per-query database prefix**: Would require rewriting all Cypher queries and break existing code
3. **Multiple connections**: Unnecessary overhead; single connection with USE DATABASE is sufficient

**Implementation Details**:
```cypher
USE DATABASE codegraph_myproject;
-- All subsequent queries execute in codegraph_myproject context
```

**Edge Cases**:
- If database doesn't exist, Memgraph auto-creates it
- Database names must follow naming rules: alphanumeric, hyphens, underscores
- Special characters in names should be avoided or properly escaped

### Q2: How does pymgclient handle database switching?

**Decision**: Execute `USE DATABASE` as a regular query via `cursor.execute()` in the `__enter__` method.

**Rationale**:
- pymgclient (mgclient) treats `USE DATABASE` as a standard Cypher command
- No special API methods required; use existing `_execute_query()` infrastructure
- Command can be executed immediately after `mgclient.connect()` establishes connection
- Connection state persists for all subsequent queries

**Alternatives Considered**:
1. **Connection pool with database routing**: Overcomplicated for current scale
2. **Separate connection per database**: Resource-intensive, unnecessary
3. **Wrapper class around connection**: Adds abstraction layer without clear benefit

**Best Practices**:
- Execute USE DATABASE immediately in `__enter__` after connection establishment
- Log the database switch for debugging purposes
- Validate database name before attempting to switch (alphanumeric + hyphen/underscore only)
- Handle connection errors gracefully with clear error messages

### Q3: What is the environment variable configuration pattern in the codebase?

**Decision**: Add `MEMGRAPH_DATABASE` to `AppConfig` class in `config.py`, with optional override via constructor parameter.

**Rationale**:
- Existing pattern: `MEMGRAPH_HOST`, `MEMGRAPH_PORT` already defined in `AppConfig`
- Pydantic settings automatically load from environment variables or `.env` file
- Default value should be `None` or empty string to maintain backward compatibility
- Constructor parameter allows runtime override for tests

**Pattern Observed**:
```python
# codebase_rag/config.py (lines 41-46)
class AppConfig(BaseSettings):
    MEMGRAPH_HOST: str = "localhost"
    MEMGRAPH_PORT: int = 7687
    # ADD: MEMGRAPH_DATABASE: str = ""
```

**Integration Points**:
- `stress_test.py` line 34: Already sets `MEMGRAPH_DATABASE` env var
- `MemgraphIngestor.__init__()` should accept optional `database_name` parameter
- If `database_name` is None, fall back to `settings.MEMGRAPH_DATABASE`

### Q4: How should database name validation work?

**Decision**: Validate database names using regex pattern `^[a-zA-Z0-9_-]+$` before attempting USE DATABASE.

**Rationale**:
- Prevents SQL injection-style attacks through database names
- Matches Memgraph's database naming requirements
- Provides clear error messages for invalid names
- Fails fast before attempting connection

**Validation Logic**:
```python
import re

def validate_database_name(name: str) -> bool:
    """Validate database name contains only safe characters."""
    if not name:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))
```

**Error Handling**:
- Invalid name → raise `ValueError` with descriptive message
- Empty/None name → skip USE DATABASE command (backward compatible)
- Connection failure after USE DATABASE → log full error with database name

### Q5: What test infrastructure is needed?

**Decision**: Create `codebase_rag/tests/` directory structure with unit and integration tests.

**Rationale**:
- `pyproject.toml` line 83 references `testpaths = ["codebase_rag/tests"]` but directory doesn't exist
- Need both unit tests (mock connection) and integration tests (real Memgraph)
- Fixtures for test database creation/cleanup
- Tests should verify isolation between databases

**Test Structure**:
```
codebase_rag/tests/
├── __init__.py
├── unit/
│   └── test_graph_service.py      # Mock-based tests for MemgraphIngestor
├── integration/
│   └── test_database_switching.py # Real Memgraph integration tests
└── fixtures/
    └── conftest.py                # pytest fixtures for test databases
```

**Test Scenarios** (from spec.md):
1. **Unit Tests**: Mock connection, verify USE DATABASE called with correct name
2. **Integration Tests**: Real Memgraph, verify queries execute against correct database
3. **Isolation Tests**: Multiple MemgraphIngestor instances, verify no cross-contamination
4. **Environment Variable Tests**: Verify MEMGRAPH_DATABASE env var respected
5. **Validation Tests**: Invalid database names rejected with clear errors

## Implementation Sequence

1. **Config Layer** (codebase_rag/config.py):
   - Add `MEMGRAPH_DATABASE: str = ""` to AppConfig class

2. **Service Layer** (codebase_rag/services/graph_service.py):
   - Add `database_name: str | None = None` parameter to `__init__`
   - Add `validate_database_name()` static method
   - Add `USE DATABASE` execution in `__enter__` method
   - Update connection logging to include database name

3. **Test Infrastructure** (codebase_rag/tests/):
   - Create directory structure
   - Add unit tests with mocked connection
   - Add integration tests with real Memgraph
   - Add pytest fixtures for test database lifecycle

4. **Stress Test Update** (stress_test.py):
   - Pass `database_name` parameter to MemgraphIngestor (line 66-69)
   - Verify tests execute against correct database

5. **Documentation**:
   - Update quickstart.md with multi-database setup examples
   - Document MEMGRAPH_DATABASE environment variable

## Technology Decisions Summary

| Component | Technology/Pattern | Justification |
|-----------|-------------------|---------------|
| Database switching | `USE DATABASE` via cursor.execute() | Standard Cypher command, no special API needed |
| Configuration | Pydantic settings + env var | Matches existing MEMGRAPH_HOST/PORT pattern |
| Validation | Regex `^[a-zA-Z0-9_-]+$` | Prevents injection, matches Memgraph requirements |
| Testing | pytest + fixtures | Existing test framework (pyproject.toml) |
| Error handling | Raise ValueError for invalid names | Fast failure with clear messages |

## Open Questions Resolved

- ✅ **Q1**: Memgraph USE DATABASE syntax → `USE DATABASE <name>;`
- ✅ **Q2**: pymgclient API → Use `cursor.execute()` with USE DATABASE command
- ✅ **Q3**: Configuration pattern → Add to AppConfig, env var MEMGRAPH_DATABASE
- ✅ **Q4**: Validation approach → Regex validation before connection
- ✅ **Q5**: Test infrastructure → Create codebase_rag/tests/ structure

All technical unknowns from the plan's Technical Context have been resolved.
