# Feature Specification: Fix Structural Query Bugs and Achieve 100% Test Pass Rate

**Feature Branch**: `003-fix-structural-query-bugs`
**Created**: 2025-12-09
**Status**: Draft
**Input**: User description: "Fix all stress test failures and partial passes in structural query system: add parameter validation, fix Cypher bugs, block CREATE operations, and ensure 100% test pass rate"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Parameter Validation for Query Safety (Priority: P1)

When developers use structural query tools with invalid parameters, the system should reject them immediately with clear error messages rather than executing invalid queries or producing unexpected behavior. This prevents bugs, improves debugging experience, and ensures API consistency.

**Why this priority**: Critical for system reliability and security. Invalid parameters can cause crashes, return incorrect results, or expose security vulnerabilities. This is foundational for all other query operations.

**Independent Test**: Can be fully tested by calling each structural query tool with invalid parameter values (out-of-range numbers, invalid enum values, null values, empty strings) and verifying that clear error messages are returned before any database query executes.

**Acceptance Scenarios**:

1. **Given** a user calls `query_hierarchy` with `direction="sideways"`, **When** the query executes, **Then** the system returns an error stating "Invalid direction parameter. Must be 'up', 'down', or 'both'" before any database query runs
2. **Given** a user calls `query_dependencies` with `dependency_type="invalid_type"`, **When** the query executes, **Then** the system returns an error stating "Invalid dependency_type parameter. Must be 'imports', 'calls', or 'all'"
3. **Given** a user calls `query_callers` with `max_depth=999`, **When** the query executes, **Then** the system returns an error stating "max_depth must be between 1 and 5 (got 999)"
4. **Given** a user calls any query tool with empty string for a required qualified_name parameter, **When** the query executes, **Then** the system returns an error stating "[Entity] name cannot be empty"

---

### User Story 2 - Expert Mode Security Controls (Priority: P1)

When developers use expert mode to write custom Cypher queries, the system must block all write operations (CREATE, DELETE, SET, MERGE) to maintain read-only access and prevent accidental or malicious data corruption. Users should receive clear error messages explaining why the operation was blocked.

**Why this priority**: Critical security requirement. Expert mode provides powerful query capabilities but must remain read-only to prevent data corruption. One missed write operation could compromise the entire knowledge graph.

**Independent Test**: Can be fully tested by attempting to execute Cypher queries containing CREATE, DELETE, SET, or MERGE statements through the `query_cypher` tool and verifying that all are rejected with specific error messages identifying the forbidden operation.

**Acceptance Scenarios**:

1. **Given** a user executes `query_cypher` with "CREATE (n:TestNode) RETURN n", **When** the query is validated, **Then** the system returns error "Destructive operation 'CREATE' is not allowed in expert mode"
2. **Given** a user executes `query_cypher` with "DELETE n", **When** the query is validated, **Then** the system returns error "Destructive operation 'DELETE' is not allowed in expert mode"
3. **Given** a user executes `query_cypher` with "MATCH (n) SET n.foo = 'bar'", **When** the query is validated, **Then** the system returns error "SET operations are not allowed in expert mode (read-only)"
4. **Given** a user executes `query_cypher` with "MERGE (n:Test) RETURN n", **When** the query is validated, **Then** the system returns error "MERGE operations are not allowed in expert mode (read-only)"

---

### User Story 3 - Fix Module Exports Cypher Query Bug (Priority: P1)

When developers query module exports using `query_module_exports`, the system should successfully return all exported functions, classes, and methods sorted in a logical order. Currently, the query fails with a Cypher error when attempting to sort results because it tries to order by a list value (node labels).

**Why this priority**: This is a complete blocker for the `query_module_exports` functionality. The tool is currently non-functional and fails 100% of the time, making it impossible for users to discover what a module exports.

**Independent Test**: Can be fully tested by calling `query_module_exports` on any module that contains at least one function or class and verifying that results are returned without Cypher errors, properly sorted, and containing all expected exports.

**Acceptance Scenarios**:

1. **Given** a module contains multiple functions and classes, **When** `query_module_exports` is called with `include_private=False`, **Then** the system returns all public exports sorted by export type and name without any Cypher errors
2. **Given** a module contains both public and private members, **When** `query_module_exports` is called with `include_private=True`, **Then** the system returns all exports (public and private) sorted correctly
3. **Given** the Cypher query uses `labels(export)` which returns a list, **When** the query attempts to sort results, **Then** the system uses `labels(export)[0]` or an alternative approach that doesn't cause "Comparison is not defined for values of type list" errors

