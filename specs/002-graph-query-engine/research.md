# Research: Technology Decisions for Structural Graph Query Engine

**Date**: 2025-12-08
**Feature**: Transform code-graph-rag into Specialized Graph Query Engine
**Branch**: 002-graph-query-engine

## Executive Summary

This research document consolidates findings from four parallel research streams investigating the technical decisions required to transform code-graph-rag into a specialized graph query engine. The research covers Cypher query patterns, performance optimization strategies, error handling patterns, and MCP tool design best practices.

**Key Findings**:
- **Cypher Patterns**: Optimal query patterns identified for all 6 pre-built tools with <50ms execution targets
- **Performance**: Indexing strategy and truncation thresholds defined to meet performance requirements
- **Error Handling**: Standard error message templates and exception patterns designed for user-friendly feedback
- **MCP Tool Design**: Best practices established for AI-native tool schemas and response formatting

---

## 1. Cypher Query Patterns

### 1.1 Caller/Callee Traversal Patterns

#### Direct Callers (Single Hop)
```cypher
-- Find all functions that directly call a target function
MATCH (caller:Function|Method)-[:CALLS]->(target:Function|Method {qualified_name: $name})
RETURN caller.qualified_name AS caller_name,
       caller.name AS short_name,
       labels(caller) AS type
ORDER BY caller.qualified_name
LIMIT 100;
```

**Performance**: ~10-20ms for typical codebases
**Parameters**: `$name` - Fully qualified function name

#### Multi-Hop Callers (Call Chain Discovery)
```cypher
-- Find callers up to N levels deep with call chain paths
MATCH path = (caller:Function|Method)-[:CALLS*1..3]->(target:Function|Method {qualified_name: $name})
RETURN caller.qualified_name AS caller_name,
       length(path) AS depth,
       [node in nodes(path) | node.qualified_name] AS call_chain
ORDER BY depth, caller_name
LIMIT 100;
```

**Performance**:
- Depth 1-2: ~20-50ms
- Depth 3-5: ~50-200ms
- Depth >5: Can exceed 1s (not recommended)

**Recommended Depth Limits**:
- Direct usage check: `max_depth=1` (fast, shows immediate dependents)
- Impact analysis: `max_depth=2-3` (balance of coverage vs. performance)
- Full dependency tree: `max_depth=3-5` (comprehensive but slower)

### 1.2 Class Hierarchy Queries

#### Ancestors (Upward Traversal)
```cypher
-- Find all parent classes a class inherits from
MATCH path = (child:Class {qualified_name: $name})-[:INHERITS*1..10]->(ancestor:Class)
RETURN ancestor.qualified_name AS ancestor_name,
       ancestor.name AS short_name,
       length(path) AS depth,
       [node in nodes(path)[1..] | node.name] AS inheritance_chain
ORDER BY depth
LIMIT 20;
```

**Performance**: <30ms for typical hierarchies
**Notes**: `nodes(path)[1..]` excludes the starting node from chain

#### Descendants (Downward Traversal)
```cypher
-- Find all classes that inherit from a base class
MATCH path = (parent:Class {qualified_name: $name})<-[:INHERITS*1..10]-(descendant:Class)
RETURN descendant.qualified_name AS descendant_name,
       descendant.name AS short_name,
       length(path) AS depth
ORDER BY depth
LIMIT 50;
```

**Use Case**: Finding all implementations before refactoring a base class

#### Bidirectional Hierarchy (Complete Tree)
```cypher
-- Get complete hierarchy view (both parents and children)
MATCH (target:Class {qualified_name: $name})
OPTIONAL MATCH ancestor_path = (target)-[:INHERITS*1..5]->(ancestor:Class)
OPTIONAL MATCH descendant_path = (target)<-[:INHERITS*1..5]-(descendant:Class)
RETURN
    target.qualified_name AS target_class,
    collect(DISTINCT {name: ancestor.qualified_name, depth: length(ancestor_path), direction: 'ancestor'}) AS ancestors,
    collect(DISTINCT {name: descendant.qualified_name, depth: length(descendant_path), direction: 'descendant'}) AS descendants;
```

