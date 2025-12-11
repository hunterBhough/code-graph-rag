# Code-Graph-RAG HTTP API Reference

**Version**: 0.0.24
**Base URL**: `http://localhost:8001`
**OpenAPI Specification**: [contracts/openapi.yaml](../specs/004-mcp-http-standard/contracts/openapi.yaml)

## Overview

The Code-Graph-RAG HTTP API provides REST access to all MCP (Model Context Protocol) tools for analyzing code structure and relationships. All responses follow a standardized envelope format with consistent error codes and request tracking.

## Quick Start

```bash
# Start HTTP server
uv run python -m codebase_rag.http

# Discover available tools
curl http://localhost:8001/tools | jq

# Execute a tool
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d '{"tool": "query_callers", "arguments": {"function_name": "my.function"}}' | jq

# Check service health
curl http://localhost:8001/health | jq
```

## Endpoints

### POST /call-tool

Execute any available MCP tool with provided arguments.

**Request Format**:
```json
{
  "tool": "query_callers",
  "arguments": {
    "function_name": "codebase_rag.services.graph_service.MemgraphIngestor.ensure_node_batch",
    "max_depth": 3
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Request Fields**:
- `tool` (string, required): Name of MCP tool to execute (snake_case pattern)
- `arguments` (object, required): Tool-specific arguments matching tool's JSON Schema
- `request_id` (string, optional): Client-provided UUID for request tracking

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "callers": [
      {"name": "function_a", "module": "module1"},
      {"name": "function_b", "module": "module2"}
    ]
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-12-09T12:34:56.789Z",
  "meta": {
    "execution_time_ms": 150
  }
}
```

**Error Response** (400/404/408/429/500):
```json
{
  "success": false,
  "error": "Tool not found: invalid_tool",
  "code": "TOOL_NOT_FOUND",
  "request_id": "550e8400-e29b-41d4-a716-446655440001",
  "timestamp": "2025-12-09T12:34:57.123Z"
}
```

**Error Codes**:
- `TOOL_NOT_FOUND` (404): Requested tool does not exist
- `INVALID_ARGUMENTS` (400): Tool arguments failed validation
- `EXECUTION_ERROR` (500): Tool executed but encountered runtime error
- `INTERNAL_ERROR` (500): Unhandled exception in HTTP server
- `TIMEOUT` (408): Tool execution exceeded configured timeout
- `RATE_LIMITED` (429): Client exceeded rate limit

### GET /tools

List all available MCP tools with their input schemas.

**Request**:
```bash
curl http://localhost:8001/tools
```

**Response** (200 OK):
```json
{
  "service": "code-graph-rag",
  "version": "0.0.24",
  "tools": [
    {
      "name": "query_callers",
      "description": "Find all functions that call the specified function",
      "input_schema": {
        "type": "object",
        "properties": {
          "function_name": {
            "type": "string",
            "description": "Qualified name of the function to analyze"
          },
          "max_depth": {
            "type": "integer",
            "minimum": 1,
            "maximum": 10,
            "description": "Maximum depth of call chain to traverse"
          }
        },
        "required": ["function_name"]
      }
    },
    {
      "name": "query_hierarchy",
      "description": "Query class inheritance hierarchy",
      "input_schema": {
        "type": "object",
        "properties": {
          "class_name": {
            "type": "string"
          },
          "direction": {
            "type": "string",
            "enum": ["up", "down", "both"]
          },
          "max_depth": {
            "type": "integer",
            "minimum": 1,
            "maximum": 10
          }
        },
        "required": ["class_name", "direction"]
      }
    }
  ]
}
```

**Error Response** (503 Service Unavailable):
```json
{
  "success": false,
  "error": "Service is initializing, please retry",
  "code": "INTERNAL_ERROR",
  "request_id": "550e8400-e29b-41d4-a716-446655440002",
  "timestamp": "2025-12-09T12:34:58.456Z"
}
```

**Response Headers** (503 only):
- `Retry-After`: Seconds to wait before retrying

### GET /health

Check service health and dependency status.

**Request**:
```bash
curl http://localhost:8001/health
```

