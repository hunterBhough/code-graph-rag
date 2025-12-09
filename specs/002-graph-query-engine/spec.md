# Feature Specification: Transform code-graph-rag into Specialized Graph Query Engine

**Feature Branch**: `002-graph-query-engine`
**Created**: 2025-12-08
**Status**: Draft
**Input**: User description: "Transform code-graph-rag into a Specialized Graph Query Engine by removing semantic search functionality and focusing on structural code relationships, call graphs, dependencies, and complex multi-hop queries. This refactoring clarifies the tool's role in a three-tool architecture alongside vector-search-mcp (semantic/keyword search) and mcp-ragdocs (documentation search)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Query Function Call Relationships (Priority: P1)

A developer needs to understand where a specific function is called throughout their codebase to assess the impact of potential changes. They use code-graph-rag to quickly find all callers without waiting for semantic search or scanning documentation.

**Why this priority**: Understanding function usage is the most fundamental graph query operation. This provides immediate value and demonstrates the core capability of structural relationship exploration.

**Independent Test**: Can be fully tested by indexing a sample codebase with known function call relationships and verifying the tool returns accurate caller lists within 50ms.

**Acceptance Scenarios**:

1. **Given** a function `auth.login` exists in the codebase, **When** developer queries for callers of `auth.login`, **Then** the tool returns all direct callers within 50ms
2. **Given** a function has multi-level callers (callers of callers), **When** developer specifies max_depth=2, **Then** the tool returns caller chains showing the complete path
3. **Given** a function has no callers, **When** developer queries for callers, **Then** the tool returns an empty result with clear messaging

---

### User Story 2 - Explore Class Inheritance Hierarchies (Priority: P1)

A developer working with object-oriented code needs to understand class inheritance relationships to refactor a base class without breaking child implementations. They query the class hierarchy to see both parent classes and all subclasses.

**Why this priority**: Class inheritance is a fundamental structural relationship in OOP codebases. This capability is essential for safe refactoring and architectural understanding.

**Independent Test**: Can be fully tested by creating a class hierarchy with multiple inheritance levels and verifying the tool correctly displays ancestor and descendant relationships.

**Acceptance Scenarios**:

1. **Given** a class `BaseAuth` with three child classes, **When** developer queries class hierarchy for `BaseAuth`, **Then** the tool displays all three children with their depth levels
2. **Given** a class `AdminAuth` that inherits from `BaseAuth`, **When** developer queries hierarchy with direction="up", **Then** the tool shows only parent classes
3. **Given** a class with both parents and children, **When** developer queries with direction="both", **Then** the tool displays complete hierarchy tree

---

### User Story 3 - Analyze Module Dependencies (Priority: P2)

A developer preparing to extract a module into a separate library needs to identify all imports and function calls the module depends on. They use the dependency analysis to create a complete list of required interfaces.

**Why this priority**: Dependency analysis supports architectural decisions and refactoring efforts. While important, it builds on the foundational query capabilities from P1 stories.

**Independent Test**: Can be fully tested by analyzing a module with known import and call dependencies, verifying all dependencies are identified.

**Acceptance Scenarios**:

1. **Given** a module `payment_processor` that imports two libraries, **When** developer queries dependencies with type="imports", **Then** the tool lists all imported modules
2. **Given** a function that calls five other functions, **When** developer queries dependencies with type="calls", **Then** the tool lists all called functions
3. **Given** a module with both imports and calls, **When** developer queries with type="all", **Then** the tool provides complete dependency information

---

### User Story 4 - Find Interface Implementations (Priority: P2)

A developer wants to understand all classes that implement a specific interface to ensure consistent behavior across implementations. They query for all implementations to review each one.

**Why this priority**: Implementation discovery is critical for maintaining consistency but is used less frequently than direct call/hierarchy queries.

**Independent Test**: Can be tested by defining an interface with multiple implementing classes and verifying all implementations are found.

**Acceptance Scenarios**:

1. **Given** an interface `PaymentProvider` with four implementations, **When** developer queries implementations, **Then** all four classes are returned
2. **Given** a base class used for inheritance, **When** developer queries implementations, **Then** all extending classes are identified
3. **Given** an interface with no implementations, **When** developer queries, **Then** an empty result is returned with clear messaging

---

### User Story 5 - Execute Custom Graph Queries (Priority: P3)

An advanced user needs to perform a complex graph query not covered by pre-built tools (e.g., "find all functions in module X that call functions in module Y"). They write a custom Cypher query using expert mode.

**Why this priority**: Expert mode provides flexibility for power users but requires graph schema knowledge. Most users will rely on pre-built queries, making this lower priority.