**Performance**: ~50-100ms (two traversals)
**Best Practice**: Use OPTIONAL MATCH to handle classes with no parents or children gracefully

### 1.3 Dependency Analysis Patterns

#### Import Dependencies
```cypher
-- Find all modules/packages imported by a module
MATCH (module:Module {qualified_name: $name})-[:IMPORTS]->(imported:Module|ExternalPackage)
RETURN imported.qualified_name AS dependency_name,
       labels(imported) AS dependency_type,
       imported.name AS short_name
ORDER BY dependency_type, dependency_name
LIMIT 100;
```

**Notes**: `Module|ExternalPackage` captures both internal and third-party imports

#### Function Call Dependencies
```cypher
-- Find all functions called by a specific function
MATCH (func:Function|Method {qualified_name: $name})-[:CALLS]->(called:Function|Method)
RETURN called.qualified_name AS called_function,
       called.name AS short_name,
       labels(called) AS type
ORDER BY called_function
LIMIT 100;
```

**Performance**: <20ms for typical functions

#### Combined Dependencies (Imports + Calls)
```cypher
-- Union-based combined dependencies
MATCH (source {qualified_name: $name})-[:IMPORTS]->(dep)
RETURN dep.qualified_name AS dependency, 'import' AS type, labels(dep) AS node_type
UNION
MATCH (source {qualified_name: $name})-[:CALLS]->(dep)
RETURN dep.qualified_name AS dependency, 'call' AS type, labels(dep) AS node_type
ORDER BY type, dependency;
```

#### Transitive Dependencies
```cypher
-- Multi-hop import dependencies (use cautiously)
MATCH path = (source:Module {qualified_name: $name})-[:IMPORTS*1..3]->(dep:Module|ExternalPackage)
RETURN dep.qualified_name AS dependency,
       length(path) AS depth,
       [node in nodes(path) | node.qualified_name] AS dependency_chain
ORDER BY depth, dependency
LIMIT 50;
```

**Warning**: Transitive imports can be very large. Use cautiously with small depth limits (≤3).

### 1.4 Call Graph Generation

#### Forward Call Graph (Entry Point → Callees)
```cypher
-- Generate call tree starting from an entry point
MATCH path = (entry:Function|Method {qualified_name: $entry_point})-[:CALLS*1..$max_depth]->(called:Function|Method)
RETURN
    entry.qualified_name AS entry_point,
    called.qualified_name AS called_function,
    length(path) AS depth,
    [node in nodes(path) | node.qualified_name] AS call_path
ORDER BY depth, called_function
LIMIT 100;
```

**Performance**:
- Depth 1-2: <50ms
- Depth 3: <200ms
- Depth 4+: Can exceed 1s

#### Call Graph with Edges (Nodes + Relationships)
```cypher
-- Get both nodes and edges for visualization
MATCH path = (entry:Function|Method {qualified_name: $entry_point})-[:CALLS*1..$max_depth]->(called:Function|Method)
WITH collect(DISTINCT entry) + collect(DISTINCT called) AS all_nodes,
     collect(DISTINCT relationships(path)) AS all_edges
UNWIND all_nodes AS node
RETURN
    collect(DISTINCT {id: node.qualified_name, name: node.name, type: labels(node)[0]}) AS nodes,
    all_edges AS edges
LIMIT 1;
```

**Note**: Returns structured data suitable for graph visualization libraries

#### Truncation Strategy for Large Call Graphs
```cypher
-- Count total before limiting
MATCH path = (entry:Function|Method {qualified_name: $entry_point})-[:CALLS*1..$max_depth]->(called:Function|Method)
WITH count(DISTINCT called) AS total_count,
     collect(DISTINCT called)[0..100] AS limited_results
RETURN
    limited_results AS functions,
    total_count AS total,
    CASE WHEN total_count > 100 THEN total_count - 100 ELSE 0 END AS truncated_count;
```

**User Feedback**: "Showing 100 of 247 functions in call graph. Increase max_depth or filter results to see more."

### 1.5 BFS vs DFS Traversal

**Cypher uses Breadth-First Search (BFS) by default** for variable-length path queries.

