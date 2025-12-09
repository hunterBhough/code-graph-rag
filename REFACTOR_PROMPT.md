# Task: Transform code-graph-rag into a Specialized Graph Query Engine

## Context
You are refactoring code-graph-rag to be a specialized "Graph Query Engine" in a three-tool architecture:
- **vector-search-mcp**: Code discovery via semantic + keyword search (different tool)
- **code-graph-rag**: Graph query engine for structural relationships (YOU)
- **mcp-ragdocs**: Documentation search (different tool)

Currently there's significant overlap with vector-search-mcp (both do semantic code search). We're eliminating redundancy and hyper-focusing this tool on what ONLY a knowledge graph can do: structural relationships, call graphs, dependencies, and complex multi-hop queries.

## Goal
Remove semantic search functionality and transform this into a pure graph query engine with fast, pre-built structural queries and expert-mode Cypher access.

## Required Changes

### 1. Remove Semantic Search Functionality

**Delete these files**:
```bash
rm codebase_rag/tools/semantic_search.py
rm codebase_rag/vector_store.py
rm codebase_rag/embedder.py
rm codebase_rag/unixcoder.py  # if unused elsewhere
```

**Update `codebase_rag/graph_updater.py`**:
- Remove `_generate_semantic_embeddings()` method (around line 448)
- Remove embedding-related imports:
  ```python
  # Remove these
  from .embedder import embed_code
  from .vector_store import store_embedding
  ```
- Remove Qdrant client initialization
- Remove `EMBEDDING_*` config checks

**Update `codebase_rag/config.py`**:
- Remove or comment out all `EMBEDDING_*` settings (lines 78-83):
  ```python
  # REMOVED: Semantic search now handled by vector-search-mcp
  # EMBEDDING_ENDPOINT: str = "http://localhost:8082"
  # EMBEDDING_MODEL: str = "bge-m3"
  # ...
  ```

**Update `codebase_rag/mcp/tools.py`**:
- Remove semantic search tool from `_tools` registry
- Remove semantic search imports

**Update `pyproject.toml`**:
- Remove `qdrant-client` from dependencies
- Remove or empty the `semantic` extra group:
  ```toml
  [project.optional-dependencies]
  # semantic = []  # Removed - use vector-search-mcp instead
  ```

### 2. Eliminate Documentation Indexing

**Rationale**: mcp-ragdocs handles all documentation. Code-graph-rag should ONLY index code structure.

**Update `codebase_rag/graph_updater.py`**:

Find the `IGNORED_PATTERNS` list and add:
```python
IGNORED_PATTERNS = [
    # ... existing patterns ...
    "**/*.md",           # Markdown docs
    "**/*.mdx",          # MDX docs
    "**/*.txt",          # Text files
    "**/*.rst",          # ReStructuredText
    "**/*.adoc",         # AsciiDoc
    "**/*.asciidoc",     # AsciiDoc alt extension
    "**/docs/**",        # Documentation directories
    "**/documentation/**",
    "**/README*",        # README files
    "**/*.pdf",          # PDFs
]
```

**Update README/CLAUDE.md**:
- Clarify that code-graph-rag is CODE ONLY
- Documentation search is handled by mcp-ragdocs
- Remove references to indexing documentation

### 3. Add Pre-Built Structural Query Tools

**New file**: `codebase_rag/tools/structural_queries.py`

See the complete implementation in the appendix below. This file provides:
- `get_function_callers()` - Find what calls a function
- `get_class_hierarchy()` - Get inheritance tree
- `get_function_dependencies()` - Get imports and calls
- `get_module_exports()` - Get public API of a module
- `find_implementations()` - Find implementations of interface/base class
- `get_call_graph()` - Generate call graph from entry point
- `create_structural_query_tools()` - Factory for MCP tools

### 4. Add Expert-Mode Cypher Query Tool

**Update `codebase_rag/tools/codebase_query.py`**:

Add a new function:
```python
def create_execute_cypher_tool(ingestor: MemgraphIngestor) -> Tool:
    """Create a tool for direct Cypher query execution (expert mode)."""

    async def execute_cypher_query(
        cypher_query: str,
        parameters: dict[str, Any] | None = None
    ) -> str:
        """Execute a Cypher query directly against the knowledge graph (EXPERT MODE).

        Use this when pre-built tools don't cover your use case. Requires knowledge
        of the graph schema and Cypher query language.

        SCHEMA:
        - Nodes: Function, Method, Class, Module, File, Package, ExternalPackage, Project
        - Relationships: CALLS, DEFINES, DEFINES_METHOD, INHERITS, IMPLEMENTS, IMPORTS, CONTAINS
        - Properties: qualified_name, name, start_line, end_line, path, etc.

        Examples:
          "MATCH (f:Function)-[:CALLS]->(target:Function {name: 'login'}) RETURN f.qualified_name"
          "MATCH (c:Class)-[:INHERITS*]->(base:Class {name: 'BaseModel'}) RETURN c.name"

        Args:
            cypher_query: Valid Cypher query string
            parameters: Optional parameters for parameterized queries

        Returns:
            Query results formatted as text
        """
        logger.info(f"[ExpertQuery] Executing Cypher: {cypher_query[:100]}...")

        try:
            results = ingestor.fetch_all(cypher_query, parameters or {})

            if not results:
                return "Query executed successfully but returned no results."

            # Format results as table
            output = f"Query returned {len(results)} result(s):\n\n"

            # Get column names from first result
            if results:
                columns = list(results[0].keys())
                output += " | ".join(columns) + "\n"
                output += "-" * (len(columns) * 20) + "\n"

                for row in results[:50]:  # Limit to 50 rows
                    output += " | ".join(str(row.get(col, ""))[:50] for col in columns) + "\n"

                if len(results) > 50:
                    output += f"\n... and {len(results) - 50} more rows (truncated)"

            return output

        except Exception as e:
            logger.error(f"Cypher query failed: {e}")
            return f"Cypher query failed: {str(e)}\n\nQuery: {cypher_query}"

    return Tool(execute_cypher_query, name="execute_cypher_query")
```

### 5. Update MCP Tool Registry

**File**: `codebase_rag/mcp/tools.py`

```python
from codebase_rag.tools.structural_queries import create_structural_query_tools
from codebase_rag.tools.codebase_query import create_execute_cypher_tool

class MCPToolsRegistry:
    def __init__(self, project_root: str, ingestor: MemgraphIngestor, cypher_gen: CypherGenerator):
        # ... existing init ...

        # Create structural query tools
        self._structural_tools = create_structural_query_tools(ingestor)
        self._execute_cypher_tool = create_execute_cypher_tool(ingestor)

        # Remove semantic search tools from registry
        # Add structural query tools to registry
        self._tools.update({
            "get_function_callers": ToolMetadata(
                name="get_function_callers",
                description="Find all functions that call the specified function (reverse call graph). "
                "Use this to understand code usage or trace backwards through the call chain.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "qualified_name": {
                            "type": "string",
                            "description": "Full qualified name (e.g., 'myproject.auth.AuthService.login')"
                        },
                        "max_depth": {
                            "type": "integer",
                            "description": "Search depth (1=direct callers, 2=callers of callers, etc.)",
                            "default": 1
                        }
                    },
                    "required": ["qualified_name"]
                },
                handler=self._call_async_tool(self._structural_tools[0]),
                returns_json=True
            ),
            "get_class_hierarchy": ToolMetadata(
                name="get_class_hierarchy",
                description="Get class inheritance hierarchy (parents and children). "
                "Shows what a class inherits from and what inherits from it.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "class_name": {
                            "type": "string",
                            "description": "Class name or qualified name"
                        },
                        "direction": {
                            "type": "string",
                            "description": "'up' (ancestors), 'down' (descendants), 'both' (full tree)",
                            "enum": ["up", "down", "both"],
                            "default": "both"
                        }
                    },
                    "required": ["class_name"]
                },
                handler=self._call_async_tool(self._structural_tools[1]),
                returns_json=True
            ),
            "get_dependencies": ToolMetadata(
                name="get_dependencies",
                description="Get dependencies (imports and calls) for code. "
                "Shows what a function/module imports and what functions it calls.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "qualified_name": {
                            "type": "string",
                            "description": "Function or module qualified name"
                        },
                        "dependency_type": {
                            "type": "string",
                            "description": "Type of dependencies to return",
                            "enum": ["imports", "calls", "all"],
                            "default": "all"
                        }
                    },
                    "required": ["qualified_name"]
                },
                handler=self._call_async_tool(self._structural_tools[2]),
                returns_json=True
            ),
            "get_module_exports": ToolMetadata(
                name="get_module_exports",
                description="Get all public exports from a module. "
                "Shows functions, classes, and variables that a module exports.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "module_name": {
                            "type": "string",
                            "description": "Module name, qualified name, or file path"
                        }
                    },
                    "required": ["module_name"]
                },
                handler=self._call_async_tool(self._structural_tools[3]),
                returns_json=True
            ),
            "find_implementations": ToolMetadata(
                name="find_implementations",
                description="Find all implementations of an interface or subclasses of a base class.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "interface_or_base": {
                            "type": "string",
                            "description": "Interface or base class name"
                        }
                    },
                    "required": ["interface_or_base"]
                },
                handler=self._call_async_tool(self._structural_tools[4]),
                returns_json=True
            ),
            "get_call_graph": ToolMetadata(
                name="get_call_graph",
                description="Generate a call graph starting from an entry point function. "
                "Shows the tree of function calls emanating from a starting point.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "entry_point": {
                            "type": "string",
                            "description": "Starting function qualified name"
                        },
                        "max_depth": {
                            "type": "integer",
                            "description": "How deep to traverse",
                            "default": 3
                        }
                    },
                    "required": ["entry_point"]
                },
                handler=self._call_async_tool(self._structural_tools[5]),
                returns_json=True
            ),
            "execute_cypher_query": ToolMetadata(
                name="execute_cypher_query",
                description="Execute custom Cypher query (EXPERT MODE - requires schema knowledge). "
                "Use when pre-built tools don't cover your use case.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "cypher_query": {
                            "type": "string",
                            "description": "Valid Cypher query string"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Optional parameters for parameterized queries"
                        }
                    },
                    "required": ["cypher_query"]
                },
                handler=self._call_async_tool(self._execute_cypher_tool),
                returns_json=False
            ),
        })

    def _call_async_tool(self, tool: Tool):
        """Helper to call async pydantic-ai tools from sync MCP handlers."""
        async def wrapper(**kwargs):
            return await tool.function(**kwargs)
        return wrapper
```