**Healthy Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "code-graph-rag",
  "version": "0.0.24",
  "uptime_seconds": 3600,
  "dependencies": {
    "memgraph": {
      "status": "connected",
      "latency_ms": 5
    }
  },
  "timestamp": "2025-12-09T15:00:00.000Z"
}
```

**Degraded Response** (200 OK):
```json
{
  "status": "degraded",
  "service": "code-graph-rag",
  "version": "0.0.24",
  "uptime_seconds": 7200,
  "dependencies": {
    "memgraph": {
      "status": "unavailable"
    }
  },
  "timestamp": "2025-12-09T16:00:00.000Z"
}
```

**Health Statuses**:
- `healthy`: All dependencies connected
- `degraded`: Some dependencies unavailable
- `unavailable`: Service shutting down

**Dependency Statuses**:
- `connected`: Dependency is reachable and responsive
- `unavailable`: Dependency is unreachable or unresponsive
- `unknown`: Dependency status not yet checked

## Available Tools

### 1. query_callers

Find all functions that call a specified function.

**Arguments**:
- `function_name` (string, required): Qualified name of function to analyze
- `max_depth` (integer, optional): Maximum call chain depth (default: 1, max: 5)

**Example**:
```bash
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "query_callers",
    "arguments": {
      "function_name": "codebase_rag.services.graph_service.MemgraphIngestor.ensure_node_batch",
      "max_depth": 3
    }
  }' | jq
```

**Response**:
```json
{
  "success": true,
  "data": {
    "function_name": "codebase_rag.services.graph_service.MemgraphIngestor.ensure_node_batch",
    "callers": [
      {"name": "ingest_function", "module": "codebase_rag.parsers.python_parser"},
      {"name": "ingest_class", "module": "codebase_rag.parsers.python_parser"}
    ]
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-12-09T12:34:56.789Z",
  "meta": {
    "execution_time_ms": 45
  }
}
```

### 2. query_hierarchy

Query class inheritance hierarchy (ancestors, descendants, or both).

**Arguments**:
- `class_name` (string, required): Qualified name of class to analyze
- `direction` (string, required): Hierarchy direction - "up" (ancestors), "down" (descendants), or "both"
- `max_depth` (integer, optional): Maximum hierarchy depth (default: 10, max: 10)

**Example**:
```bash
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "query_hierarchy",
    "arguments": {
      "class_name": "codebase_rag.http.models.ResponseEnvelope",
      "direction": "both",
      "max_depth": 5
    }
  }' | jq
```

### 3. query_dependencies

Analyze module dependencies (imports and function calls).

**Arguments**:
- `target` (string, required): Module name or qualified name to analyze
- `dependency_type` (string, required): Type of dependencies - "imports", "calls", or "all"

**Example**:
```bash
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "query_dependencies",
    "arguments": {
      "target": "codebase_rag.services.graph_service",
      "dependency_type": "all"
    }
  }' | jq
```

### 4. query_implementations

Find all classes implementing an interface or extending a base class.

**Arguments**:
- `interface_name` (string, required): Qualified name of interface or base class

**Example**:
```bash
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "query_implementations",
    "arguments": {
      "interface_name": "pydantic.BaseModel"
    }
  }' | jq
```

### 5. query_module_exports

List all public exports from a module.

**Arguments**:
- `module_name` (string, required): Module name to query
- `include_private` (boolean, optional): Include private members (default: false)

**Example**:
```bash
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "query_module_exports",
    "arguments": {
      "module_name": "codebase_rag.http.models",
      "include_private": false
    }
  }' | jq
```

### 6. query_call_graph

Generate call graph from an entry point function.

**Arguments**:
- `entry_point` (string, required): Qualified name of entry point function
- `max_depth` (integer, optional): Maximum depth to traverse (default: 3, max: 5)
- `max_nodes` (integer, optional): Maximum nodes to return (default: 50, max: 100)

**Example**:
```bash
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "query_call_graph",
    "arguments": {
      "entry_point": "codebase_rag.main",
      "max_depth": 3,
      "max_nodes": 50
    }
  }' | jq
```

### 7. query_cypher

Execute custom Cypher queries (expert mode).

**Arguments**:
- `query` (string, required): Cypher query to execute

**Example**:
```bash
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "query_cypher",
    "arguments": {
      "query": "MATCH (f:Function)-[:CALLS]->(g:Function) WHERE f.name CONTAINS \"login\" RETURN f.name, g.name LIMIT 10"
    }
  }' | jq