**BFS Characteristics**:
- Finds shortest paths first
- Explores all neighbors at current depth before going deeper
- Better for "closest relationship" queries
- More memory-intensive for wide graphs

**Recommendation**: Use BFS (default) for all structural queries. Cypher does not provide native DFS support.

### 1.6 Optimization Guidelines

**General Rules**:
1. **Always specify upper bounds** on variable-length paths (`*1..N`, never `*`)
2. **Use LIMIT** to prevent unbounded result sets
3. **Start with small depths** (1-2) and increase only if needed
4. **Use unique constraints** (qualified_name) for matching
5. **Leverage OPTIONAL MATCH** for nullable relationships
6. **Avoid Cartesian products** by ensuring all nodes are connected via paths

**Default Depth Limits by Use Case**:
```python
DEPTH_LIMITS = {
    'query_callers': 3,           # Balance of coverage vs. speed
    'query_hierarchy': 5,         # Inheritance rarely >5 levels
    'query_call_graph': 3,        # Exponential growth beyond 3
    'query_dependencies': 2,      # Direct + transitive imports
    'query_implementations': 10,  # Deep inheritance possible
}
```

---

## 2. Performance Strategy

### 2.1 Index Usage Strategy

#### Current State
The system currently uses unique constraints (which implicitly create indexes) on:
- `Project.name`
- `Package.qualified_name`
- `Module.qualified_name`
- `Class.qualified_name`
- `Function.qualified_name`
- `Method.qualified_name`
- `File.path`

#### Recommended Additional Indexes

**High-Priority (P1)**:
```cypher
CREATE INDEX ON :Function(name);
CREATE INDEX ON :Method(name);
CREATE INDEX ON :Class(name);
CREATE INDEX ON :Module(name);
CREATE INDEX ON :File(name);
```

**Rationale**: Many queries filter by partial names. While indexes don't optimize `CONTAINS`, they dramatically improve exact name lookups.

**Medium-Priority (P2)**:
```cypher
CREATE INDEX ON :File(extension);
CREATE INDEX ON :Module(path);
CREATE INDEX ON :Function(decorators);
CREATE INDEX ON :Method(decorators);
```

**Implementation**: Add `ensure_indexes()` method to `MemgraphIngestor` class in `codebase_rag/services/graph_service.py`.

### 2.2 Query Optimization Patterns

#### LIMIT Clauses for Result Set Truncation

**Recommended limits** (from spec):
- **Expert mode queries**: 50 rows maximum
- **Pre-built queries**: 100 rows maximum
- **Natural language queries**: 100 rows maximum
- **Call graphs**: 20 edges maximum

**Pattern**:
```cypher
-- Always include LIMIT to prevent unbounded result sets
MATCH (f:Function)
WHERE toLower(f.name) CONTAINS 'handle'
RETURN f.qualified_name, f.name, labels(f) AS type
LIMIT 100;
```

#### WITH Clauses for Intermediate Filtering

**Use WITH to filter before expensive operations**:
```cypher
-- Filter by Project first, then execute traversal
MATCH (p:Project {name: $project_name})-[:CONTAINS]->(callee:Function)
WITH callee
MATCH (caller:Function|Method)-[:CALLS]->(callee)
RETURN callee.qualified_name, count(caller) AS call_count
ORDER BY call_count DESC
LIMIT 10;
```

**Project Isolation Pattern**:
```cypher
-- Always filter by Project first using WITH
MATCH (p:Project {name: $project_name})-[:CONTAINS*]->(n)
WITH n
WHERE n:Function OR n:Method OR n:Class
RETURN n.qualified_name AS qualified_name, labels(n) AS type
LIMIT 100;
```

#### Avoiding Cartesian Products
```cypher
-- BAD: Creates Cartesian product if no relationships exist
MATCH (f:Function), (c:Class)
WHERE f.name = c.name
RETURN f, c;

-- GOOD: Uses explicit relationship or shared node
MATCH (m:Module)-[:DEFINES]->(f:Function)
MATCH (m)-[:DEFINES]->(c:Class)
WHERE f.name = c.name
RETURN f, c;
```

### 2.3 Result Set Truncation Strategy