### 6. Optimize Natural Language Query Tool

**Update `codebase_rag/tools/codebase_query.py`**:

Update the tool description to focus on STRUCTURAL queries:

```python
async def query_codebase_knowledge_graph(natural_language_query: str) -> GraphData:
    """
    Query the codebase knowledge graph using natural language for STRUCTURAL questions.

    Use this tool for questions about CODE STRUCTURE and RELATIONSHIPS:
    ✅ "Find all functions in module X that call functions in module Y"
    ✅ "Show me all classes that implement multiple interfaces"
    ✅ "What are the transitive dependencies of module Z?"
    ✅ "Find all functions that indirectly call error handlers"

    For SIMPLE structural queries, use pre-built tools instead (faster, free):
    - "What calls function X?" → Use get_function_callers (faster)
    - "Show class hierarchy for Y" → Use get_class_hierarchy (faster)

    For FINDING code by functionality or intent, use vector-search-mcp:
    - "Find error handling code" → vector-search-mcp
    - "Locate authentication functions" → vector-search-mcp

    This tool uses an LLM to generate Cypher queries, which costs tokens and takes ~2-5 seconds.
    Use pre-built tools when possible for better performance.

    Args:
        natural_language_query: Your question about code structure or relationships

    Returns:
        Graph query results with nodes and relationships
    """
```

### 7. Update README and Documentation

**File**: `README.md`

Complete rewrite focusing on graph query capabilities:

```markdown
# code-graph-rag: Knowledge Graph Query Engine for Codebases

A specialized graph database tool for exploring code structure, relationships,
and dependencies using Memgraph and Cypher queries.

## What This Tool Does

code-graph-rag builds a knowledge graph of your codebase and provides tools to query:

✅ **Call graphs** - What calls this function? What does it call?
✅ **Dependencies** - Import relationships and function calls
✅ **Class hierarchies** - Inheritance trees and implementations
✅ **Module exports** - Public API surfaces
✅ **Structural analysis** - Complex multi-hop relationship queries
✅ **Expert queries** - Direct Cypher access for power users

## What This Tool Does NOT Do

❌ **Semantic code search** - Use `vector-search-mcp` instead
❌ **Documentation search** - Use `mcp-ragdocs` instead
❌ **Find code by intent** - Use `vector-search-mcp` instead

This tool is for understanding HOW code relates, not FINDING code by what it does.

## Three-Tool Ecosystem

This is part of a specialized tool ecosystem:

| Tool | Purpose | Use When |
|------|---------|----------|
| **vector-search-mcp** | Find code by functionality | "Find auth code" |
| **code-graph-rag** (this) | Explore structure & relationships | "What calls this?" |
| **mcp-ragdocs** | Search documentation | "Show API docs" |

## MCP Tools Provided

### Pre-Built Structural Queries (Fast, <50ms)

1. **`get_function_callers`** - Reverse call graph
   ```python
   get_function_callers("myproject.auth.login", max_depth=2)
   # Returns: All functions that call login, up to 2 levels deep
   ```

2. **`get_class_hierarchy`** - Inheritance tree
   ```python
   get_class_hierarchy("AuthService", direction="both")
   # Returns: Parents (what it extends) and children (what extends it)
   ```

3. **`get_dependencies`** - Imports + function calls
   ```python
   get_dependencies("myproject.auth.login", dependency_type="all")
   # Returns: What this function imports and what it calls
   ```

4. **`get_module_exports`** - Public API surface
   ```python
   get_module_exports("myproject.auth")
   # Returns: All functions and classes exported by this module
   ```

5. **`find_implementations`** - Interface implementors
   ```python
   find_implementations("IAuthProvider")
   # Returns: All classes that implement IAuthProvider
   ```

6. **`get_call_graph`** - Forward call tree
   ```python
   get_call_graph("myproject.main", max_depth=3)
   # Returns: All functions called from main, up to 3 levels deep
   ```

### Expert Mode (Requires Cypher Knowledge)

7. **`execute_cypher_query`** - Direct Cypher access
   ```cypher
   execute_cypher_query("""
     MATCH (f:Function)-[:CALLS*1..3]->(target:Function)
     WHERE target.name = 'authenticate'
     RETURN f.qualified_name, length(path) AS depth
     ORDER BY depth
   """)
   ```

8. **`query_code_graph`** - Natural language → Cypher (uses LLM, slower)
   ```python
   query_code_graph("Find all functions that transitively call error handlers")
   # LLM generates Cypher query, executes it, returns results
   ```

### Utilities

9. **`index_repository`** - Build/update the knowledge graph
10. **`get_code_snippet`** - Retrieve source code by qualified name

## Workflow Example

```
1. DISCOVERY (use vector-search-mcp):
   Search: "Find authentication functions"
   → Result: myproject.auth.AuthService.login

2. STRUCTURE ANALYSIS (use code-graph-rag):
   get_function_callers("myproject.auth.AuthService.login")
   → Shows: 15 functions call this

   get_dependencies("myproject.auth.AuthService.login")
   → Shows: Imports bcrypt, calls validate_credentials

3. DOCUMENTATION (use mcp-ragdocs):
   Search: "authentication architecture"
   → Returns: Auth design docs, API specs
