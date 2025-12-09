# Feature Specification: Fix Database Connection Architecture

**Feature Branch**: `001-fix-db-connection`
**Created**: 2025-12-08
**Status**: Draft
**Input**: User description: "do all of this except for #4. I really don't care about cloud LLM provider embeddings because I'm poor and we have no choice but to use local resources."

**Context**: Based on stress test results (2025-12-08), the system successfully indexes codebases (2,312 nodes, 309 files) but the test harness cannot execute queries against named databases due to missing multi-database support in MemgraphIngestor.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Database Switching for Multiple Projects (Priority: P1)

Development teams need to work with multiple indexed projects simultaneously, each stored in its own isolated database. When running queries or tests against a specific project, the system must connect to the correct database without interference from other projects.

**Why this priority**: This is the root cause of stress test failures and blocks end-to-end testing. Without this, users cannot validate that indexed data is accessible.

**Independent Test**: Can be fully tested by indexing two different projects into separate databases (e.g., `codegraph_project-a` and `codegraph_project-b`), then verifying that queries against each database return only that project's data with no cross-contamination.

**Acceptance Scenarios**:

1. **Given** a codebase indexed in database `codegraph_myproject`, **When** a user connects specifying `database_name="codegraph_myproject"`, **Then** all subsequent queries execute against `codegraph_myproject` only

2. **Given** multiple databases exist (`codegraph_project-a`, `codegraph_project-b`), **When** tests switch between databases using different MemgraphIngestor instances, **Then** each instance queries only its specified database

3. **Given** an environment variable `MEMGRAPH_DATABASE="codegraph_test"` is set, **When** the system initializes a connection, **Then** it automatically switches to the `codegraph_test` database

---

### User Story 2 - Stress Test Execution (Priority: P2)

Quality assurance teams need to run comprehensive stress tests that validate query execution, code retrieval, and performance metrics against an indexed codebase. Tests must connect to the correct database and return actual results, not connection errors.

**Why this priority**: Enables validation of the entire system end-to-end, proving that Cypher generation, database queries, and result processing work together correctly.

**Independent Test**: Can be tested by running the existing `stress_test.py` script and verifying that all 26 test scenarios execute with real database results instead of "Not connected to Memgraph" errors.

**Acceptance Scenarios**:

1. **Given** a codebase is indexed in `codegraph_code-graph-rag`, **When** stress tests run with `MEMGRAPH_DATABASE` environment variable set, **Then** all 21 Cypher queries return actual results from the database

2. **Given** the stress test harness creates a MemgraphIngestor instance, **When** it executes code retrieval tests, **Then** it successfully retrieves code snippets by qualified name

3. **Given** performance tests execute concurrent queries, **When** all queries target the same database, **Then** results are consistent and performant

---

### User Story 3 - Integration Test Validation (Priority: P3)

Development teams writing integration tests need a reliable way to validate that database operations (indexing, querying, updates) work correctly against isolated test databases. Tests should be able to create temporary databases, run assertions, and clean up without affecting production data.

**Why this priority**: Supports the long-term health of the codebase by enabling comprehensive integration testing in CI/CD pipelines.

**Independent Test**: Can be tested by creating a test suite that spins up a temporary database (e.g., `codegraph_test_12345`), indexes sample code, runs assertions, and verifies the database can be dropped afterward.

**Acceptance Scenarios**:

1. **Given** an integration test suite, **When** it creates a MemgraphIngestor with `database_name="codegraph_test_temp"`, **Then** all operations execute against that database only

2. **Given** a test database exists from a previous run, **When** tests attempt to connect, **Then** the system either reuses or clears the existing database as configured

---

### Edge Cases

- What happens when the specified database doesn't exist? (Should auto-create or return clear error)
- How does the system handle switching between databases in a single process? (Multiple MemgraphIngestor instances)
- What happens if `MEMGRAPH_DATABASE` is set but invalid? (Clear error message indicating database issue)
- How does the system behave if database switch fails mid-operation? (Rollback or error with current state info)
- What happens when database name contains special characters? (Sanitize or reject invalid names)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: MemgraphIngestor MUST accept a `database_name` parameter during initialization
- **FR-002**: MemgraphIngestor MUST execute a `USE DATABASE [name]` command immediately after connecting to Memgraph
- **FR-003**: MemgraphIngestor MUST read the `MEMGRAPH_DATABASE` environment variable and use it as default database name if no parameter provided
- **FR-004**: System MUST validate that database names contain only alphanumeric characters, hyphens, and underscores
- **FR-005**: System MUST provide clear error messages when database switching fails (e.g., "Failed to switch to database 'codegraph_xyz': database does not exist")
- **FR-006**: All Cypher query executions MUST occur within the context of the selected database
- **FR-007**: Stress test harness MUST set `MEMGRAPH_DATABASE` environment variable before initializing MemgraphIngestor
- **FR-008**: System MUST support creating new databases on-demand when they don't exist (Memgraph auto-creates on first use)
- **FR-009**: Connection health checks MUST validate both connectivity to Memgraph AND successful database selection
- **FR-010**: Documentation MUST include examples of multi-database setup for local development and testing

### Key Entities

- **Database Connection**: Represents the Memgraph connection with associated database context
  - Attributes: host, port, database name, connection state
  - Relationships: Each connection is scoped to exactly one database at a time

- **Test Environment**: Configuration for isolated testing
  - Attributes: database name, project path, test fixtures
  - Relationships: Maps to a specific Memgraph database instance

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Stress test suite executes all 26 tests with zero "Not connected to Memgraph" errors (currently 21 failures)
- **SC-002**: Code retrieval tests successfully fetch actual code snippets from the database (currently untested due to connection failures)
- **SC-003**: Multiple MemgraphIngestor instances can coexist in the same process, each connected to different databases without interference
- **SC-004**: Database switching completes in under 100ms (negligible overhead)
- **SC-005**: 100% of integration tests pass when using isolated test databases
- **SC-006**: Documentation enables developers to set up multi-database environments in under 5 minutes

## Assumptions

- Memgraph supports `USE DATABASE` command for switching contexts (standard Memgraph feature)
- Database names follow naming conventions: `codegraph_[project-name]` or `codegraph_[group-name]`
- Each project/test suite manages its own database lifecycle (no shared ownership)
- Memgraph auto-creates databases on first use when referenced in `USE DATABASE` command
- Connection pooling is not required for current scale (single-threaded test execution)

## Dependencies

- Memgraph server must be running and accessible
- `mgclient` Python library supports database switching commands
- Existing indexing infrastructure remains unchanged (only connection logic affected)

## Out of Scope

- Database migration utilities (databases are ephemeral, re-indexing is acceptable)
- Connection pooling or advanced connection management
- Cross-database queries or joins
- Database backup/restore functionality
- Cloud-based embedding providers (explicitly excluded per user requirements)
- Performance optimization beyond the database switching mechanism
- GUI or visual tools for database management