---

### User Story 4 - Improve Test Data and Query Accuracy (Priority: P2)

When stress tests run against an indexed project, all structural queries should return accurate results based on the actual code graph. Currently, some queries return 0 results when they should return relationships (callers, dependencies), indicating either missing test data or incorrect query patterns.

**Why this priority**: Important for test reliability and confidence. While lower priority than fixing actual bugs, accurate test data ensures we can detect regressions and validate that queries work correctly in real-world scenarios.

**Independent Test**: Can be fully tested by verifying that the test project (ai-gateway-mcp) is fully indexed, examining its graph structure to confirm expected relationships exist, and running structural queries against known functions/classes/modules that should have relationships.

**Acceptance Scenarios**:

1. **Given** the test project has been fully indexed, **When** `query_callers` is called on a function that is actually called by other functions in the codebase, **Then** the system returns at least one caller relationship
2. **Given** a module imports other modules, **When** `query_dependencies(dependency_type="all")` is called, **Then** the system returns combined results from both import and call dependencies
3. **Given** test queries reference qualified names, **When** those names are constructed, **Then** they match the actual qualified names in the indexed graph (correct project prefix, correct module paths)
4. **Given** complex multi-hop relationship queries are executed, **When** the relationships exist in the graph, **Then** the queries traverse the paths correctly and return expected results

---

### Edge Cases

- What happens when a query tool receives a None value for a required parameter?
- What happens when max_depth is set to 0 or a negative number?
- What happens when expert mode query contains multiple forbidden operations?
- What happens when module_exports is called on a module that doesn't exist?
- What happens when query_dependencies is called with type="all" but the target has no dependencies?
- What happens when query_callers is called on a function with no callers (legitimate empty result)?
- How does the system distinguish between "query returned 0 results because none exist" vs "query returned 0 results due to a bug"?

## Requirements *(mandatory)*

### Functional Requirements

**Parameter Validation (P1)**

- **FR-001**: The `query_hierarchy` function MUST validate that the `direction` parameter is one of: "up", "down", or "both". Any other value MUST be rejected with a clear error message before executing the database query.

- **FR-002**: The `query_dependencies` function MUST validate that the `dependency_type` parameter is one of: "imports", "calls", or "all". Any other value MUST be rejected with a clear error message.

- **FR-003**: All query functions MUST validate that required qualified_name parameters (function_name, class_name, module_name, etc.) are non-empty strings. Empty strings or None values MUST be rejected with clear error messages.

- **FR-004**: All functions with `max_depth` parameters MUST validate that values are within the documented allowed range (1-5 for callers, 1-10 for hierarchy, etc.). Out-of-range values MUST be rejected with error messages specifying the valid range and the received value.

- **FR-005**: All functions with numeric limit parameters (max_nodes, limit, etc.) MUST validate that values are positive integers. Zero or negative values MUST be rejected with clear error messages.

**Expert Mode Security (P1)**

- **FR-006**: The `query_cypher` expert mode function MUST scan the provided Cypher query for CREATE, DELETE, SET, and MERGE keywords (case-insensitive) and reject queries containing any of these operations with specific error messages identifying the forbidden operation.

- **FR-007**: The expert mode validation MUST occur before any query execution to prevent write operations from reaching the database.

- **FR-008**: Error messages for forbidden operations MUST clearly state: (1) which operation was detected, (2) that expert mode is read-only, and (3) that the operation is not allowed.

**Module Exports Query Fix (P1)**

- **FR-009**: The `query_module_exports` Cypher query MUST NOT attempt to order results by `labels(export)` directly, as Cypher cannot compare list types for sorting.

- **FR-010**: The module exports query MUST either: (a) extract the first label using `labels(export)[0]` for sorting, OR (b) remove the ORDER BY clause entirely, OR (c) use an alternative sorting approach that doesn't involve list comparison.

- **FR-011**: The fixed query MUST successfully return all functions, classes, and methods defined by a module without Cypher errors.

- **FR-012**: The fixed query MUST respect the `include_private` parameter to filter exports correctly.