```

## Response Envelope Format

All responses follow a standardized envelope format for consistency:

### Success Envelope

```json
{
  "success": true,
  "data": {
    // Tool-specific result data
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-12-09T12:34:56.789Z",
  "meta": {
    "execution_time_ms": 150,
    // Optional metadata (pagination, truncation, etc.)
  }
}
```

### Error Envelope

```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "request_id": "550e8400-e29b-41d4-a716-446655440001",
  "timestamp": "2025-12-09T12:34:57.123Z"
}
```

## Error Handling

### Common Error Scenarios

**Tool Not Found (404)**:
```bash
curl -X POST http://localhost:8001/call-tool \
  -d '{"tool": "invalid_tool", "arguments": {}}'
# Returns: {"success": false, "code": "TOOL_NOT_FOUND", "error": "Tool not found: invalid_tool"}
```

**Invalid Arguments (400)**:
```bash
curl -X POST http://localhost:8001/call-tool \
  -d '{"tool": "query_callers", "arguments": {"max_depth": 999}}'
# Returns: {"success": false, "code": "INVALID_ARGUMENTS", "error": "Invalid argument: max_depth must be between 1 and 5"}
```

**Execution Error (500)**:
```bash
curl -X POST http://localhost:8001/call-tool \
  -d '{"tool": "query_callers", "arguments": {"function_name": "nonexistent.function"}}'
# Returns: {"success": false, "code": "EXECUTION_ERROR", "error": "Node not found: nonexistent.function"}
```

**Timeout (408)**:
```bash
# Occurs when tool execution exceeds configured timeout (default: 30 seconds)
# Returns: {"success": false, "code": "TIMEOUT", "error": "Tool execution exceeded timeout of 30 seconds"}
```

**Rate Limited (429)**:
```bash
# Occurs when client exceeds rate limit (default: 1000 requests/minute)
# Returns: {"success": false, "code": "RATE_LIMITED", "error": "Rate limit exceeded: 1000 requests per minute"}
```

## Request Tracking

Use the optional `request_id` field to track requests across logs and distributed systems:

```bash
REQUEST_ID=$(uuidgen)
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d "{
    \"tool\": \"query_callers\",
    \"arguments\": {\"function_name\": \"my.function\"},
    \"request_id\": \"$REQUEST_ID\"
  }"

# Search logs for request_id
grep "$REQUEST_ID" deployment/launchagents/logs/code-graph-rag.log
```

If `request_id` is not provided, the server generates a UUID automatically.

## Performance

**Expected Response Times**:
- GET /tools: <100ms
- GET /health: <50ms (cached)
- POST /call-tool: <200ms p95 (typical codebase <10K nodes)

**Latency Factors**:
- Tool complexity (e.g., deep graph traversals)
- Codebase size (nodes in Memgraph)
- Memgraph connection latency
- Query result size

**Performance Tips**:
- Use `max_depth` and `max_nodes` parameters to limit result size
- Cache frequently-used query results client-side
- Use concurrent requests for independent queries
- Monitor `/health` endpoint for dependency latency

## Configuration

### Server Configuration

Edit `config/http-server.yaml`:

```yaml
service:
  name: "code-graph-rag"
  port: 8001
  host: "127.0.0.1"

server:
  workers: 1
  timeout: 30  # Request timeout in seconds
  graceful_shutdown_seconds: 5

monitoring:
  health_check_interval: 30  # Background health check interval

security:
  api_keys_enabled: false
  rate_limit: 1000  # Max requests per minute
  cors:
    enabled: true
    allowed_origins:
      - "http://localhost:*"

dependencies:
  memgraph:
    host: "localhost"
    port: 7687
    timeout: 1000  # Connection timeout in milliseconds
```

### Environment Variable Overrides

Override any configuration value using environment variables:

```bash
# Override port
export HTTP_SERVER__SERVICE__PORT=8002

# Override Memgraph host
export HTTP_SERVER__DEPENDENCIES__MEMGRAPH__HOST=memgraph.local

# Override timeout
export HTTP_SERVER__SERVER__TIMEOUT=60

# Start server with overrides
uv run python -m codebase_rag.http
```

### CLI Overrides

Override configuration via command-line arguments:

```bash
# Override host and port
uv run python -m codebase_rag.http --host 0.0.0.0 --port 9000

# Use custom config file
uv run python -m codebase_rag.http --config /path/to/custom-config.yaml

# CLI args take precedence over config file
uv run python -m codebase_rag.http --config custom.yaml --port 8888
```

## Authentication (Optional)

Enable API key authentication in `config/http-server.yaml`:

```yaml
security:
  api_keys_enabled: true
