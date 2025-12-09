# Data Model: Database Connection Architecture

**Feature**: 001-fix-db-connection
**Date**: 2025-12-08

## Overview

This feature extends the existing MemgraphIngestor class to support multi-database contexts. The data model describes the new attributes, validation rules, and state transitions for database-aware connections.

## Entities

### 1. MemgraphIngestor (Modified)

**Description**: Handles all communication and query execution with Memgraph database, now with multi-database support.

**Attributes**:

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `_host` | `str` | Yes | N/A | Memgraph host address |
| `_port` | `int` | Yes | N/A | Memgraph port number |
| `_database_name` | `str \| None` | No | `None` | Target database name |
| `batch_size` | `int` | Yes | `1000` | Batch size for bulk operations |
| `conn` | `mgclient.Connection \| None` | Yes | `None` | Active database connection |
| `node_buffer` | `list[tuple]` | Yes | `[]` | Buffered nodes for batch insertion |
| `relationship_buffer` | `list[tuple]` | Yes | `[]` | Buffered relationships for batch insertion |
| `unique_constraints` | `dict[str, str]` | Yes | {...} | Label-to-property constraint mappings |

**New/Modified Attributes**:
- `_database_name` (NEW): Optional database name for multi-database support

**Validation Rules**:

1. **Database Name Format** (FR-004):
   - Pattern: `^[a-zA-Z0-9_-]+$`
   - Must contain only alphanumeric characters, hyphens, and underscores
   - Empty string or `None` is valid (backward compatible)
   - Invalid names raise `ValueError` with descriptive message

2. **Batch Size** (existing):
   - Must be positive integer (>= 1)
   - Invalid values raise `ValueError`

3. **Connection State**:
   - `conn` must be non-None before executing queries
   - Queries fail with `ConnectionError("Not connected to Memgraph.")` if conn is None

**State Transitions**:

```
┌──────────────┐
│ Disconnected │ (conn = None, _database_name set or None)
└──────┬───────┘
       │ __enter__()
       │ 1. mgclient.connect(host, port)
       │ 2. IF _database_name: execute USE DATABASE
       ▼
┌──────────────┐
│  Connected   │ (conn != None, database context set)
└──────┬───────┘
       │ execute queries
       │ (all queries run in selected database context)
       ▼
┌──────────────┐
│  Connected   │ (active query execution)
└──────┬───────┘
       │ __exit__()
       │ 1. flush_all()
       │ 2. conn.close()
       ▼
┌──────────────┐
│ Disconnected │ (conn = None)
└──────────────┘
```

**Relationships**:
- **Has-One**: Memgraph connection (mgclient.Connection)
- **Uses**: AppConfig for default database name fallback
- **Buffers**: Nodes and relationships for batch operations

### 2. AppConfig (Modified)

**Description**: Application configuration loaded from environment variables.

**Attributes** (relevant to this feature):

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MEMGRAPH_HOST` | `str` | No | `"localhost"` | Memgraph host address |
| `MEMGRAPH_PORT` | `int` | No | `7687` | Memgraph port number |
| `MEMGRAPH_DATABASE` | `str` | No | `""` | Default database name (NEW) |
| `MEMGRAPH_BATCH_SIZE` | `int` | No | `1000` | Default batch size |

**New Attributes**:
- `MEMGRAPH_DATABASE` (NEW, FR-003): Default database name from environment variable

**Validation Rules**:
- All Pydantic validation rules apply (type checking)
- Port must be valid integer
- Batch size must be positive integer

**Relationships**:
- **Provides-Config-To**: MemgraphIngestor (via dependency injection pattern)

### 3. TestEnvironment (Conceptual)

**Description**: Configuration for isolated test database contexts.

**Attributes**:

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `database_name` | `str` | Yes | N/A | Test database name (e.g., `codegraph_test_12345`) |
| `project_root` | `str` | Yes | N/A | Path to test project/fixtures |
| `cleanup_on_exit` | `bool` | No | `True` | Whether to drop database after tests |

**Validation Rules**:
- `database_name` must follow same validation as MemgraphIngestor
- `project_root` must be valid directory path

**State Transitions**:

```
┌──────────┐
│  Setup   │ (create test database context)
└────┬─────┘
     │ pytest fixture setup
     │ 1. Create MemgraphIngestor(database_name=test_db)
     │ 2. Index test fixtures
     ▼
┌──────────┐
│ Testing  │ (execute test scenarios)
└────┬─────┘
     │ pytest fixture teardown
     │ IF cleanup_on_exit:
     │   1. DROP DATABASE test_db (or MATCH/DETACH DELETE)
     ▼