**Test Data and Query Accuracy (P2)**

- **FR-013**: The stress test MUST verify that the test project (ai-gateway-mcp) is fully indexed before running queries by checking node count and confirming expected graph structure.

- **FR-014**: Test cases using specific qualified names MUST use names that actually exist in the indexed test project. Queries testing "0 callers" edge cases should use functions known to have no callers.

- **FR-015**: The `query_dependencies` function with `dependency_type="all"` MUST correctly combine results from both "imports" and "calls" queries and return the union of both result sets.

- **FR-016**: Stress test assertions for "partial" status MUST be updated to distinguish between legitimate empty results (function has no callers) and unexpected empty results (query bug or missing test data).

### Key Entities

- **Query Tool**: A structural query function (query_callers, query_hierarchy, query_dependencies, query_implementations, query_module_exports, query_call_graph, query_cypher) that accepts parameters and returns graph query results

- **Parameter Validation Rule**: A constraint defining allowed values for a query parameter (enum values, numeric ranges, non-empty strings, etc.)

- **Expert Mode Query**: A custom Cypher query provided by users for advanced graph querying, subject to read-only restrictions

- **Forbidden Operation**: A Cypher keyword (CREATE, DELETE, SET, MERGE) that must be blocked in expert mode to maintain read-only access

- **Module Export**: A function, class, or method defined by a module and available to importers

- **Test Result Status**: Classification of test outcome (pass, fail, partial) with "partial" indicating query executed but returned unexpected results

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 50 stress tests achieve "pass" status (100% pass rate, up from current 68%)

- **SC-002**: Zero tests have "fail" status (down from 8 failures)

- **SC-003**: Zero tests have "partial" status indicating unexpected empty results (down from 8 partials)

- **SC-004**: All parameter validation tests (P1-P15) reject invalid inputs with clear error messages within 5ms

- **SC-005**: All expert mode security tests block forbidden operations before any database query executes

- **SC-006**: Module exports query successfully returns results for test modules without Cypher errors

- **SC-007**: Stress test execution completes in under 1 second (current: 0.40s, maintain fast performance)

- **SC-008**: All structural query performance targets continue to be met (<50ms for simple queries, <150ms for complex traversals)

- **SC-009**: All concurrent operation tests pass, demonstrating that validation and fixes don't introduce thread safety issues

- **SC-010**: Test suite provides clear reporting distinguishing between legitimate empty results and bugs

## Scope

### In Scope

- Add parameter validation to all 7 structural query tools
- Block CREATE operations in expert mode (currently missing)
- Fix module_exports Cypher query to handle label list sorting
- Verify and correct test data qualified names
- Fix query_dependencies "all" type to properly combine results
- Update stress test assertions to handle legitimate empty results correctly
- Ensure all 50 tests pass

### Out of Scope

- Adding new structural query tools or features
- Performance optimization beyond maintaining current speed
- Changes to MCP protocol or tool schemas
- Refactoring test suite structure (already completed)
- Adding new test categories beyond the 50 existing tests
- Changes to Memgraph configuration or infrastructure
- UI/UX improvements for error messages (focus on accuracy and clarity)

## Assumptions

- The test project (ai-gateway-mcp) is already indexed in Memgraph and accessible
- The existing parameter validation patterns (for max_depth ranges) provide good examples to follow
- Cypher query validation using regex/string scanning for keywords is sufficient (no need for full Cypher parsing)
- Performance will not degrade significantly from adding parameter validation checks (sub-millisecond overhead)
- The current test assertion logic can distinguish between legitimate empty results and bugs by checking for specific known cases
- Fixing the module_exports ORDER BY issue won't significantly change the order of results in a way that breaks existing consumers

## Dependencies

- Access to Memgraph database at localhost:7687
- Indexed ai-gateway-mcp project with expected code structure
- Existing structural query implementation in `codebase_rag/tools/structural_queries.py`
- Stress test suite in `tests/stress/` directory
- Python Pydantic for potential parameter validation models (already in dependencies)

## Open Questions

None - all requirements are sufficiently clear to proceed with implementation. Parameter validation rules are well-defined from existing patterns, expert mode forbidden operations are explicitly listed in current code, and the Cypher bug has a clear fix (use labels()[0] or remove ORDER BY).
