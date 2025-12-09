# Data Model: Structural Graph Query Engine

**Date**: 2025-12-08
**Feature**: Transform code-graph-rag into Specialized Graph Query Engine
**Branch**: 002-graph-query-engine

## Overview

This document defines the data model for all structural query tools in code-graph-rag. The model consists of three categories: query request entities (tool inputs), query response entities (tool outputs), and graph node entities (existing schema).

---

## 1. Query Request Entities

These entities represent the input parameters for each pre-built structural query tool.

### 1.1 CallersQuery

Find all functions that call a specified target function.

```python
@dataclass
class CallersQuery:
    function_name: str          # Fully qualified name (e.g., 'auth.services.login')
    max_depth: int = 1          # Maximum caller chain depth (1 = direct callers only)
    include_paths: bool = True  # Include file paths and line numbers in results
```

**Validation Rules**:
- `function_name`: Required, non-empty string
- `max_depth`: Integer between 1 and 5 (inclusive)
- `include_paths`: Boolean

**Example**:
```python
CallersQuery(
    function_name="auth.services.UserService.authenticate",
    max_depth=2,
    include_paths=True
)
```

### 1.2 HierarchyQuery

Retrieve class inheritance hierarchy showing ancestors, descendants, or both.

```python
@dataclass
class HierarchyQuery:
    class_name: str                    # Fully qualified class name
    direction: Literal["up", "down", "both"] = "both"  # Traversal direction
    max_depth: int = 10                # Maximum hierarchy depth
```

**Validation Rules**:
- `class_name`: Required, non-empty string
- `direction`: Must be one of "up" (ancestors), "down" (descendants), or "both"
- `max_depth`: Integer between 1 and 10 (inclusive)

**Example**:
```python
HierarchyQuery(
    class_name="auth.models.BaseAuth",
    direction="down",  # Find all child classes
    max_depth=5
)
```

### 1.3 DependenciesQuery

Analyze module or function dependencies including imports and function calls.

```python
@dataclass
class DependenciesQuery:
    target: str  # Qualified name of module or function to analyze
    dependency_type: Literal["imports", "calls", "all"] = "all"  # Type of dependencies
    include_transitive: bool = False  # Include dependencies of dependencies
```

**Validation Rules**:
- `target`: Required, non-empty string
- `dependency_type`: Must be one of "imports", "calls", or "all"
- `include_transitive`: Boolean (use cautiously, can generate large result sets)

**Example**:
```python
DependenciesQuery(
    target="auth.services",
    dependency_type="imports",
    include_transitive=False
)
```

### 1.4 ExportsQuery

Retrieve all public exports (functions, classes) from a specified module.

```python
@dataclass
class ExportsQuery:
    module_name: str            # Fully qualified module name
    include_private: bool = False  # Include private members (starting with _)
```

**Validation Rules**:
- `module_name`: Required, non-empty string
- `include_private`: Boolean

**Example**:
```python
ExportsQuery(
    module_name="auth.services",
    include_private=False
)
```

### 1.5 ImplementationsQuery

Find all classes that implement a specified interface or extend a base class.

```python
@dataclass
class ImplementationsQuery:
    interface_name: str           # Fully qualified interface or base class name
    include_indirect: bool = False  # Include indirect implementations (children of implementers)
```

**Validation Rules**:
- `interface_name`: Required, non-empty string
- `include_indirect`: Boolean (use cautiously with deep inheritance trees)

**Example**:
```python
ImplementationsQuery(
    interface_name="auth.interfaces.PaymentProvider",
    include_indirect=True
)
```

### 1.6 CallGraphQuery

Generate a call graph starting from an entry point function.

```python
@dataclass
class CallGraphQuery:
    entry_point: str      # Fully qualified name of entry point function
    max_depth: int = 3    # Maximum depth to traverse call graph
    max_nodes: int = 50   # Maximum number of nodes to return (truncate if exceeded)
```

**Validation Rules**:
- `entry_point`: Required, non-empty string
- `max_depth`: Integer between 1 and 5 (inclusive)
- `max_nodes`: Integer between 1 and 100 (inclusive)

**Example**:
```python
CallGraphQuery(
    entry_point="app.main",
    max_depth=3,
    max_nodes=50
)
```

### 1.7 CypherQuery

Execute a custom Cypher query (expert mode).

```python
@dataclass
class CypherQuery:
    query: str                  # Cypher query string
    parameters: dict[str, Any] = field(default_factory=dict)  # Query parameters
    limit: int = 50             # Maximum number of rows to return
```

**Validation Rules**:
- `query`: Required, non-empty string
- `parameters`: Dictionary of parameter name → value mappings
- `limit`: Integer between 1 and 1000 (inclusive)

**Example**:
```python
CypherQuery(
    query="MATCH (f:Function) WHERE f.name CONTAINS $pattern RETURN f",
    parameters={"pattern": "login"},
    limit=50
)
```