```

**Request with API key**:
```bash
curl -X POST http://localhost:8001/call-tool \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"tool": "query_callers", "arguments": {...}}'
```

**Note**: API key management is configured externally (not covered in this version).

## CORS Configuration

CORS is enabled by default for localhost origins. Customize in `config/http-server.yaml`:

```yaml
security:
  cors:
    enabled: true
    allowed_origins:
      - "http://localhost:*"
      - "http://127.0.0.1:*"
      - "https://app.example.com"
```

## Deployment

### Local Development

```bash
# Start with auto-reload
uv run python -m codebase_rag.http --reload --log-level debug
```

### Production (LaunchAgent)

```bash
# Install as macOS service
cd deployment/launchagents
./install.sh

# Manage service
./services-manager.sh start
./services-manager.sh status
./services-manager.sh logs
```

### Docker (Future)

```bash
# Build Docker image
docker build -t code-graph-rag:latest .

# Run container
docker run -p 8001:8001 \
  -e HTTP_SERVER__DEPENDENCIES__MEMGRAPH__HOST=host.docker.internal \
  code-graph-rag:latest
```

## Client Libraries

### Generated Python Client

```python
from mcp_clients.code_graph_rag import CodeGraphRagClient

# Initialize client
client = CodeGraphRagClient(base_url="http://localhost:8001")

# Query function callers
result = client.query_callers(
    function_name="codebase_rag.services.graph_service.MemgraphIngestor.ensure_node_batch",
    max_depth=3
)

print(result)
# {'function_name': '...', 'callers': [...]}
```

### Generated Bash Script

```bash
# Navigate to generated scripts
cd /path/to/http-service-wrappers/output/code-graph-rag/scripts

# Execute tool
./query_callers.sh "codebase_rag.services.graph_service.MemgraphIngestor.ensure_node_batch" 3
```

### Raw HTTP (curl)

```bash
# Execute tool
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "query_callers",
    "arguments": {
      "function_name": "my.function",
      "max_depth": 3
    }
  }' | jq
```

### Raw HTTP (httpie)

```bash
# Execute tool
http POST http://localhost:8001/call-tool \
  tool=query_callers \
  arguments:='{"function_name": "my.function", "max_depth": 3}'
```

## Troubleshooting

### Server Won't Start

```bash
# Check if port is in use
lsof -i :8001

# Check configuration
cat config/http-server.yaml

# Start with debug logging
uv run python -m codebase_rag.http --log-level debug
```

### Tool Execution Fails

```bash
# Check Memgraph connection
curl http://localhost:8001/health | jq '.dependencies.memgraph'

# Verify Memgraph is running
docker ps | grep memgraph

# Check logs
tail -f deployment/launchagents/logs/code-graph-rag.log
```

### Performance Issues

```bash
# Check health endpoint for dependency latency
curl http://localhost:8001/health | jq '.dependencies.memgraph.latency_ms'

# Monitor execution times
curl -X POST http://localhost:8001/call-tool -d '{...}' | jq '.meta.execution_time_ms'

# Reduce result size
# Use max_depth and max_nodes parameters to limit traversal
```

## OpenAPI Specification

The complete OpenAPI 3.1 specification is available at:

**File**: [specs/004-mcp-http-standard/contracts/openapi.yaml](../specs/004-mcp-http-standard/contracts/openapi.yaml)

**Import into tools**:
- Postman: Import OpenAPI file directly
- Swagger UI: Serve openapi.yaml and view at http://localhost:8080
- API clients: Generate clients using openapi-generator

## Support

- **Documentation**: See [README.md](../README.md) for full documentation
- **Configuration**: See [HTTP_SERVER_CONFIG.md](HTTP_SERVER_CONFIG.md) for detailed configuration
- **MCP Server**: See [claude-code-setup.md](claude-code-setup.md) for stdio protocol integration
- **Quick Start**: See [quickstart.md](../specs/004-mcp-http-standard/quickstart.md) for step-by-step guide

## Changelog

### v0.0.24 (2025-12-09)

- Initial HTTP API implementation
- POST /call-tool endpoint with standardized request/response
- GET /tools endpoint for tool discovery
- GET /health endpoint with background dependency checks
- LaunchAgent deployment support
- Automatic client wrapper generation
- Full OpenAPI 3.1 specification