**Independent Test**: Can be tested by executing valid Cypher queries against a known graph structure and verifying correct results are returned.

**Acceptance Scenarios**:

1. **Given** a valid Cypher query, **When** user executes via expert mode, **Then** results are returned in formatted table
2. **Given** an invalid Cypher query, **When** user executes, **Then** an error message with query details is returned
3. **Given** a query that returns no results, **When** user executes, **Then** a clear "no results" message is shown

---

### User Story 6 - Generate Call Graph Visualizations (Priority: P3)

A developer analyzing code flow needs to see the complete call chain starting from an entry point function. They generate a call graph to visualize the execution path.

**Why this priority**: Call graph generation is valuable for understanding complex flows but is used less frequently than point queries. It builds on the foundational caller/callee query capabilities.

**Independent Test**: Can be tested by generating a call graph from a known entry point and verifying all nodes and edges are correctly identified.

**Acceptance Scenarios**:

1. **Given** an entry point function with a call depth of 3, **When** developer generates call graph with max_depth=3, **Then** all nodes and edges are returned
2. **Given** a call graph with more than 20 edges, **When** developer generates the graph, **Then** output is truncated with count of additional edges
3. **Given** an entry point with no outgoing calls, **When** developer generates call graph, **Then** an error indicates no call graph found

---

### Edge Cases