---

## 2. Query Response Entities

These entities represent the structured output from each pre-built structural query tool.

### 2.1 CallerResult

Result from querying function callers.

```python
@dataclass
class CallerResult:
    callers: list[FunctionNode]       # List of functions that call the target
    call_chains: list[list[str]] | None  # Call chain paths (if max_depth > 1)
    metadata: QueryMetadata           # Execution metadata

@dataclass
class QueryMetadata:
    row_count: int                    # Number of results returned
    total_count: int                  # Total available results (before truncation)
    truncated: bool                   # Whether results were truncated
    execution_time_ms: float          # Query execution time
    max_depth: int | None = None      # For traversal queries
    query_type: str = "structural"    # Tool category
```

**Example**:
```python
CallerResult(
    callers=[
        FunctionNode(
            qualified_name="auth.api.login_endpoint",
            name="login_endpoint",
            file_path="src/auth/api.py",
            line_start=23,
            line_end=45
        )
    ],
    call_chains=[
        ["auth.api.login_endpoint", "auth.services.login"]
    ],
    metadata=QueryMetadata(
        row_count=1,
        total_count=1,
        truncated=False,
        execution_time_ms=12.5,
        max_depth=2
    )
)
```

### 2.2 HierarchyResult

Result from querying class inheritance hierarchy.

```python
@dataclass
class HierarchyResult:
    hierarchy_tree: dict[str, Any]    # Nested tree structure
    ancestors: list[ClassNode]        # Parent classes (if direction="up" or "both")
    descendants: list[ClassNode]      # Child classes (if direction="down" or "both")
    circular_dependencies: list[CircularDependency] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)  # User warnings (e.g., circular inheritance)
    metadata: QueryMetadata

@dataclass
class CircularDependency:
    cycle_type: str                   # "inheritance", "calls", or "imports"
    cycle_path: list[str]             # Qualified names forming the cycle
    cycle_length: int                 # Number of hops in the cycle
```

**Example**:
```python
HierarchyResult(
    hierarchy_tree={
        "name": "auth.models.BaseAuth",
        "children": [
            {"name": "auth.models.AdminAuth", "depth": 1},
            {"name": "auth.models.UserAuth", "depth": 1}
        ]
    },
    ancestors=[],
    descendants=[
        ClassNode(qualified_name="auth.models.AdminAuth", name="AdminAuth"),
        ClassNode(qualified_name="auth.models.UserAuth", name="UserAuth")
    ],
    circular_dependencies=[],
    warnings=[],
    metadata=QueryMetadata(row_count=2, total_count=2, truncated=False, execution_time_ms=18.3)
)
```

### 2.3 DependenciesResult

Result from dependency analysis.

```python
@dataclass
class DependenciesResult:
    imports: list[ModuleNode]         # Imported modules (if type="imports" or "all")
    calls: list[FunctionNode]         # Called functions (if type="calls" or "all")
    dependency_graph: dict[str, list[str]]  # Adjacency list representation
    metadata: QueryMetadata
```

**Example**:
```python
DependenciesResult(
    imports=[
        ModuleNode(qualified_name="os", name="os", path="<stdlib>"),
        ModuleNode(qualified_name="auth.utils", name="utils", path="src/auth/utils.py")
    ],
    calls=[
        FunctionNode(qualified_name="auth.utils.validate_token", name="validate_token")
    ],
    dependency_graph={
        "auth.services": ["os", "auth.utils", "auth.utils.validate_token"]
    },
    metadata=QueryMetadata(row_count=3, total_count=3, truncated=False, execution_time_ms=15.2)
)
```

### 2.4 ExportsResult

Result from module exports query.

```python
@dataclass
class ExportsResult:
    exports: list[FunctionNode | ClassNode]  # Public exports from the module
    module_info: ModuleNode                  # Module metadata
    metadata: QueryMetadata
```

**Example**:
```python
ExportsResult(
    exports=[
        FunctionNode(qualified_name="auth.services.login", name="login"),
        ClassNode(qualified_name="auth.services.UserService", name="UserService")
    ],
    module_info=ModuleNode(
        qualified_name="auth.services",
        name="services",
        path="src/auth/services.py"
    ),
    metadata=QueryMetadata(row_count=2, total_count=2, truncated=False, execution_time_ms=9.8)
)
```

### 2.5 ImplementationsResult

Result from interface implementations query.

```python
@dataclass
class ImplementationsResult:
    implementations: list[ClassNode]  # Classes implementing the interface
    inheritance_depth: dict[str, int]  # Qualified name → depth from interface
    metadata: QueryMetadata
```