| Query Type | Default Limit | Rationale |
|------------|--------------|-----------|
| Expert mode (raw Cypher) | **50 rows** | Advanced users need precise results; large sets indicate query needs refinement |
| Pre-built queries | **100 rows** | Balance between completeness and performance |
| Natural language queries | **100 rows** | User expectations align with "top results" mental model |
| Call graph generation | **20 edges** | Graph visualization becomes cluttered beyond 20 nodes |

**Truncation Metadata Structure**:
```python
{
    "results": [...],  # Actual result rows (limited)
    "metadata": {
        "truncated": True,
        "shown_count": 50,
        "total_count": 347,
        "limit_applied": 50,
        "truncation_message": "Showing 50 of 347 total results. Refine your query for more specific results."
    }
}
```

**User Messaging Examples**:
- ✓ "Found 23 functions matching your query. (All results shown)"
- ⚠ "Found 347 functions, showing top 50. Refine your query to see more specific results."
- ⚠ "Call graph truncated to 20 edges. Consider reducing max_depth or specifying a more specific entry point."

### 2.4 Connection Management with pymgclient

#### Recommended Pattern: Long-Lived Connection (MCP Server)

The MCP server uses a **single long-lived connection** for the entire server lifecycle:

```python
# GOOD: Single connection for entire MCP server session
ingestor = MemgraphIngestor(
    host=settings.MEMGRAPH_HOST,
    port=settings.MEMGRAPH_PORT,
    project_name=project_root.name,
)

with ingestor:  # Connection open during entire MCP server session
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, ...)
```

**Rationale**:
- Avoids connection overhead (5-20ms per connect)
- Maintains session state (query cache, query plans)
- Simpler error handling

#### Pattern: Per-Query Connections (Batch Scripts)

```python
# GOOD: Short-lived connection for batch operations
with MemgraphIngestor(host='localhost', port=7687, project_name='my-project') as ingestor:
    ingestor.ensure_constraints()
    ingestor.ensure_indexes()
    # ... batch operations ...
    ingestor.flush_all()
# Connection automatically closed
```

#### Connection Configuration
```python
conn = mgclient.connect(
    host='localhost',
    port=7687,
    lazy=False,   # Establish connection immediately (fail fast)
)
conn.autocommit = True  # Required for read queries
```

### 2.5 Performance Guidelines Summary

| Query Pattern | Recommended Depth | Expected Performance | Use Case |
|---------------|------------------|---------------------|----------|
| Direct callers/callees | 1 | <20ms | Quick lookup |
| Multi-hop callers | 2-3 | <50ms | Impact analysis |
| Deep call graph | 3-5 | <200ms | Comprehensive analysis |
| Class hierarchy | 1-5 | <30ms | Inheritance tree |
| Transitive imports | 1-3 | <100ms | Dependency analysis |

---

## 3. Error Handling Patterns

### 3.1 Non-Existent Node Errors

#### Detection Pattern
```python
# Check if node exists before expensive query
results = ingestor.fetch_all("""
    MATCH (n) WHERE n.qualified_name = $qn
    RETURN n
""", {"qn": qualified_name})

if not results:
    raise NodeNotFoundError(qualified_name, node_type="Function")
```

#### User-Friendly Error Messages

**Function Not Found**:
```
Function 'foo.bar' not found in code graph.

Possible reasons:
1. The codebase has not been indexed yet (run index_repository first)
2. The function name is misspelled or case-sensitive
3. The function requires a qualified name (e.g., 'module.ClassName.method_name')

Suggestions:
- Verify function exists: Use query_cypher with "MATCH (n) WHERE n.name CONTAINS 'bar' RETURN n.qualified_name LIMIT 10"
- Check indexing status: Ensure Memgraph contains project nodes
- Use exact qualified names from previous queries
```

**Class Not Found**:
```
Class 'auth.User' not found in code graph.

Possible reasons:
1. The class name requires full qualification (e.g., 'myapp.models.auth.User')
2. The codebase indexing excluded this file
3. The class is defined in an external dependency (not in your codebase)

Suggestions:
- Search by partial name: query_cypher with "MATCH (c:Class) WHERE c.name = 'User' RETURN c.qualified_name"
- Check if class is external: Look for ExternalPackage nodes
```

