# Feature Specification: Fix Async Handlers for Structural Query Tools

**Feature Branch**: `001-fix-async-handlers`
**Created**: 2025-12-09
**Status**: Draft
**Input**: User description: "Fix structural query tool handlers to be async - resolve stress test failures caused by sync handlers being awaited"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stress Tests Pass (Priority: P1)

As a developer running the stress test suite, I want all structural query tool tests to pass so that I can verify the system is working correctly before deployment.

**Why this priority**: This is the core issue - 23 tests are failing due to async/sync mismatch. Without this fix, the test suite cannot validate system correctness.

**Independent Test**: Run `uv run stress_test.py` and verify structural query tests (S1-S7) pass.

**Acceptance Scenarios**:

1. **Given** the stress test suite is executed, **When** structural query tests S1-S7 run, **Then** all 7 tests should pass without "object dict can't be used in 'await' expression" errors
2. **Given** the stress test suite is executed, **When** edge case tests E6-E15 run, **Then** all tests should handle errors gracefully without async-related failures

---

### User Story 2 - Concurrent Operations Work (Priority: P1)

As a developer, I want concurrent query operations to function correctly so that performance tests validate the system's ability to handle multiple simultaneous requests.

**Why this priority**: Concurrent operations (CONC1-CONC4) are essential for validating production readiness under load.

**Independent Test**: Run `uv run stress_test.py` and verify concurrent operation tests pass.

**Acceptance Scenarios**:

1. **Given** multiple structural queries are issued simultaneously, **When** using `asyncio.gather()`, **Then** all queries should complete successfully without "unhashable type: 'dict'" errors
2. **Given** 10 concurrent queries are issued (CONC3 high load test), **When** the test executes, **Then** at least 80% should complete successfully

---

### User Story 3 - MCP Server Tool Invocation Works (Priority: P1)

As an MCP client (Claude Code), I want to invoke structural query tools through the MCP protocol so that I can query the code knowledge graph.

**Why this priority**: The MCP server is the primary interface for AI assistants to use this tool. If handlers aren't async, the server fails.

**Independent Test**: Start the MCP server and invoke `query_callers` tool via MCP protocol.

**Acceptance Scenarios**:

1. **Given** the MCP server is running, **When** a client calls `query_callers` tool, **Then** the server should await the handler and return results successfully
2. **Given** the MCP server is running, **When** any of the 7 structural query tools is invoked, **Then** the tool should return a valid JSON response

---

### Edge Cases

- What happens when a structural query handler returns an empty result? The handler returns a valid dict with an empty results array
- How does the system handle concurrent requests to the same handler? Handlers execute independently without race conditions
- What happens when a handler throws an exception? Exception is caught and returned as an error response without crashing the async loop

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All 7 structural query tool handlers MUST be async functions that can be awaited
- **FR-002**: Handlers MUST return `dict[str, Any]` after being awaited (return type unchanged)
- **FR-003**: Handlers MUST be compatible with `asyncio.gather()` for concurrent execution
- **FR-004**: The MCP server's `call_tool()` function MUST successfully await all structural query handlers
- **FR-005**: The stress test suite MUST pass all structural query tests (S1-S7) after the fix
- **FR-006**: The stress test suite MUST pass all concurrent operation tests (CONC1-CONC4) after the fix
- **FR-007**: The stress test suite MUST pass MCP integration test MCP4 (return type consistency)

### Key Entities

- **Handler Function**: The inner function returned by `create_*_tool()` functions that executes the actual query
- **Tool Registry**: `MCPToolsRegistry` class that stores handlers and provides them to the MCP server
- **Query Tool Classes**: `FindCallersQuery`, `ClassHierarchyQuery`, etc. that contain the query logic (unchanged)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Stress test pass rate improves from 37.7% to at least 80%
- **SC-002**: All 7 structural query tests (S1-S7) pass
- **SC-003**: All 4 concurrent operation tests (CONC1-CONC4) pass
- **SC-004**: All 10 edge case tests (E6-E15) that were failing due to async issues pass
- **SC-005**: MCP integration test MCP4 passes
- **SC-006**: Project isolation tests (ISO1-ISO3) pass
- **SC-007**: The MCP server can successfully invoke any structural query tool without errors

## Assumptions

- The underlying query logic in the `*Query` classes (e.g., `FindCallersQuery.execute()`) is synchronous and does not need to change
- Making handlers async (even though they don't perform async I/O) is acceptable for API consistency
- The stress test correctly expects async handlers (as the MCP server does)
- No other consumers of these handlers expect them to be synchronous