- What happens when a query targets a function/class that doesn't exist in the graph?
- How does the system handle circular dependencies in class hierarchies?
- What occurs when a Cypher query times out or exceeds memory limits?
- How are ambiguous names handled when multiple classes/functions share the same name?
- What happens when the graph database is unavailable or unreachable?
- How does the system handle very large result sets (e.g., a function called by 1000+ other functions)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST remove all semantic search code including vector_store.py, embedder.py, semantic_search.py, and unixcoder.py files
- **FR-002**: System MUST exclude documentation files (*.md, *.mdx, *.txt, *.rst, *.adoc, *.pdf, docs/**, documentation/**) from graph indexing
- **FR-003**: System MUST provide a pre-built query tool to find all direct callers of a specified function
- **FR-004**: System MUST provide a pre-built query tool to find multi-level callers up to a specified depth
- **FR-005**: System MUST provide a pre-built query tool to retrieve class inheritance hierarchies (ancestors, descendants, or both)
- **FR-006**: System MUST provide a pre-built query tool to analyze module/function dependencies (imports, calls, or both)
- **FR-007**: System MUST provide a pre-built query tool to retrieve all public exports from a module
- **FR-008**: System MUST provide a pre-built query tool to find all classes that implement a given interface or extend a base class
- **FR-009**: System MUST provide a pre-built query tool to generate call graphs from an entry point with configurable depth
- **FR-010**: System MUST provide an expert-mode tool for direct Cypher query execution
- **FR-011**: System MUST return pre-built query results in under 50ms for typical codebases
- **FR-012**: System MUST format expert-mode Cypher results as readable tables
- **FR-013**: System MUST update all tool descriptions to emphasize structural/relational query focus
- **FR-014**: System MUST update documentation (README, CLAUDE.md) to clearly differentiate from vector-search-mcp and mcp-ragdocs
- **FR-015**: System MUST remove all Qdrant client dependencies from configuration
- **FR-016**: System MUST remove all embedding-related settings from configuration
- **FR-017**: System MUST update MCP tool registry to register structural query tools instead of semantic search tools
- **FR-018**: System MUST provide clear error messages when queries target non-existent nodes
- **FR-019**: System MUST handle circular dependency detection in class hierarchies
- **FR-020**: System MUST truncate large result sets (>50 rows for expert mode, >100 for pre-built queries) with clear indicators

### Key Entities

- **Function/Method Node**: Represents a callable code unit with qualified_name, name, start_line, end_line, and path attributes
- **Class Node**: Represents a class definition with qualified_name, name, and location attributes, connected via INHERITS/IMPLEMENTS relationships
- **Module Node**: Represents a code module/file with qualified_name, name, and path, connected to Functions and Classes via DEFINES relationships
- **Package Node**: Represents a code package, connected to Modules via containment relationships
- **Call Relationship**: Directed edge (CALLS) between Function/Method nodes indicating invocation
- **Inheritance Relationship**: Directed edge (INHERITS) between Class nodes indicating parent-child relationships
- **Import Relationship**: Directed edge (IMPORTS) between Module/Function nodes indicating dependencies
- **Structural Query**: User request for relationship information (callers, hierarchy, dependencies, implementations, call graph)
- **Cypher Query**: Expert-mode raw Cypher query string with optional parameters

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Pre-built structural query tools respond in under 50ms for codebases with up to 10,000 nodes
- **SC-002**: All 6 pre-built structural query tools (callers, hierarchy, dependencies, exports, implementations, call graph) are operational and tested
- **SC-003**: Expert-mode Cypher tool successfully executes valid queries and returns formatted results
- **SC-004**: Graph indexing excludes all documentation file types (*.md, *.mdx, *.txt, *.rst, *.adoc, *.pdf)
- **SC-005**: No semantic search code remains in codebase (0 references to Qdrant, embeddings, vector_store)
- **SC-006**: Documentation clearly distinguishes code-graph-rag as structural query tool, directing users to vector-search-mcp for semantic search and mcp-ragdocs for documentation
- **SC-007**: Natural language to Cypher query tool includes guidance to use pre-built tools for simple queries
- **SC-008**: Test suite covers all 6 structural query tools with known graph patterns
- **SC-009**: Tool descriptions in MCP registry emphasize "structural relationships" and "graph queries" terminology
- **SC-010**: Dependencies removed from pyproject.toml: qdrant-client and all embedding-related libraries

### Assumptions

1. **Graph Database Availability**: Assumes Memgraph instance is running and accessible at localhost:7687 during operation
2. **Project Isolation**: Assumes existing project-based isolation via CONTAINS relationships continues to function correctly
3. **Backward Compatibility**: Breaking changes are acceptable since this is a major refactoring (v2.0), existing users will need to migrate
4. **Performance Baseline**: Pre-built query performance targets (<50ms) assume standard hardware (modern laptop/server) and reasonably-sized codebases (<100K nodes)
5. **User Skill Levels**: Assumes two user personas: (1) regular developers using pre-built tools, (2) advanced users with Cypher knowledge for expert mode
6. **Integration Architecture**: Assumes vector-search-mcp and mcp-ragdocs are separate, functioning tools that users have access to
7. **Graph Schema Stability**: Assumes existing graph schema (node types, relationship types, properties) remains unchanged during this refactoring
8. **Error Handling Defaults**: Assumes standard error handling patterns (user-friendly messages, graceful degradation) without specific UX requirements
9. **Documentation Standards**: Assumes README follows markdown best practices and is the primary user-facing documentation
10. **Testing Infrastructure**: Assumes existing test infrastructure (pytest, stress_test.py) can be adapted for structural query testing

### Out of Scope

- **Data Migration**: Migration of existing vector embeddings or semantic search data is not included; users re-index from scratch
- **Visualization UI**: Call graph and hierarchy visualization in graphical UI format is not included; tools return data structures only
- **Multi-Database Support**: Support for graph databases other than Memgraph is not included
- **Natural Language Improvements**: Enhancements to NL→Cypher translation quality beyond updating descriptions is not included
- **Performance Optimization**: Advanced query optimization, caching strategies, or database tuning beyond basic requirements is not included
- **Authentication/Authorization**: User access control, multi-tenancy, or permission systems are not included
- **API Versioning**: Formal API versioning or deprecation management for breaking changes is not included
- **Incremental Graph Updates**: Smart differential updates based on code changes is not included; full re-indexing is expected
- **Cross-Project Queries**: Querying across multiple projects simultaneously is not included; queries target one project at a time
- **Export Formats**: Export of query results to CSV, JSON, or other formats is not included; results are text-formatted

### Dependencies

- **Memgraph Database**: Requires running Memgraph instance (Community Edition or higher)
- **Existing Graph Schema**: Depends on current node types (Function, Method, Class, Module, File, Package) and relationship types (CALLS, DEFINES, INHERITS, IMPLEMENTS, IMPORTS)
- **Tree-sitter Integration**: Depends on existing Tree-sitter parsing for code analysis
- **MCP Protocol**: Depends on MCP server framework for tool registration and invocation
- **Python Environment**: Requires Python 3.12+ environment with pymgclient for Memgraph connectivity
- **Complementary Tools**: Assumes users have access to vector-search-mcp for semantic queries and mcp-ragdocs for documentation search

### Non-Functional Requirements

- **Performance**: Pre-built queries must execute in <50ms for typical codebases; graph traversal operations complete in <100ms
- **Reliability**: Tool must gracefully handle database connection failures with clear error messaging
- **Usability**: Error messages must clearly indicate query issues and suggest corrective actions
- **Maintainability**: Code must follow existing project structure and patterns for future extensibility
- **Documentation Quality**: All tool descriptions must be clear to non-expert users; expert mode must include schema documentation
- **Testing Coverage**: All structural query tools must have comprehensive test coverage with known graph patterns
