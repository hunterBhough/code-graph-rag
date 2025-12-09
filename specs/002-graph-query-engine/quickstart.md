# Quickstart Guide: Code-Graph-RAG Structural Query Engine

**Last Updated**: 2025-12-08
**Version**: 2.0 (Specialized Graph Query Engine)

## Overview

### What is code-graph-rag?

Code-graph-rag is a **specialized graph query engine** for exploring structural code relationships in your codebase. It analyzes code using Tree-sitter AST parsing, builds a knowledge graph in Memgraph, and provides natural language and structured query tools for exploring function calls, class hierarchies, dependencies, and execution flows.

### Three-Tool Architecture

Code-graph-rag is one component in a three-tool architecture for code intelligence:

1. **code-graph-rag** (this tool): Structural relationships and graph queries
   - Use when: Finding function callers, exploring class hierarchies, analyzing dependencies, generating call graphs
   - Strengths: Fast (<50ms), precise, relationship-focused

2. **vector-search-mcp**: Semantic code search
   - Use when: Finding code by meaning/behavior, keyword search, "find similar functions"
   - Strengths: Fuzzy matching, natural language understanding

3. **mcp-ragdocs**: Documentation search
   - Use when: Searching README files, API docs, code comments, markdown files
   - Strengths: Documentation-focused, supports multiple formats

**When to use code-graph-rag**:
- "Which functions call `auth.login`?"
- "Show me the class hierarchy for `BaseModel`"
- "What does `payment_processor` module depend on?"
- "Generate a call graph from `app.main`"
- "Find all classes that implement `PaymentProvider`"

**When NOT to use code-graph-rag**:
- "Find functions that handle authentication" → Use **vector-search-mcp** (semantic)
- "What does the installation guide say?" → Use **mcp-ragdocs** (documentation)
- "Find code similar to this snippet" → Use **vector-search-mcp** (similarity)

---

## Installation & Setup

### Prerequisites

1. **Python 3.12+** (required)
2. **Memgraph** (graph database)
3. **Docker** (for running Memgraph)

### Step 1: Install Memgraph

```bash
# Using docker-compose (recommended)
cd /path/to/code-graph-rag
docker compose up -d

# Verify Memgraph is running
docker ps | grep memgraph
# Should show memgraph container on port 7687

# Access Memgraph Lab UI (optional)
open http://localhost:3000
```

### Step 2: Install code-graph-rag

```bash
# Clone repository
git clone https://github.com/yourusername/code-graph-rag.git
cd code-graph-rag

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### Step 3: Configure MCP Server for Claude Code

Add to your Claude Code MCP settings (`~/.config/claude-code/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "code-graph": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag",
        "run",
        "-m",
        "codebase_rag.mcp.server"
      ],
      "env": {
        "TARGET_REPO_PATH": "/path/to/your/project"
      }
    }
  }
}
```

**Important**: Replace `/path/to/your/project` with the absolute path to the codebase you want to analyze.

### Step 4: Index Your Codebase

```bash
# From the code-graph-rag directory
uv run graph-code index /path/to/your/project

# With specific project name
uv run graph-code index /path/to/your/project --project-name my-app

# Check indexing progress
tail -f /path/to/your/project/.codebase-intelligence/code-graph/update.log
```

**What gets indexed**:
- Python, JavaScript, TypeScript, Rust, Go, Java, C++, Lua source files
- Functions, classes, methods, imports, function calls
- **Excluded**: Documentation files (*.md, *.txt, *.rst, docs/), test files (configurable)

**Indexing time**: ~10-30 seconds for small projects (<1K files), ~2-5 minutes for large projects (10K+ files)

### Step 5: Verify Setup

```bash
# Query the graph to verify indexing
uv run graph-code query "MATCH (p:Project) RETURN p.name"

# Count indexed functions
uv run graph-code query "MATCH (f:Function) RETURN count(f) as total_functions"