**Example**:
```python
ImplementationsResult(
    implementations=[
        ClassNode(qualified_name="auth.providers.StripeProvider", name="StripeProvider"),
        ClassNode(qualified_name="auth.providers.PayPalProvider", name="PayPalProvider")
    ],
    inheritance_depth={
        "auth.providers.StripeProvider": 1,  # Direct implementation
        "auth.providers.PayPalProvider": 1
    },
    metadata=QueryMetadata(row_count=2, total_count=2, truncated=False, execution_time_ms=14.7)
)
```

### 2.6 CallGraphResult

Result from call graph generation.

```python
@dataclass
class CallGraphResult:
    nodes: list[FunctionNode]         # Functions in the call graph
    edges: list[CallEdge]             # Call relationships
    truncated: bool                   # Whether graph was truncated at max_nodes
    total_nodes: int                  # Total nodes before truncation
    metadata: QueryMetadata
```

**Example**:
```python
CallGraphResult(
    nodes=[
        FunctionNode(qualified_name="app.main", name="main"),
        FunctionNode(qualified_name="app.startup", name="startup")
    ],
    edges=[
        CallEdge(from_function="app.main", to_function="app.startup", call_type="direct")
    ],
    truncated=False,
    total_nodes=2,
    metadata=QueryMetadata(row_count=2, total_count=2, truncated=False, execution_time_ms=22.1)
)
```

### 2.7 CypherResult

Result from expert-mode Cypher query.

```python
@dataclass
class CypherResult:
    rows: list[dict[str, Any]]        # Query result rows
    columns: list[str]                # Column names
    row_count: int                    # Number of rows returned
    truncated: bool                   # Whether results were truncated at limit
    metadata: QueryMetadata
```

**Example**:
```python
CypherResult(
    rows=[
        {"function_name": "auth.login", "line_count": 42},
        {"function_name": "auth.logout", "line_count": 15}
    ],
    columns=["function_name", "line_count"],
    row_count=2,
    truncated=False,
    metadata=QueryMetadata(row_count=2, total_count=2, truncated=False, execution_time_ms=18.5)
)
```

---

## 3. Graph Node Entities

These entities represent nodes in the existing Memgraph schema. No changes required.

### 3.1 FunctionNode

Represents a standalone function in the codebase.

```python
@dataclass
class FunctionNode:
    qualified_name: str    # Fully qualified name (e.g., 'auth.services.login')
    name: str              # Short name (e.g., 'login')
    file_path: str         # Relative path to source file
    line_start: int        # Starting line number
    line_end: int          # Ending line number
    decorators: list[str] = field(default_factory=list)  # Function decorators
```

**Graph Label**: `Function`
**Unique Constraint**: `qualified_name`

### 3.2 MethodNode

Represents a class method in the codebase.

```python
@dataclass
class MethodNode:
    qualified_name: str    # Fully qualified name (e.g., 'auth.UserService.authenticate')
    name: str              # Short name (e.g., 'authenticate')
    class_name: str        # Qualified class name (e.g., 'auth.UserService')
    file_path: str         # Relative path to source file
    line_start: int        # Starting line number
    line_end: int          # Ending line number
    decorators: list[str] = field(default_factory=list)  # Method decorators
```

**Graph Label**: `Method`
**Unique Constraint**: `qualified_name`

### 3.3 ClassNode

Represents a class definition in the codebase.

```python
@dataclass
class ClassNode:
    qualified_name: str    # Fully qualified name (e.g., 'auth.models.User')
    name: str              # Short name (e.g., 'User')
    file_path: str         # Relative path to source file
    line_start: int        # Starting line number
    line_end: int          # Ending line number
    base_classes: list[str] = field(default_factory=list)  # Parent class names
```

**Graph Label**: `Class`
**Unique Constraint**: `qualified_name`

### 3.4 ModuleNode

Represents a code module/file in the codebase.

```python
@dataclass
class ModuleNode:
    qualified_name: str    # Fully qualified name (e.g., 'auth.services')
    name: str              # Short name (e.g., 'services')
    path: str              # Relative file path (e.g., 'src/auth/services.py')
    extension: str = ".py" # File extension
```

**Graph Label**: `Module`
**Unique Constraint**: `qualified_name`

### 3.5 PackageNode

Represents a code package (directory containing __init__.py).

```python
@dataclass
class PackageNode:
    qualified_name: str    # Fully qualified name (e.g., 'auth')
    name: str              # Short name (e.g., 'auth')
    path: str              # Relative directory path (e.g., 'src/auth')
```

**Graph Label**: `Package`
**Unique Constraint**: `qualified_name`

### 3.6 CallEdge

Represents a function call relationship.

```python
@dataclass
class CallEdge:
    from_function: str     # Qualified name of caller
    to_function: str       # Qualified name of callee
    call_type: Literal["direct", "method", "constructor"]  # Type of call
```

**Graph Relationship**: `(:Function|Method)-[:CALLS]->(:Function|Method)`

