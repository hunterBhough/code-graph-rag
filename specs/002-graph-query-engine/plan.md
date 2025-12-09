# Implementation Plan: Transform code-graph-rag into Specialized Graph Query Engine

**Branch**: `002-graph-query-engine` | **Date**: 2025-12-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-graph-query-engine/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Transform code-graph-rag from a hybrid semantic/structural search tool into a specialized graph query engine focused exclusively on code structure and relationships. This refactoring removes all semantic search functionality (vector stores, embeddings, documentation indexing) and clarifies the tool's role as one component in a three-tool architecture alongside vector-search-mcp (semantic/keyword search) and mcp-ragdocs (documentation search). The system will provide 6 pre-built structural query tools (callers, hierarchy, dependencies, exports, implementations, call graphs) plus expert-mode Cypher execution, all optimized for <50ms response times.

## Technical Context

**Language/Version**: Python 3.12+ (requires-python >= 3.12)
**Primary Dependencies**: pymgclient 1.4.0 (Memgraph client), tree-sitter 0.25.0 (AST parsing), mcp 1.21.1+ (MCP protocol), pydantic-ai-slim 0.2.18+ (LLM integration for NL→Cypher), loguru 0.7.3 (logging)
**Storage**: Memgraph Community Edition (graph database at localhost:7687), project-based isolation via CONTAINS relationships
**Testing**: pytest 8.4.1+, pytest-asyncio 1.0.0+, pytest-xdist 3.8.0+ (parallel test execution)
**Target Platform**: Cross-platform Python (Linux, macOS, Windows) via MCP stdio transport
**Project Type**: Single Python package (codebase_rag) with MCP server entry point
**Performance Goals**: <50ms for pre-built structural queries, <100ms for graph traversal operations (typical codebases <10K nodes)
**Constraints**: Must maintain backward compatibility with existing graph schema (node types: Function, Method, Class, Module, File, Package; relationships: CALLS, DEFINES, INHERITS, IMPLEMENTS, IMPORTS, CONTAINS), no database migrations required
**Scale/Scope**: Support codebases up to 100K nodes (10K nodes nominal), handle 1000+ callers without degradation, truncate large result sets (>50 rows expert mode, >100 pre-built queries)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principles Evaluation

**I. Graph-First Intelligence** ✅ PASS
- Feature exclusively focuses on graph queries (structural relationships)
- All semantic search code removed (vector_store, embeddings)
- Natural language queries translate to Cypher → graph results
- Pre-built tools generate Cypher queries internally
- **Alignment**: This refactoring STRENGTHENS graph-first intelligence by removing non-graph search methods

**II. Multi-Language Universality** ✅ PASS
- No language-specific changes required
- Existing unified schema (Module, Class, Function, Method) maintained
- Tree-sitter parsing continues to support all languages uniformly
- Query tools work identically across Python, JavaScript, TypeScript, Rust, Go, Java, C++, Lua
- **Alignment**: Feature is language-agnostic; structural queries apply universally

**III. AI-Native Interface** ✅ PASS
- MCP tools remain the primary interface
- Tool descriptions updated to emphasize structural/relational queries
- Natural language → Cypher translation preserved (using pydantic-ai LLM)
- All 6 pre-built tools + expert mode exposed via MCP
- **Alignment**: Feature enhances AI-native interface by clarifying tool purpose and reducing confusion about capabilities

**IV. Parse Precision** ✅ PASS
- No changes to Tree-sitter AST parsing
- All code extraction continues via Tree-sitter grammars
- Function/class boundaries derived from AST nodes only
- **Alignment**: Feature does not affect parsing; maintains AST-only approach

**V. Safe Code Operations** ✅ PASS
- Feature is read-only (query operations only)
- No code modification tools added
- Graph indexing continues to be read-only AST analysis
- **Alignment**: Feature maintains read-only safety posture

### Technical Standards Evaluation

**Database Requirements** ✅ PASS
- Memgraph remains the required database
- Project-based isolation via CONTAINS relationships unchanged
- No schema changes required (existing node/relationship types sufficient)
- **Alignment**: No database requirement changes

**Embedding Requirements** ⚠️ REMOVED BY DESIGN
- Feature explicitly removes all semantic search embeddings
- Qdrant client dependencies removed
- UniXcoder embedding models removed
- **Justification**: Semantic search is delegated to vector-search-mcp tool; embedding requirements no longer apply to code-graph-rag

**Configuration Standards** ✅ PASS
- LLM provider configuration (for NL→Cypher) continues via environment variables
- No hardcoded endpoints or model names
- Mixed provider support maintained
- **Alignment**: Existing configuration patterns preserved

