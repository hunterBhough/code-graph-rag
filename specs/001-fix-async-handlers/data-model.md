# Data Model: Fix Async Handlers for Structural Query Tools

**Feature**: 001-fix-async-handlers
**Date**: 2025-12-09
**Status**: Complete

## Overview

This feature is a bug fix that does not introduce new data models. The existing entities and their relationships remain unchanged.

---

## Existing Entities (Unchanged)

### Handler Function

The inner function returned by `create_*_tool()` functions that executes graph queries.

| Field | Type | Description |
|-------|------|-------------|
| name | `str` | Function name (e.g., `find_callers`) |
| signature | `Callable[..., Awaitable[dict[str, Any]]]` | **Changed**: Now returns awaitable |
| return_type | `dict[str, Any]` | Query result dictionary (unchanged) |

### ToolMetadata

Metadata for an MCP tool including schema and handler information.

| Field | Type | Description |
|-------|------|-------------|
| name | `str` | Tool name (e.g., `query_callers`) |
| description | `str` | Tool description for MCP clients |
| input_schema | `dict[str, Any]` | JSON schema for tool input |
| handler | `Callable[..., Any]` | Handler function reference |
| returns_json | `bool` | Whether handler returns JSON-serializable dict |

### MCPToolsRegistry

Registry for all MCP tools with shared dependencies.

| Field | Type | Description |
|-------|------|-------------|
| project_root | `str` | Path to target repository |
| ingestor | `MemgraphIngestor` | Graph database connection |
| cypher_gen | `CypherGenerator` | Natural language to Cypher translator |
| _tools | `dict[str, ToolMetadata]` | Tool name to metadata mapping |

---

## Structural Query Classes (Unchanged)

### FindCallersQuery
### ClassHierarchyQuery
### DependencyAnalysisQuery
### InterfaceImplementationsQuery
### ExpertModeQuery
### CallGraphGeneratorQuery
### ModuleExportsQuery

All `*Query` classes remain synchronous. Their `execute()` methods do not change.

---

## State Transitions

Not applicable. This fix does not introduce stateful behavior.

---

## Validation Rules

### Handler Function Validation

| Rule | Description |
|------|-------------|
| Must be async | Handler must be defined with `async def` |
| Must return dict | Return type must be `dict[str, Any]` |
| Must be awaitable | When called, must return a coroutine object |

---

## Relationships

```
MCPToolsRegistry
    ├── stores → ToolMetadata[]
    │                 └── references → Handler Function
    └── uses → MemgraphIngestor
                   └── queries → Memgraph Database

MCP Server
    └── calls → MCPToolsRegistry.get_tool_handler()
                       └── returns → (handler, returns_json)
                                          └── awaited by → call_tool()
```

---

## Impact Assessment

| Component | Impact | Notes |
|-----------|--------|-------|
| Handler functions | Modified | Add `async` keyword |
| ToolMetadata | None | Already stores `Callable[..., Any]` |
| MCPToolsRegistry | None | No changes needed |
| Query classes | None | `execute()` stays sync |
| MCP Server | None | Already awaits handlers |