**Call Types**:
- `direct`: Direct function call (e.g., `login()`)
- `method`: Method call on an object (e.g., `user.authenticate()`)
- `constructor`: Class instantiation (e.g., `UserService()`)

---

## 4. Relationship Types

These relationships already exist in the graph schema and require no changes.

### 4.1 CALLS
- **Direction**: Caller → Callee
- **Nodes**: `Function|Method` → `Function|Method`
- **Meaning**: Function/method invokes another function/method

### 4.2 INHERITS
- **Direction**: Child → Parent
- **Nodes**: `Class` → `Class`
- **Meaning**: Class inherits from another class

### 4.3 IMPLEMENTS
- **Direction**: Implementation → Interface
- **Nodes**: `Class` → `Class`
- **Meaning**: Class implements an interface (language-dependent)

### 4.4 IMPORTS
- **Direction**: Importer → Imported
- **Nodes**: `Module|Function` → `Module|ExternalPackage`
- **Meaning**: Module or function imports another module

### 4.5 DEFINES
- **Direction**: Container → Contained
- **Nodes**: `Module` → `Function|Class|Method`
- **Meaning**: Module defines a function, class, or method

### 4.6 CONTAINS
- **Direction**: Project → Node
- **Nodes**: `Project` → `*` (any node type)
- **Meaning**: Project-based isolation relationship (all nodes belong to a project)

---

## 5. Validation Rules Summary

| Entity | Field | Validation Rule |
|--------|-------|----------------|
| CallersQuery | function_name | Required, non-empty string |
| CallersQuery | max_depth | Integer, 1 ≤ value ≤ 5 |
| HierarchyQuery | class_name | Required, non-empty string |
| HierarchyQuery | direction | Enum: "up", "down", "both" |
| HierarchyQuery | max_depth | Integer, 1 ≤ value ≤ 10 |
| DependenciesQuery | target | Required, non-empty string |
| DependenciesQuery | dependency_type | Enum: "imports", "calls", "all" |
| CallGraphQuery | entry_point | Required, non-empty string |
| CallGraphQuery | max_depth | Integer, 1 ≤ value ≤ 5 |
| CallGraphQuery | max_nodes | Integer, 1 ≤ value ≤ 100 |
| CypherQuery | query | Required, non-empty string |
| CypherQuery | limit | Integer, 1 ≤ value ≤ 1000 |

---

## 6. Data Flow Diagram

```
User → MCP Tool → Query Request Entity → Query Handler
                                              ↓
                                         Cypher Query
                                              ↓
                                          Memgraph
                                              ↓
                                    Graph Node Entities
                                              ↓
                               Query Response Entity → MCP Tool → User
```

**Example Flow (query_callers)**:
1. User calls `query_callers(function_name="auth.login", max_depth=2)`
2. MCP tool creates `CallersQuery(function_name="auth.login", max_depth=2)`
3. Query handler generates Cypher: `MATCH (caller)-[:CALLS*1..2]->(target {qualified_name: "auth.login"}) RETURN caller`
4. Memgraph executes query, returns `FunctionNode` entities
5. Query handler creates `CallerResult` with nodes and metadata
6. MCP tool formats result as JSON and returns to user

---

## 7. Implementation Notes

### 7.1 Response Formatting

All query tools should return responses in this structure:

```python
{
    "query": "Human-readable query description",
    "results": [...],  # Tool-specific results (callers, hierarchy, etc.)
    "metadata": {
        "row_count": 10,
        "total_count": 15,
        "truncated": True,
        "execution_time_ms": 42.3,
        "max_depth": 3
    }
}
```

### 7.2 Error Handling

When a query fails (node not found, timeout, etc.), return an error object:

```python
{
    "error": "Function 'nonexistent.func' not found in graph",
    "error_code": "NODE_NOT_FOUND",
    "suggestion": "Check the qualified name format (e.g., 'module.Class.method')",
    "provided_input": {
        "function_name": "nonexistent.func"
    }
}
```

### 7.3 Truncation Behavior

- **Pre-built queries**: Truncate at 100 rows
- **Expert mode (query_cypher)**: Truncate at 50 rows (configurable via `limit` parameter)
- **Call graphs**: Truncate at `max_nodes` parameter (default: 50)

When truncated, set `metadata.truncated = True` and include `metadata.total_count` to show how many results were omitted.

---

## 8. Future Extensions

This data model is designed to be extensible. Potential future additions:

1. **Complexity Metrics**: Add `cyclomatic_complexity`, `line_count` to FunctionNode
2. **Type Information**: Add `return_type`, `parameter_types` to FunctionNode/MethodNode
3. **Documentation**: Add `docstring`, `comments` to all node types
4. **Symbol References**: Track variable/constant usage across files
5. **Test Coverage**: Link functions to their test cases

These extensions would require graph schema changes and are out of scope for this feature.