```

## Installation

### Prerequisites
- Python 3.12+
- Memgraph database (Docker recommended)

### Setup Memgraph
```bash
docker compose up -d
# Memgraph runs on localhost:7687
# Lab UI available at http://localhost:3000
```

### Install code-graph-rag
```bash
cd code-graph-rag
uv sync
```

## Usage

### Index a Project
```bash
uv run python -m codebase_rag.main start --repo-path /path/to/project --update-graph
```

### Use as MCP Server
```bash
uv run python -m codebase_rag.mcp.server
```

## Graph Schema

**Nodes**:
- `Project` - Project container (for multi-project isolation)
- `Function`, `Method` - Standalone and class-bound functions
- `Class` - Class definitions
- `Module` - Python modules/files
- `File`, `Folder` - File system structure
- `Package` - Python packages
- `ExternalPackage` - Third-party dependencies

**Relationships**:
- `CALLS` - Function → Function (call graph)
- `DEFINES` - Module → Function/Class (containment)
- `DEFINES_METHOD` - Class → Method (class methods)
- `INHERITS` - Class → Class (inheritance)
- `IMPLEMENTS` - Class → Interface (implementation)
- `IMPORTS` - Module → Module/Package (dependencies)
- `CONTAINS` - Project → Node (project isolation)

**Properties**:
- `qualified_name` - Unique identifier (e.g., "myproject.auth.login")
- `name` - Display name
- `start_line`, `end_line` - Source code location
- `path` - File path
- `decorators`, `docstring`, etc.

## Performance

| Query Type | Performance |
|------------|-------------|
| Pre-built structural queries | <50ms |
| Direct Cypher queries | <100ms |
| NL → Cypher queries (LLM) | 2-5 seconds |

**Recommendation**: Use pre-built tools whenever possible for best performance.

## Configuration

**Memgraph Settings** (`.env` or environment):
```bash
MEMGRAPH_HOST=localhost
MEMGRAPH_PORT=7687
MEMGRAPH_BATCH_SIZE=1000
```

**Project Isolation**:
Each indexed project gets a `Project` node. All queries automatically filter by project using `CONTAINS` relationships. This works with Memgraph Community Edition (no enterprise license required).

## Language Support

Supported via Tree-sitter AST parsing:
- Python
- TypeScript / JavaScript
- Go
- Rust
- C / C++
- Java
- Lua

## When to Use Each Tool

| Task | Tool |
|------|------|
| "Find error handling code" | vector-search-mcp |
| "What calls this function?" | code-graph-rag |
| "Show me the API docs" | mcp-ragdocs |
| "Functions similar to X" | vector-search-mcp |
| "Class inheritance tree" | code-graph-rag |
| "How does auth work?" | mcp-ragdocs |
| "Locate rate limiting code" | vector-search-mcp |
| "What imports this module?" | code-graph-rag |
| "ADR for service layer" | mcp-ragdocs |

## Migration from v1.x

**Breaking Changes**:
- ❌ Removed semantic search functionality (moved to vector-search-mcp)
- ❌ Removed Qdrant vector database dependency
- ❌ Documentation files no longer indexed (use mcp-ragdocs)

**New Features**:
- ✅ 6 fast pre-built structural query tools
- ✅ Expert-mode Cypher query access
- ✅ 10x faster common queries (no LLM needed)
- ✅ Clearer role separation

**Upgrade Path**:
1. Install vector-search-mcp for semantic code search
2. Install mcp-ragdocs for documentation search
3. Update to code-graph-rag v2.0
4. Re-index your project (will skip docs automatically)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT
```

### 8. Update CLAUDE.md

**File**: `CLAUDE.md`

Update the sections about what the tool does:

```markdown
# CLAUDE.md

## Repository Overview

Code-graph-rag is a **graph-based code structure query engine** that analyzes
codebases using Tree-sitter, builds knowledge graphs in Memgraph, and enables
querying of code relationships and structure.

**Key capabilities**:
- Multi-language codebase analysis (Python, TypeScript, Go, Rust, etc.)
- Knowledge graph storage in Memgraph
- Structural queries: call graphs, dependencies, hierarchies
- Pre-built query tools for common patterns
- Expert Cypher query access

**NOT included** (handled by other tools):
- Semantic code search → use vector-search-mcp
- Documentation indexing → use mcp-ragdocs

## Common Tasks

### Query Call Graphs
```python
# What calls this function?
get_function_callers("myproject.auth.login")

# What does this function call?
get_dependencies("myproject.auth.login", dependency_type="calls")
```

### Explore Class Hierarchies
```python
get_class_hierarchy("AuthService", direction="both")
```

### Find Implementations
```python
find_implementations("IAuthProvider")
```

## Three-Tool Architecture

| Tool | Role | Use For |
|------|------|---------|
| vector-search-mcp | Code Discovery | Finding code by functionality |
| code-graph-rag | Graph Queries | Structural relationships |
| mcp-ragdocs | Documentation | Specs, guides, ADRs |
```

### 9. Update Tests

**Update `stress_test.py`**:

Remove semantic search tests, add structural query tests:

```python
def test_structural_queries():
    """Test pre-built structural query tools."""

    logger.info("=== Testing Structural Query Tools ===")

    queries = [
        ("get_function_callers", {
            "qualified_name": "code-graph-rag.codebase_rag.mcp.tools.MCPToolsRegistry.query_code_graph"
        }),
        ("get_class_hierarchy", {
            "class_name": "MCPToolsRegistry",
            "direction": "both"
        }),
        ("get_dependencies", {
            "qualified_name": "code-graph-rag.codebase_rag.graph_updater",
            "dependency_type": "all"
        }),
        ("get_module_exports", {
            "module_name": "codebase_rag.services.graph_service"
        }),
        ("find_implementations", {
            "interface_or_base": "Tool"
        }),
        ("get_call_graph", {
            "entry_point": "code-graph-rag.codebase_rag.main.main",
            "max_depth": 2
        }),
    ]

    for tool_name, params in queries:
        logger.info(f"Testing {tool_name}...")
        start = time.time()

        # Execute tool
        result = execute_mcp_tool(tool_name, params)

        duration = time.time() - start
        logger.success(f"  ✓ {tool_name} completed in {duration:.2f}s")

        # Verify result is not empty
        assert result is not None
        assert len(str(result)) > 0

    logger.success("All structural query tests passed!")


def test_expert_cypher_query():
    """Test expert Cypher query tool."""

    logger.info("=== Testing Expert Cypher Query ===")

    # Simple query: count all functions
    result = execute_mcp_tool("execute_cypher_query", {
        "cypher_query": "MATCH (f:Function) RETURN count(f) AS function_count"
    })

    assert "function_count" in str(result)
    logger.success("Expert Cypher query test passed!")
```

## Implementation Order

1. **Remove semantic search** (delete files, remove imports) - 30 min
2. **Add doc exclusions** to graph_updater.py - 10 min
3. **Create structural_queries.py** with 6 tools - 2 hours
4. **Add execute_cypher_query** expert tool - 30 min
5. **Update MCP registry** with new tools - 45 min
6. **Update tool descriptions** for clarity - 30 min
7. **Rewrite README** to emphasize graph focus - 1 hour
8. **Update CLAUDE.md** - 15 min
9. **Update tests** (remove semantic, add structural) - 45 min
10. **Update pyproject.toml** dependencies - 10 min

**Total estimated time: 6 hours**

## Success Criteria

- [ ] All semantic search code removed (Qdrant, embeddings, vector_store.py)
- [ ] Documentation files excluded from indexing
- [ ] 6 pre-built structural query tools working and tested
- [ ] Expert Cypher query tool available
- [ ] Tool descriptions emphasize "structural/relational" focus
- [ ] README clearly differentiates from vector-search-mcp
- [ ] Tests cover all structural query tools
- [ ] No references to "semantic search" in user-facing docs
- [ ] Faster query times (pre-built queries <50ms)
- [ ] Migration guide for v1.x users in README

## Appendix: Complete structural_queries.py Implementation

See the full implementation at the end of this document. Key functions:
- `get_function_callers(ingestor, qualified_name, max_depth)`
- `get_class_hierarchy(ingestor, class_name, direction)`
- `get_function_dependencies(ingestor, qualified_name, dependency_type)`
- `get_module_exports(ingestor, module_name)`
- `find_implementations(ingestor, interface_or_base)`
- `get_call_graph(ingestor, entry_point, max_depth)`
- `create_structural_query_tools(ingestor)` - MCP tool factory

## Notes

- Keep NL → Cypher tool (`query_code_graph`) but update description to emphasize it's for complex structural queries only
- Pre-built tools should be the default recommendation
- Expert Cypher tool is for power users who know the schema
- All queries should be project-aware (use Project isolation)
- Log query performance to help identify slow queries

## Final Architecture

```
code-graph-rag v2.0
├── Graph Indexing
│   └── Tree-sitter → Memgraph (CODE ONLY)
├── Structural Query Tools
│   ├── get_function_callers
│   ├── get_class_hierarchy
│   ├── get_dependencies
│   ├── get_module_exports
│   ├── find_implementations
│   └── get_call_graph
├── Expert Tools
│   ├── execute_cypher_query (direct Cypher)
│   └── query_code_graph (NL → Cypher)
└── Utilities
    ├── index_repository
    └── get_code_snippet

NOT INCLUDED:
✗ Vector search → vector-search-mcp
✗ Semantic search → vector-search-mcp
✗ Documentation → mcp-ragdocs
```

Focus on being the **best graph query engine** for code structure and relationships.