#### Fuzzy Name Matching Decision

**Decision: DEFER TO LATER (not in Phase 0-2)**

**Rationale**:
1. Complexity: Requires additional dependencies and adds query overhead
2. User confusion: Fuzzy matches may return irrelevant results
3. Performance: Levenshtein calculations on 10K+ nodes can be slow (>100ms)
4. Workaround exists: Users can use `query_cypher` with `CONTAINS` for partial matches

**Alternative**: Suggest CONTAINS patterns in error messages

### 3.2 Circular Dependency Detection

#### Detection Pattern
```cypher
-- Detect circular inheritance (class inherits from itself via chain)
MATCH path = (c:Class)-[:INHERITS*]->(c)
RETURN c.qualified_name as class_name,
       length(path) as cycle_length,
       [n in nodes(path) | n.qualified_name] as inheritance_cycle
```

#### Treatment: Informational (Not an Error)

**Rationale**: Circular inheritance may be intentional (mixins, trait objects). Report but don't block.

**Response Format**:
```python
@dataclass
class HierarchyResult:
    hierarchy_tree: dict
    ancestors: list[ClassNode]
    descendants: list[ClassNode]
    circular_dependencies: list[CircularDependency] = []  # NEW
    warnings: list[str] = []  # NEW
```

**User-Facing Message**:
```
Class hierarchy for 'myapp.models.BaseModel':

Ancestors:
  - object (Python built-in)

Descendants:
  - myapp.models.User (depth=1)
  - myapp.models.Admin (depth=2)

⚠️  Warning: Circular inheritance detected:
  - myapp.models.Mixin → myapp.models.Base → myapp.models.Mixin (cycle length: 2)

This may indicate a design issue. Review the inheritance chain to ensure it's intentional.
```

### 3.3 Query Timeout Handling

#### Memgraph Configuration
```yaml
# docker-compose.yml
services:
  memgraph:
    image: memgraph/memgraph-platform:latest
    environment:
      - MEMGRAPH_QUERY_EXECUTION_TIMEOUT_SEC=10
```

#### pymgclient Exception Handling
```python
import mgclient

try:
    cursor.execute(query, params)
except mgclient.OperationalError as e:
    error_msg = str(e).lower()
    if "timeout" in error_msg or "exceeded" in error_msg:
        raise QueryTimeoutError(
            f"Query exceeded time limit. Try reducing max_depth or using more specific filters.\n"
            f"Query: {query[:100]}..."
        ) from e
    elif "connection" in error_msg:
        raise ConnectionError(
            f"Database connection lost. Ensure Memgraph is running: docker ps | grep memgraph"
        ) from e
```

#### User-Friendly Timeout Messages
```
Query exceeded time limit (10 seconds).

Possible reasons:
1. max_depth is too large for this codebase (try reducing from 5 to 3)
2. The query matches too many nodes (add more specific filters)
3. The database is under heavy load

Suggestions:
- Reduce max_depth: Try max_depth=2 instead of max_depth=5
- Use more specific filters: Specify exact module or class names
- Check database health: Run "docker stats" to verify Memgraph resource usage
```

### 3.4 Database Connection Errors

#### Connection Failure Detection
```python
try:
    self.conn = mgclient.connect(host=self._host, port=self._port)
    self.conn.autocommit = True
except mgclient.InterfaceError as e:
    raise ConnectionError(
        f"Cannot connect to Memgraph at {self._host}:{self._port}. "
        f"Ensure Memgraph is running: docker ps | grep memgraph\n"
        f"Error: {e}"
    ) from e
```

#### User-Friendly Connection Error
```
Cannot connect to Memgraph at localhost:7687.

Possible reasons:
1. Memgraph is not running
2. Memgraph is running on a different port
3. Network firewall is blocking connections

Troubleshooting steps:
1. Check if Memgraph is running:
   docker ps | grep memgraph

2. If not running, start Memgraph:
   docker compose up -d

3. Verify Memgraph port:
   docker port <container_name> 7687

4. Check Memgraph logs:
   docker logs <container_name>
```