### Gate Decision: ✅ PASS

**Summary**: All applicable constitution principles align with this feature. The removal of semantic search (embedding requirements) is by design and strengthens the graph-first intelligence principle. No violations or complexity justifications required.

## Project Structure

### Documentation (this feature)

```text
specs/002-graph-query-engine/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - Technology decisions for structural queries
├── data-model.md        # Phase 1 output - Entity definitions for query tools
├── quickstart.md        # Phase 1 output - User guide for graph queries
├── contracts/           # Phase 1 output - MCP tool schemas
│   ├── query_callers.json          # Find function callers tool schema
│   ├── query_hierarchy.json        # Class hierarchy tool schema
│   ├── query_dependencies.json     # Module/function dependencies schema
│   ├── query_exports.json          # Module exports schema
│   ├── query_implementations.json  # Interface implementations schema
│   ├── query_call_graph.json       # Call graph generation schema
│   └── query_cypher.json           # Expert mode Cypher schema
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
codebase_rag/
├── mcp/
│   ├── server.py           # MCP server entry point (update tool registry)
│   └── tools.py            # Tool definitions and handlers (replace semantic search tools)
├── services/
│   ├── graph_service.py    # Memgraph interaction (unchanged)
│   └── llm.py              # CypherGenerator for NL→Cypher (unchanged)
├── tools/                  # NEW: Pre-built query tool implementations
│   ├── __init__.py
│   ├── callers.py          # Find function callers (direct + multi-hop)
│   ├── hierarchy.py        # Class inheritance hierarchy queries
│   ├── dependencies.py     # Module/function dependency analysis
│   ├── exports.py          # Module public exports
│   ├── implementations.py  # Interface/base class implementations
│   └── call_graph.py       # Call graph generation
├── parsers/                # Tree-sitter parsers (unchanged)
├── config.py               # Settings (remove Qdrant/embedding config)
├── main.py                 # CLI entry point (remove semantic search commands)
└── graph_loader.py         # Graph indexing (exclude documentation files)

# REMOVED (semantic search functionality):
# - codebase_rag/vector_store.py
# - codebase_rag/embedder.py
# - codebase_rag/tools/semantic_search.py
# - codebase_rag/unixcoder.py
# - codebase_rag/providers/embedders/ (directory)

tests/
├── unit/                   # NEW: Organized test structure
│   ├── test_callers.py
│   ├── test_hierarchy.py
│   ├── test_dependencies.py
│   ├── test_exports.py
│   ├── test_implementations.py
│   └── test_call_graph.py
├── integration/
│   └── test_mcp_tools_integration.py  # Update for new tool registry
└── conftest.py             # Shared fixtures for known graph patterns
```

**Structure Decision**: Single Python package structure maintained. New `codebase_rag/tools/` directory created to house pre-built structural query implementations. Semantic search files removed. Test suite reorganized to unit/integration structure for clarity.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. This section is empty.

## Phase 0: Research & Technology Decisions

**Objective**: Resolve all technical unknowns and establish design patterns for structural query tools.

### Research Tasks

1. **Cypher Query Patterns for Structural Relationships**
   - Research optimal Cypher patterns for caller/callee traversal (depth-limited)
   - Research class hierarchy queries (ancestors vs descendants vs both)
   - Research dependency analysis patterns (imports + call relationships)
   - Research call graph generation (BFS vs DFS, truncation strategies)
   - **Output**: Cypher pattern library in research.md

2. **Performance Optimization Strategies**
   - Research Memgraph query optimization (index usage, query hints)
   - Research result set truncation strategies (pagination vs hard limits)
   - Research connection pooling best practices for pymgclient
   - **Output**: Performance recommendations in research.md

3. **Error Handling Patterns**
   - Research user-friendly error messages for non-existent nodes
   - Research circular dependency detection in class hierarchies
   - Research timeout handling for complex queries
   - **Output**: Error handling guidelines in research.md

4. **MCP Tool Schema Best Practices**
   - Research MCP inputSchema patterns for optional parameters
   - Research JSON response formatting for graph results
   - Research tool description conventions for AI consumption
   - **Output**: MCP schema design patterns in research.md

### Research Consolidation

Research findings will be documented in `specs/002-graph-query-engine/research.md` with the following structure:

- **Cypher Patterns**: Recommended patterns for each query type (callers, hierarchy, dependencies, call graphs)
- **Performance Strategy**: Index recommendations, query optimization techniques, truncation thresholds
- **Error Handling**: Standard error messages, edge case handling (circular deps, missing nodes, timeouts)
- **MCP Tool Design**: Schema patterns, parameter validation, response formatting