┌──────────┐
│ Teardown │ (clean state)
└──────────┘
```

**Relationships**:
- **Creates**: MemgraphIngestor instance with test database
- **Manages**: Test database lifecycle

## Data Flow

### Scenario 1: Stress Test Execution (User Story 2)

```
┌─────────────────┐
│ stress_test.py  │
│ os.environ[     │
│  'MEMGRAPH_     │
│   DATABASE'     │
│ ] = 'codegraph_ │
│      code-graph-│
│      rag'       │
└────────┬────────┘
         │
         ▼
┌────────────────────┐
│ settings.          │
│ MEMGRAPH_DATABASE  │
│ = 'codegraph_code- │
│    graph-rag'      │
└────────┬───────────┘
         │
         ▼
┌────────────────────────┐
│ MemgraphIngestor(      │
│   host='localhost',    │
│   port=7687,           │
│   database_name=None   │ ◄─ Defaults to settings.MEMGRAPH_DATABASE
│ )                      │
└────────┬───────────────┘
         │ __enter__()
         ▼
┌────────────────────────┐
│ mgclient.connect()     │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ USE DATABASE           │
│ codegraph_code-graph-  │
│ rag                    │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Execute test queries   │
│ (all in database       │
│  context)              │
└────────────────────────┘
```

### Scenario 2: Integration Test Isolation (User Story 3)

```
┌────────────────────────┐
│ pytest fixture setup   │
│ database_name =        │
│   f'codegraph_test_    │
│    {uuid4()}'          │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────────┐
│ MemgraphIngestor(          │
│   host='localhost',        │
│   port=7687,               │
│   database_name=           │
│     'codegraph_test_a1b2'  │ ◄─ Explicit override
│ )                          │
└────────┬───────────────────┘
         │ __enter__()
         ▼
┌────────────────────────┐
│ USE DATABASE           │
│ codegraph_test_a1b2    │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ Run test assertions    │
│ (isolated database)    │
└────────┬───────────────┘
         │ __exit__()
         ▼
┌────────────────────────┐
│ pytest fixture         │
│ teardown:              │
│ MATCH (n) DETACH       │
│ DELETE n               │
└────────────────────────┘
```

### Scenario 3: Multiple Projects (User Story 1)

```
┌──────────────────┐      ┌──────────────────┐
│ MemgraphIngestor │      │ MemgraphIngestor │
│ database_name=   │      │ database_name=   │
│ 'codegraph_      │      │ 'codegraph_      │
│  project-a'      │      │  project-b'      │
└────────┬─────────┘      └────────┬─────────┘
         │                         │
         │ __enter__()             │ __enter__()
         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐
│ USE DATABASE    │       │ USE DATABASE    │
│ codegraph_      │       │ codegraph_      │
│ project-a       │       │ project-b       │
└────────┬────────┘       └────────┬────────┘
         │                         │
         │ Query for functions     │ Query for classes
         │ in project-a            │ in project-b
         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐
│ Results from    │       │ Results from    │
│ project-a       │       │ project-b       │
│ ONLY            │       │ ONLY            │
└─────────────────┘       └─────────────────┘
         │                         │
         │ No cross-contamination  │
         └─────────────┬───────────┘
                       │
                       ▼
                  ✅ Isolation
                     Verified
```

## Schema Changes

**No graph schema changes required.**

The Memgraph graph schema (Project, Module, Class, Function, etc.) remains unchanged. This feature only affects connection management and database context selection, not the structure of nodes and relationships within each database.

## Migration Strategy

**No migration required.**

- Feature is backward compatible (database_name defaults to None/empty string)
- Existing code without database_name parameter continues to work
- Existing databases remain accessible
- New functionality is opt-in via constructor parameter or environment variable

## Validation Summary

| Entity | Validation Rule | Error Type | Error Message |
|--------|----------------|------------|---------------|
| MemgraphIngestor | Database name format | `ValueError` | `"Invalid database name '{name}': must contain only alphanumeric characters, hyphens, and underscores"` |
| MemgraphIngestor | Batch size positive | `ValueError` | `"batch_size must be a positive integer"` (existing) |
| MemgraphIngestor | Connection exists | `ConnectionError` | `"Not connected to Memgraph."` (existing) |
| MemgraphIngestor | Database switch failure | `Exception` | `"Failed to switch to database '{name}': {original_error}"` (FR-005) |

## Edge Cases Handled

1. **Database doesn't exist** (FR-008): Memgraph auto-creates on first USE DATABASE → No explicit handling needed
2. **Empty/None database name**: Skip USE DATABASE command → Backward compatible default behavior
3. **Invalid database name**: Validate before connection → Fast failure with clear error
4. **Switch failure mid-operation**: Connection fails before any queries execute → Clean error state
5. **Special characters in name**: Rejected by validation → Prevents injection and malformed queries