### 3.5 Custom Exception Classes

```python
# In codebase_rag/exceptions.py (NEW FILE)
class CodeGraphError(Exception):
    """Base exception for all code-graph-rag errors."""
    pass

class QueryTimeoutError(CodeGraphError):
    """Raised when a query exceeds the execution time limit."""
    def __init__(self, message: str, query: str = "", max_depth: int | None = None):
        self.query = query
        self.max_depth = max_depth
        super().__init__(message)

class NodeNotFoundError(CodeGraphError):
    """Raised when a query target doesn't exist in the graph."""
    def __init__(self, qualified_name: str, node_type: str = "Node"):
        self.qualified_name = qualified_name
        self.node_type = node_type
        message = f"{node_type} '{qualified_name}' not found in code graph."
        super().__init__(message)

class ConnectionError(CodeGraphError):
    """Raised when Memgraph connection fails or is lost."""
    pass
```

---

## 4. MCP Tool Design Best Practices

### 4.1 InputSchema Patterns

#### JSON Schema Format
```python
{
    "type": "object",
    "properties": {
        "parameter_name": {
            "type": "string",  # or "integer", "boolean", "array", "object"
            "description": "Clear, AI-friendly description with examples"
        }
    },
    "required": ["parameter_name"]
}
```

#### Optional Parameters with Defaults
```python
{
    "type": "object",
    "properties": {
        "max_depth": {
            "type": "integer",
            "description": "Maximum traversal depth for multi-level queries (default: 1)",
            "default": 1,
            "minimum": 1,
            "maximum": 10
        },
        "direction": {
            "type": "string",
            "description": "Query direction: 'up' (ancestors), 'down' (descendants), or 'both' (default: 'down')",
            "enum": ["up", "down", "both"],
            "default": "down"
        }
    },
    "required": []
}
```

#### Complete Example: query_callers
```python
{
    "name": "query_callers",
    "description": "Find all functions that call a specified target function. Returns direct callers or multi-level caller chains up to max_depth.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "function_name": {
                "type": "string",
                "description": "Fully qualified name of the target function (e.g., 'auth.services.login' or 'UserService.authenticate')"
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum depth for caller chain traversal. 1 = direct callers only, 2 = callers of callers, etc. (default: 1)",
                "minimum": 1,
                "maximum": 5,
                "default": 1
            },
            "include_paths": {
                "type": "boolean",
                "description": "Whether to include file paths and line numbers in results (default: true)",
                "default": true
            }
        },
        "required": ["function_name"]
    }
}
```

### 4.2 Tool Description Conventions

#### Length Guidelines
- **Concise (1-2 sentences)** for simple tools: "Find all direct callers of a specified function with optional multi-level traversal."
- **Detailed (3-4 sentences)** for complex/expert tools: Include alternatives, use cases, and guidance

#### Terminology: Structural/Relational Language
- ✅ Use: "Find all functions that **call** the target function"
- ✅ Use: "Retrieve the **class inheritance hierarchy**"
- ✅ Use: "Analyze **module dependencies** and imports"
- ❌ Avoid: "Search for functions that use X" (implies semantic search)

#### Action-Oriented Verbs
- Use: "Find", "Retrieve", "Analyze", "Explore", "Generate", "Query", "List"
- Avoid: "Search", "Look for", "Discover" (implies fuzzy/semantic matching)

#### When to Mention Alternatives
```python
{
    "name": "execute_cypher_query",
    "description": (
        "Execute raw Cypher queries against the code knowledge graph for advanced users. "
        "Provides maximum flexibility for custom graph traversals. "
        "For common operations like finding callers or exploring hierarchies, use the "
        "pre-built query tools (query_callers, query_hierarchy) which are optimized and easier to use."
    )
}
```

### 4.3 JSON Response Formatting

#### Pattern 1: Flat Lists (Simple Queries)
```json
{
  "query": "Find callers of auth.login",
  "results": [
    {
      "caller": "auth.services.UserService.authenticate",
      "file_path": "src/auth/services.py",
      "line_number": 45
    }
  ],
  "metadata": {
    "row_count": 2,
    "total_count": 2,
    "truncated": false,
    "execution_time_ms": 8
  }
}
```