## Phase 1: Design & Contracts

**Prerequisites**: `research.md` complete

### 1. Data Model Definition (`data-model.md`)

Extract entities from feature spec and research findings:

**Query Request Entities**:
- `CallersQuery`: `{function_name: str, max_depth: int = 1, include_path: bool = False}`
- `HierarchyQuery`: `{class_name: str, direction: "up" | "down" | "both", max_depth: int = 10}`
- `DependenciesQuery`: `{target: str, type: "imports" | "calls" | "all", include_transitive: bool = False}`
- `ExportsQuery`: `{module_name: str, include_private: bool = False}`
- `ImplementationsQuery`: `{interface_name: str, include_indirect: bool = False}`
- `CallGraphQuery`: `{entry_point: str, max_depth: int = 3, max_nodes: int = 50}`
- `CypherQuery`: `{query: str, parameters: dict = {}, limit: int = 50}`

**Query Response Entities**:
- `CallerResult`: `{callers: list[FunctionNode], call_chains: list[list[str]] | None}`
- `HierarchyResult`: `{hierarchy_tree: dict, ancestors: list[ClassNode], descendants: list[ClassNode]}`
- `DependenciesResult`: `{imports: list[ModuleNode], calls: list[FunctionNode], dependency_graph: dict}`
- `ExportsResult`: `{exports: list[FunctionNode | ClassNode], module_info: ModuleNode}`
- `ImplementationsResult`: `{implementations: list[ClassNode], inheritance_depth: dict}`
- `CallGraphResult`: `{nodes: list[FunctionNode], edges: list[CallEdge], truncated: bool, total_nodes: int}`
- `CypherResult`: `{rows: list[dict], columns: list[str], row_count: int, truncated: bool}`

**Graph Node Entities** (from existing schema):
- `FunctionNode`: `{qualified_name: str, name: str, start_line: int, end_line: int, path: str}`
- `MethodNode`: `{qualified_name: str, name: str, class_name: str, start_line: int, end_line: int, path: str}`
- `ClassNode`: `{qualified_name: str, name: str, start_line: int, end_line: int, path: str}`
- `ModuleNode`: `{qualified_name: str, name: str, path: str}`
- `CallEdge`: `{from_function: str, to_function: str, call_type: "direct" | "method" | "constructor"}`

### 2. API Contracts (`contracts/`)

Generate MCP tool schemas for each pre-built query tool:

**Tool 1: query_callers** (`contracts/query_callers.json`)
```json
{
  "name": "query_callers",
  "description": "Find all functions/methods that call a specified function. Supports multi-level caller chains up to max_depth.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "function_name": {"type": "string", "description": "Qualified name of the function to find callers for"},
      "max_depth": {"type": "integer", "default": 1, "description": "Maximum depth for caller chains (1=direct callers only)"},
      "include_path": {"type": "boolean", "default": false, "description": "Include full call chain paths in results"}
    },
    "required": ["function_name"]
  }
}
```

**Tool 2: query_hierarchy** (`contracts/query_hierarchy.json`)
```json
{
  "name": "query_hierarchy",
  "description": "Retrieve class inheritance hierarchies showing ancestors (parent classes), descendants (child classes), or both.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "class_name": {"type": "string", "description": "Qualified name of the class to analyze"},
      "direction": {"type": "string", "enum": ["up", "down", "both"], "default": "both", "description": "Direction to traverse: 'up' for ancestors, 'down' for descendants"},
      "max_depth": {"type": "integer", "default": 10, "description": "Maximum depth to traverse hierarchy"}
    },
    "required": ["class_name"]
  }
}
```

**Tool 3: query_dependencies** (`contracts/query_dependencies.json`)
```json
{
  "name": "query_dependencies",
  "description": "Analyze module or function dependencies including imports and function calls.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "target": {"type": "string", "description": "Qualified name of module or function to analyze"},
      "type": {"type": "string", "enum": ["imports", "calls", "all"], "default": "all", "description": "Type of dependencies to retrieve"},
      "include_transitive": {"type": "boolean", "default": false, "description": "Include transitive dependencies (dependencies of dependencies)"}
    },
    "required": ["target"]
  }
}
```

**Tool 4: query_exports** (`contracts/query_exports.json`)
```json
{
  "name": "query_exports",
  "description": "Retrieve all public exports (functions, classes) from a specified module.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "module_name": {"type": "string", "description": "Qualified name of the module"},
      "include_private": {"type": "boolean", "default": false, "description": "Include private members (starting with _)"}
    },
    "required": ["module_name"]
  }
}
```