# Or use Memgraph Lab UI
open http://localhost:3000
# Run: MATCH (n) RETURN count(n) as total_nodes
```

---

## Pre-Built Query Tools

Code-graph-rag provides 6 pre-built structural query tools optimized for common operations. These tools are faster and easier to use than expert mode.

### Tool 1: query_callers

**Purpose**: Find all functions that call a specified target function.

**Use Cases**:
- Impact analysis before refactoring
- Understanding function usage
- Finding dead code (functions with no callers)

**Example**:
```python
# Via MCP tool (in Claude Code)
query_callers(
    function_name="auth.services.login",
    max_depth=2,  # Include callers of callers
    include_paths=True
)
```

**Output**:
```json
{
  "query": "Callers of auth.services.login",
  "results": [
    {
      "caller": "auth.api.login_endpoint",
      "file_path": "src/auth/api.py",
      "line_number": 23,
      "depth": 1
    },
    {
      "caller": "auth.api.refresh_token",
      "file_path": "src/auth/api.py",
      "line_number": 67,
      "depth": 2
    }
  ],
  "metadata": {
    "row_count": 2,
    "total_count": 2,
    "truncated": false,
    "execution_time_ms": 12.5
  }
}
```

**Performance**: <50ms for typical codebases

### Tool 2: query_hierarchy

**Purpose**: Retrieve class inheritance hierarchy showing parents, children, or both.

**Use Cases**:
- Understanding OOP relationships
- Safe base class refactoring
- Finding all subclasses

**Example**:
```python
query_hierarchy(
    class_name="auth.models.BaseAuth",
    direction="down",  # Find child classes
    max_depth=5
)
```

**Output**:
```json
{
  "query": "Class hierarchy for auth.models.BaseAuth",
  "hierarchy_tree": {
    "name": "auth.models.BaseAuth",
    "children": [
      {"name": "auth.models.AdminAuth", "depth": 1},
      {"name": "auth.models.UserAuth", "depth": 1}
    ]
  },
  "ancestors": [],
  "descendants": [
    {"class_name": "auth.models.AdminAuth", "depth": 1},
    {"class_name": "auth.models.UserAuth", "depth": 1}
  ],
  "metadata": {
    "row_count": 2,
    "total_count": 2,
    "truncated": false
  }
}
```

**Performance**: <30ms for typical hierarchies

### Tool 3: query_dependencies

**Purpose**: Analyze module or function dependencies (imports + function calls).

**Use Cases**:
- Module extraction planning
- Understanding coupling
- Dependency auditing

**Example**:
```python
query_dependencies(
    target="auth.services",
    dependency_type="all",  # Both imports and calls
    include_transitive=False
)
```

**Output**:
```json
{
  "query": "Dependencies of auth.services",
  "imports": [
    {"module_name": "os", "is_external": true},
    {"module_name": "auth.utils", "is_external": false}
  ],
  "calls": [
    {"function_name": "auth.utils.validate_token", "file_path": "src/auth/utils.py"}
  ],
  "dependency_graph": {
    "auth.services": ["os", "auth.utils", "auth.utils.validate_token"]
  },
  "metadata": {
    "row_count": 3,
    "total_count": 3,
    "truncated": false
  }
}
```

**Performance**: <20ms for direct dependencies, <100ms for transitive

### Tool 4: query_exports

**Purpose**: Retrieve all public exports from a module.

**Use Cases**:
- Understanding module API surface
- Finding public functions/classes
- API documentation generation

**Example**:
```python
query_exports(
    module_name="auth.services",
    include_private=False  # Exclude _private members
)
```

**Output**:
```json
{
  "query": "Exports from auth.services",
  "exports": [
    {"name": "login", "type": "Function", "file_path": "src/auth/services.py", "line_number": 15},
    {"name": "UserService", "type": "Class", "file_path": "src/auth/services.py", "line_number": 42}
  ],
  "module_info": {
    "module_name": "auth.services",
    "file_path": "src/auth/services.py"
  },
  "metadata": {
    "row_count": 2,
    "total_count": 2,
    "truncated": false
  }
}
```

**Performance**: <15ms

### Tool 5: query_implementations

**Purpose**: Find all classes that implement an interface or extend a base class.

**Use Cases**:
- Finding all implementations
- Ensuring consistent behavior across implementers
- Refactoring interfaces

**Example**:
```python
query_implementations(
    interface_name="auth.interfaces.PaymentProvider",
    include_indirect=False  # Direct implementations only
)
```

**Output**:
```json
{
  "query": "Implementations of auth.interfaces.PaymentProvider",
  "implementations": [
    {"class_name": "auth.providers.StripeProvider", "depth": 1},
    {"class_name": "auth.providers.PayPalProvider", "depth": 1}
  ],
  "inheritance_depth": {
    "auth.providers.StripeProvider": 1,
    "auth.providers.PayPalProvider": 1
  },
  "metadata": {
    "row_count": 2,
    "total_count": 2,
    "truncated": false
  }
}
```

**Performance**: <25ms

### Tool 6: query_call_graph

**Purpose**: Generate a call graph starting from an entry point.

**Use Cases**:
- Visualizing execution flow
- Understanding program structure
- Tracing function call paths

**Example**:
```python
query_call_graph(
    entry_point="app.main",
    max_depth=3,
    max_nodes=50  # Truncate if exceeded
)
```

**Output**:
```json
{
  "query": "Call graph from app.main",
  "nodes": [
    {"id": "app.main", "name": "main", "type": "Function"},
    {"id": "app.startup", "name": "startup", "type": "Function"}
  ],
  "edges": [
    {"from": "app.main", "to": "app.startup", "call_type": "direct"}
  ],
  "truncated": false,
  "total_nodes": 2,
  "metadata": {
    "row_count": 2,
    "total_count": 2,
    "truncated": false,
    "execution_time_ms": 22.1
  }
}
```

**Performance**: <200ms for depth 3

---

## Expert Mode: Custom Cypher Queries

For advanced users, `query_cypher` provides full control over graph queries.

### When to Use Expert Mode

- Complex multi-hop queries not covered by pre-built tools
- Custom graph traversals
- Aggregations and statistics
- Advanced filtering

**Recommendation**: Always try pre-built tools first. They're optimized and easier to use.

### Graph Schema Reference

**Node Types**:
- `Project` - Project container (name)
- `Module` - Code module/file (qualified_name, name, path, extension)
- `Package` - Code package/directory (qualified_name, name, path)
- `Class` - Class definition (qualified_name, name, file_path, line_start, line_end)
- `Function` - Standalone function (qualified_name, name, file_path, line_start, line_end, decorators)
- `Method` - Class method (qualified_name, name, class_name, file_path, line_start, line_end, decorators)
- `File` - Source file (path, name, extension)
- `ExternalPackage` - Third-party package (name)

**Relationship Types**:
- `CONTAINS` - Project → * (project isolation)
- `DEFINES` - Module → Function|Class|Method (module defines entities)
- `CALLS` - Function|Method → Function|Method (function calls)
- `INHERITS` - Class → Class (class inheritance)
- `IMPLEMENTS` - Class → Class (interface implementation)
- `IMPORTS` - Module|Function → Module|ExternalPackage (import dependencies)

### Example Cypher Queries

**Find functions with specific decorator**:
```cypher
MATCH (f:Function)
WHERE 'dataclass' IN f.decorators
RETURN f.qualified_name, f.file_path
LIMIT 50;
```

**Find most-called functions**:
```cypher
MATCH (caller)-[:CALLS]->(callee:Function)
RETURN callee.qualified_name, count(caller) AS call_count
ORDER BY call_count DESC
LIMIT 10;
```

**Find circular dependencies**:
```cypher
MATCH path = (c:Class)-[:INHERITS*]->(c)
RETURN c.qualified_name, length(path) AS cycle_length
ORDER BY cycle_length;
```

**Cross-module function calls**:
```cypher
MATCH (m1:Module)-[:DEFINES]->(f1:Function)-[:CALLS]->(f2:Function)<-[:DEFINES]-(m2:Module)
WHERE m1.qualified_name <> m2.qualified_name
RETURN m1.qualified_name AS from_module, m2.qualified_name AS to_module, count(*) AS call_count
ORDER BY call_count DESC
LIMIT 20;
```

### Using query_cypher Tool

```python
query_cypher(
    query="MATCH (f:Function) WHERE f.name CONTAINS $pattern RETURN f.qualified_name LIMIT 10",
    parameters={"pattern": "login"},
    limit=50
)
```

**Output**:
```json
{
  "query": "MATCH (f:Function) WHERE f.name CONTAINS $pattern RETURN f.qualified_name LIMIT 10",
  "rows": [
    {"f.qualified_name": "auth.services.login"},
    {"f.qualified_name": "auth.api.login_endpoint"}
  ],
  "columns": ["f.qualified_name"],
  "row_count": 2,
  "truncated": false,
  "metadata": {
    "row_count": 2,
    "total_count": 2,
    "truncated": false,
    "execution_time_ms": 18.5
  }
}
```

---

## Performance Tips

### General Guidelines

1. **Use pre-built tools** instead of expert mode when possible (optimized queries)
2. **Start with small depths** (max_depth=1-2) and increase only if needed
3. **Apply filters early** in Cypher queries (use WHERE before expensive operations)
4. **Limit result sets** (pre-built tools auto-limit to 100 rows)

### Depth Recommendations

| Query Type | Recommended max_depth | Rationale |
|------------|----------------------|-----------|
| query_callers | 1-3 | Balance coverage vs. performance |
| query_hierarchy | 5 | Inheritance rarely >5 levels |
| query_call_graph | 3 | Exponential growth beyond 3 |
| query_dependencies (transitive) | 2 | Large result sets beyond 2 |

### When Queries Are Slow

If a query exceeds 100ms:

1. **Reduce max_depth**: Try max_depth=2 instead of max_depth=5
2. **Add more specific filters**: Target specific modules or classes
3. **Use direct queries**: query_callers with max_depth=1 instead of query_call_graph
4. **Check Memgraph health**: `docker stats` to verify resource usage

---

## Troubleshooting

### "Node not found" Errors

**Error**:
```
Function 'nonexistent.func' not found in code graph.
```

**Solutions**:
1. Verify the codebase has been indexed: `docker ps | grep memgraph`
2. Check qualified name format: Use `module.ClassName.method_name`, not `method_name` alone
3. Search by partial name: `query_cypher` with `MATCH (f:Function) WHERE f.name CONTAINS 'func' RETURN f.qualified_name`
4. Re-index the project: `uv run graph-code index /path/to/project`

### Query Timeouts

**Error**:
```
Query exceeded time limit (10 seconds).
```

**Solutions**:
1. Reduce max_depth from current value (e.g., 5 → 3)
2. Use more specific filters (target specific modules)
3. Check database load: `docker stats memgraph`
4. Restart Memgraph: `docker compose restart memgraph`

### Memgraph Connection Issues

**Error**:
```
Cannot connect to Memgraph at localhost:7687.
```

**Solutions**:
1. Check if Memgraph is running: `docker ps | grep memgraph`
2. Start Memgraph: `docker compose up -d`
3. Verify port: `docker port <container-name> 7687`
4. Check logs: `docker logs <container-name>`

### Large Result Sets

**Warning**:
```
Showing first 100 results (347 total). Refine your query to see more specific results.
```

**Solutions**:
1. Add more specific filters (e.g., filter by module: `WHERE f.file_path STARTS WITH 'src/auth'`)
2. Use query_cypher with custom LIMIT: `query_cypher(query="...", limit=200)`
3. Narrow search criteria (use more specific qualified names)

---

## Common Use Cases

### Use Case 1: Impact Analysis Before Refactoring

**Goal**: Understand which code will be affected if I change function `auth.login`

**Steps**:
1. Find all callers:
   ```python
   query_callers(function_name="auth.login", max_depth=2)
   ```
2. Check dependencies:
   ```python
   query_dependencies(target="auth.login", dependency_type="all")
   ```
3. Review results and assess impact

### Use Case 2: Understanding Class Hierarchy

**Goal**: Find all subclasses of `BaseModel` before refactoring

**Steps**:
1. Query hierarchy:
   ```python
   query_hierarchy(class_name="models.BaseModel", direction="down", max_depth=5)
   ```
2. Review all descendants
3. Check for circular dependencies (reported in warnings)

### Use Case 3: Module Extraction

**Goal**: Extract `payment_processor` module into a separate library

**Steps**:
1. Find all dependencies:
   ```python
   query_dependencies(target="payment_processor", dependency_type="all", include_transitive=True)
   ```
2. Find all callers:
   ```python
   query_callers(function_name="payment_processor.*", max_depth=1)
   ```
3. Identify required interfaces from dependencies and callers

### Use Case 4: Finding Dead Code

**Goal**: Identify functions with no callers

**Steps**:
1. Use expert mode:
   ```cypher
   MATCH (f:Function)
   WHERE NOT (f)<-[:CALLS]-()
   RETURN f.qualified_name, f.file_path
   ORDER BY f.qualified_name
   LIMIT 50;
   ```
2. Review results (exclude entry points like `main`, test fixtures)

---

## Next Steps

1. **Index your codebase**: Follow "Installation & Setup" above
2. **Try pre-built tools**: Start with query_callers and query_hierarchy
3. **Explore the graph**: Use Memgraph Lab UI (http://localhost:3000) to visualize
4. **Read the docs**: See `README.md` for detailed documentation
5. **Join the community**: Report issues at https://github.com/yourusername/code-graph-rag/issues

---

## Additional Resources

- **Full Documentation**: `README.md` in repository root
- **Infrastructure Guide**: `docs/INFRASTRUCTURE.md` for deployment details
- **Claude Code Setup**: `docs/claude-code-setup.md` for MCP server configuration
- **Memgraph Documentation**: https://memgraph.com/docs
- **Cypher Query Language**: https://memgraph.com/docs/cypher-manual

---

**Questions or Issues?**
- GitHub Issues: https://github.com/yourusername/code-graph-rag/issues
- MCP Documentation: https://modelcontextprotocol.io