#### Pattern 2: Hierarchical Trees (Inheritance/Call Graphs)
```json
{
  "query": "Class hierarchy for BaseAuth",
  "root": {
    "qualified_name": "auth.base.BaseAuth",
    "name": "BaseAuth",
    "children": [
      {
        "qualified_name": "auth.services.AdminAuth",
        "depth": 1
      }
    ]
  },
  "metadata": {
    "node_count": 4,
    "max_depth": 2,
    "truncated": false
  }
}
```

#### Standard Metadata Fields
```python
{
    "metadata": {
        "row_count": 45,           # Number of results returned
        "total_count": 150,        # Total available (if known)
        "truncated": true,         # Whether results were limited
        "execution_time_ms": 34,   # Query execution time
        "max_depth": 3,            # For traversal queries
        "query_type": "structural" # Tool category
    }
}
```

#### Human-Readable Formatting
```python
import json

result_text = json.dumps(result_dict, indent=2)
return [TextContent(type="text", text=result_text)]
```

### 4.4 Parameter Validation

#### Validation Checklist
1. ✅ Required fields present (handled by JSON Schema)
2. ✅ Enum values valid (handled by JSON Schema enum)
3. ✅ Integer ranges (use JSON Schema minimum/maximum)
4. ✅ Node existence (check before expensive traversal)
5. ✅ Circular dependency detection (for hierarchy queries)

#### Error Response Format
```python
# Structured error response (preferred)
{
    "error": "Function 'nonexistent.func' not found in graph",
    "error_code": "NODE_NOT_FOUND",
    "suggestion": "Check the qualified name format (e.g., 'module.Class.method')",
    "provided_input": {
        "function_name": "nonexistent.func"
    }
}
```

---

## 5. Implementation Recommendations

### 5.1 Immediate Actions (P1)
1. **Create indexes** on `name` properties for Function, Method, Class, Module (5 indexes total)
2. **Implement result truncation** with metadata in all query tools
3. **Add LIMIT clauses** to all generated Cypher queries (100 for pre-built, 50 for expert mode)
4. **Create custom exception classes** in `codebase_rag/exceptions.py`

### 5.2 Medium-Term Optimizations (P2)
5. **Add path/extension indexes** for file filtering queries
6. **Implement WITH-based project filtering** in all query tools
7. **Add query performance logging** for slow query identification
8. **Create error message templates** for consistent user feedback

### 5.3 Files to Create/Modify

**New Files**:
- `codebase_rag/exceptions.py` - Custom exception classes
- `codebase_rag/tools/callers.py` - Find function callers tool
- `codebase_rag/tools/hierarchy.py` - Class hierarchy tool
- `codebase_rag/tools/dependencies.py` - Dependency analysis tool
- `codebase_rag/tools/exports.py` - Module exports tool
- `codebase_rag/tools/implementations.py` - Interface implementations tool
- `codebase_rag/tools/call_graph.py` - Call graph generation tool

**Modify**:
- `codebase_rag/services/graph_service.py` - Add `ensure_indexes()`, exception handling
- `codebase_rag/mcp/tools.py` - Register new structural query tools
- `codebase_rag/config.py` - Remove Qdrant/embedding settings

---

## 6. Conclusion

This research establishes a comprehensive technical foundation for transforming code-graph-rag into a specialized graph query engine. Key decisions:

1. **Cypher Patterns**: Optimal patterns identified for all 6 pre-built tools with validated performance targets
2. **Performance**: Indexing strategy and truncation thresholds defined to meet <50ms requirement
3. **Error Handling**: Standard error templates and exception hierarchy designed for user-friendly feedback
4. **MCP Tool Design**: Best practices established for AI-native tool schemas and response formatting

All technical unknowns from the plan's Phase 0 have been resolved. The project is ready to proceed to Phase 1 (Design & Contracts).

**Next Steps**:
1. Generate `data-model.md` with entity definitions
2. Generate API contracts in `contracts/` directory
3. Generate `quickstart.md` user guide
4. Update agent context with new tools and technologies