**Tool 5: query_implementations** (`contracts/query_implementations.json`)
```json
{
  "name": "query_implementations",
  "description": "Find all classes that implement a specified interface or extend a base class.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "interface_name": {"type": "string", "description": "Qualified name of interface or base class"},
      "include_indirect": {"type": "boolean", "default": false, "description": "Include indirect implementations (child classes of implementers)"}
    },
    "required": ["interface_name"]
  }
}
```

**Tool 6: query_call_graph** (`contracts/query_call_graph.json`)
```json
{
  "name": "query_call_graph",
  "description": "Generate a call graph starting from an entry point function, showing all called functions up to max_depth.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "entry_point": {"type": "string", "description": "Qualified name of the entry point function"},
      "max_depth": {"type": "integer", "default": 3, "description": "Maximum depth to traverse call graph"},
      "max_nodes": {"type": "integer", "default": 50, "description": "Maximum number of nodes to return (truncate if exceeded)"}
    },
    "required": ["entry_point"]
  }
}
```

**Tool 7: query_cypher** (`contracts/query_cypher.json`)
```json
{
  "name": "query_cypher",
  "description": "Execute a custom Cypher query against the code graph (expert mode). Requires knowledge of graph schema. For simple queries, prefer pre-built tools (query_callers, query_hierarchy, etc.).",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "Cypher query string"},
      "parameters": {"type": "object", "default": {}, "description": "Query parameters for parameterized queries"},
      "limit": {"type": "integer", "default": 50, "description": "Maximum number of rows to return"}
    },
    "required": ["query"]
  }
}
```

### 3. Quickstart Guide (`quickstart.md`)

Generate user-facing quickstart guide covering:

**Section 1: Overview**
- What is code-graph-rag? (Specialized graph query engine)
- How it differs from vector-search-mcp and mcp-ragdocs
- When to use each tool in the three-tool architecture

**Section 2: Installation & Setup**
- Prerequisites (Memgraph, Python 3.12+)
- MCP server configuration for Claude Code
- Indexing a codebase for the first time

**Section 3: Pre-Built Query Tools**
- Examples for each of the 6 pre-built tools
- Common use cases (finding function usage, refactoring classes, dependency analysis)
- Performance tips (use direct queries instead of expert mode when possible)

**Section 4: Expert Mode**
- When to use expert mode (custom graph queries)
- Graph schema reference (node types, relationship types)
- Example Cypher queries

**Section 5: Troubleshooting**
- "Node not found" errors
- Query timeouts
- Memgraph connection issues

### 4. Agent Context Update

Run `.specify/scripts/bash/update-agent-context.sh claude` to update the Claude-specific agent context file with:
- New pre-built query tools (query_callers, query_hierarchy, query_dependencies, query_exports, query_implementations, query_call_graph, query_cypher)
- Removal of semantic search tools
- Updated technology stack (no Qdrant, no embeddings)

## Phase 2: Task Generation (NOT IN THIS COMMAND)

Phase 2 (task breakdown) is handled by the `/speckit.tasks` command, which generates `tasks.md` based on this plan and the design artifacts created in Phase 0-1.

## Re-Evaluation: Constitution Check (Post-Design)

*To be completed after Phase 1 design artifacts are generated.*

**Graph-First Intelligence**: ✅ PASS (design confirms all queries use Cypher against graph)
**Multi-Language Universality**: ✅ PASS (queries work identically across all supported languages)
**AI-Native Interface**: ✅ PASS (MCP tool schemas designed for LLM consumption)
**Parse Precision**: ✅ PASS (no changes to Tree-sitter parsing)
**Safe Code Operations**: ✅ PASS (read-only query operations only)

**Final Gate Decision**: ✅ PASS - Design aligns with all applicable constitution principles. Ready for task generation.

## Next Steps

1. **Execute Phase 0**: Generate `research.md` by researching Cypher patterns, performance strategies, error handling, and MCP tool design
2. **Execute Phase 1**: Generate `data-model.md`, `contracts/`, and `quickstart.md` based on research findings
3. **Update Agent Context**: Run `.specify/scripts/bash/update-agent-context.sh claude`
4. **Re-evaluate Constitution**: Verify design aligns with principles
5. **Generate Tasks**: Run `/speckit.tasks` to create implementation task breakdown

**Branch**: `002-graph-query-engine` (already created)
**Plan Location**: `/Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag/specs/002-graph-query-engine/plan.md`
