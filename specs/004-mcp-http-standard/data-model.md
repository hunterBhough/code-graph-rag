# Data Model: Standardized MCP HTTP Server Architecture

**Branch**: `004-mcp-http-standard`
**Date**: 2025-12-09

This document defines the core entities and their relationships for the standardized MCP HTTP server architecture.

## Core Entities

### 1. ResponseEnvelope

**Description**: Standard response structure returned by all HTTP endpoints across all services.

**Fields**:
- `success` (boolean, required): Indicates whether the request succeeded
- `data` (object, optional): Response payload when success=true
- `error` (string, optional): Human-readable error message when success=false
- `code` (string, optional): Machine-readable error code from ErrorCode enum
- `request_id` (string, required): UUID for request correlation (client-provided or auto-generated)
- `timestamp` (string, required): ISO 8601 timestamp of response generation
- `meta` (object, optional): Additional metadata (e.g., execution_time_ms, rate_limit_remaining)

**Validation Rules**:
- If `success=true`, `data` MUST be present and `error`/`code` MUST be null
- If `success=false`, `error` and `code` MUST be present and `data` MUST be null
- `request_id` MUST be valid UUID v4 format
- `timestamp` MUST be ISO 8601 format with milliseconds and Z timezone (e.g., "2025-12-09T12:34:56.789Z")
- `meta.execution_time_ms` MUST be non-negative integer if present

**Example (Success)**:
```json
{
  "success": true,
  "data": {
    "callers": ["function_a", "function_b"]
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-12-09T12:34:56.789Z",
  "meta": {
    "execution_time_ms": 150
  }
}
```

**Example (Error)**:
```json
{
  "success": false,
  "error": "Tool not found: invalid_tool_name",
  "code": "TOOL_NOT_FOUND",
  "request_id": "550e8400-e29b-41d4-a716-446655440001",
  "timestamp": "2025-12-09T12:34:57.123Z"
}
```

---

### 2. ErrorCode

**Description**: Enumeration of standardized error conditions across all services.

**Values**:
- `TOOL_NOT_FOUND`: Requested tool does not exist in service
- `INVALID_ARGUMENTS`: Tool arguments failed validation (type mismatch, missing required field, etc.)
- `EXECUTION_ERROR`: Tool execution failed (database error, dependency unavailable, etc.)
- `INTERNAL_ERROR`: Unexpected server error (unhandled exception, system failure)
- `TIMEOUT`: Tool execution exceeded configured timeout
- `RATE_LIMITED`: Request rejected due to rate limit (429 status code)
- `SERVICE_UNAVAILABLE`: Service is initializing or shutting down (503 status code)

**HTTP Status Code Mapping**:
| ErrorCode | HTTP Status | When to Use |
|-----------|-------------|-------------|
| TOOL_NOT_FOUND | 404 | Tool name not in /tools list |
| INVALID_ARGUMENTS | 400 | JSON Schema validation failure |
| EXECUTION_ERROR | 500 | Tool ran but failed (DB error, etc.) |
| INTERNAL_ERROR | 500 | Uncaught exception |
| TIMEOUT | 504 | Tool exceeded max execution time |
| RATE_LIMITED | 429 | Too many requests |
| SERVICE_UNAVAILABLE | 503 | Server starting/stopping |

---

### 3. ToolSchema

**Description**: Metadata about a single tool exposed by an MCP service.

**Fields**:
- `name` (string, required): Unique identifier for the tool (e.g., "query_callers")
- `description` (string, required): Human-readable description of tool's purpose
- `input_schema` (object, required): JSON Schema (Draft 7) defining valid input arguments
  - MUST include `type: "object"`
  - MUST include `properties` with field definitions
  - MAY include `required` array listing mandatory fields

**Validation Rules**:
- `name` MUST be valid Python identifier (alphanumeric + underscore, no spaces)
- `description` MUST be non-empty string
- `input_schema` MUST be valid JSON Schema Draft 7
- `input_schema.type` MUST equal "object"
- `input_schema.properties` MUST be present (may be empty object for tools with no args)

**Example**:
```json
{
  "name": "query_callers",
  "description": "Find all functions that call a specified function",
  "input_schema": {
    "type": "object",
    "properties": {
      "function_name": {
        "type": "string",
        "description": "Qualified name of the function to query"
      },
      "max_depth": {
        "type": "integer",
        "description": "Maximum call depth to traverse",
        "default": 3,
        "minimum": 1,
        "maximum": 10
      }
    },
    "required": ["function_name"]
  }
}
```

---

### 4. ServiceConfiguration

**Description**: Configuration for an HTTP server wrapping an MCP service.

**Fields**:
- `service.name` (string, required): Service identifier (e.g., "code-graph-rag")
- `service.port` (integer, required): HTTP port to listen on
- `service.host` (string, required): Bind address (typically "0.0.0.0" or "127.0.0.1")
- `monitoring.metrics_enabled` (boolean, optional): Enable Prometheus-style metrics endpoint
- `monitoring.health_check_interval` (integer, optional): Seconds between dependency health checks
- `security.api_keys_enabled` (boolean, optional): Require API key authentication
- `security.rate_limit` (integer, optional): Max requests per minute per client
- `dependencies` (object, optional): Service-specific dependency configuration (e.g., Memgraph host/port)

**Validation Rules**:
- `service.port` MUST be in range 1024-65535
- `service.name` MUST match pattern `^[a-z][a-z0-9-]*$` (lowercase, hyphens allowed)
- `monitoring.health_check_interval` MUST be >= 10 seconds
- `security.rate_limit` MUST be >= 10 requests/minute

**Example (code-graph-rag)**:
```yaml
service:
  name: "code-graph-rag"
  port: 8001
  host: "0.0.0.0"

monitoring:
  metrics_enabled: false
  health_check_interval: 30

security:
  api_keys_enabled: false
  rate_limit: 1000

dependencies:
  memgraph:
    host: "localhost"
    port: 7687
```

**State Transitions**:
- INITIALIZING → HEALTHY: All dependencies connected, tools loaded
- HEALTHY → DEGRADED: One or more dependencies unavailable but service operational
- DEGRADED → HEALTHY: All dependencies reconnected
- ANY → SHUTTING_DOWN: SIGTERM/SIGINT received
- SHUTTING_DOWN → STOPPED: All in-flight requests completed

---

### 5. ToolRequest

**Description**: Request payload for POST /call-tool endpoint.

**Fields**:
- `tool` (string, required): Name of tool to execute (must match ToolSchema.name)
- `arguments` (object, required): Tool-specific arguments (validated against ToolSchema.input_schema)
- `request_id` (string, optional): Client-provided UUID for request correlation

**Validation Rules**:
- `tool` MUST exist in service's /tools list
- `arguments` MUST pass JSON Schema validation against tool's input_schema
- `request_id` MUST be valid UUID v4 if provided (auto-generated if omitted)

**Example**:
```json
{
  "tool": "query_callers",
  "arguments": {
    "function_name": "my_module.my_function",
    "max_depth": 5
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440002"
}
```

---

### 6. ToolsResponse

**Description**: Response from GET /tools endpoint listing available tools.

**Fields**:
- `service` (string, required): Service name matching ServiceConfiguration.service.name
- `version` (string, required): Semantic version of service (from pyproject.toml or equivalent)
- `tools` (array, required): List of ToolSchema objects

**Validation Rules**:
- `service` MUST match configured service.name
- `version` MUST follow semantic versioning (major.minor.patch)
- `tools` array MAY be empty (service with no tools)

**Example**:
```json
{
  "service": "code-graph-rag",
  "version": "0.0.24",
  "tools": [
    {
      "name": "query_callers",
      "description": "Find all functions that call a specified function",
      "input_schema": { ... }
    },
    {
      "name": "query_hierarchy",
      "description": "Get class inheritance hierarchy",
      "input_schema": { ... }
    }
  ]
}
```

---

### 7. HealthResponse

**Description**: Response from GET /health endpoint indicating service status.

**Fields**:
- `status` (string, required): One of "healthy", "degraded", "unavailable"
- `service` (string, required): Service name
- `version` (string, required): Service version
- `uptime_seconds` (integer, required): Seconds since service started
- `dependencies` (object, required): Map of dependency names to status objects
  - Each dependency status includes `status` ("connected"/"unavailable") and optional `error` message
- `timestamp` (string, required): ISO 8601 timestamp of health check

**Validation Rules**:
- `status` = "healthy" if ALL dependencies are "connected"
- `status` = "degraded" if SOME dependencies are "unavailable" but service still operational
- `status` = "unavailable" if service cannot fulfill any requests
- `uptime_seconds` MUST be non-negative

**Example (Healthy)**:
```json
{
  "status": "healthy",
  "service": "code-graph-rag",
  "version": "0.0.24",
  "uptime_seconds": 7200,
  "dependencies": {
    "memgraph": {
      "status": "connected",
      "response_time_ms": 8
    }
  },
  "timestamp": "2025-12-09T14:30:00.000Z"
}
```

**Example (Degraded)**:
```json
{
  "status": "degraded",
  "service": "code-graph-rag",
  "version": "0.0.24",
  "uptime_seconds": 7201,
  "dependencies": {
    "memgraph": {
      "status": "unavailable",
      "error": "Connection timeout after 1000ms"
    }
  },
  "timestamp": "2025-12-09T14:30:01.000Z"
}
```

---

### 8. WrapperTemplate

**Description**: Jinja2 template for generating service client wrappers.

**Fields**:
- `name` (string, required): Template identifier (e.g., "bash-script", "python-module")
- `template_path` (string, required): Relative path to .j2 template file
- `output_extension` (string, required): File extension for generated wrappers (e.g., ".sh", ".py")
- `variables` (object, required): Template variables extracted from ToolSchema
  - `tool_name`: Tool identifier
  - `description`: Tool description
  - `arguments`: Dict of argument name → JSON Schema
  - `service_url`: HTTP endpoint URL

**Example**:
```python
# WrapperTemplate is not serialized; it's a code-level abstraction
class WrapperTemplate:
    name: str = "bash-script"
    template_path: Path = Path("templates/bash-script.j2")
    output_extension: str = ".sh"
    
    def render(self, tool: ToolSchema, service_url: str) -> str:
        return self.env.get_template(self.template_path).render(
            tool_name=tool.name,
            description=tool.description,
            arguments=tool.input_schema['properties'],
            service_url=service_url
        )
```

---

### 9. ServiceRegistry

**Description**: Collection of services used by wrapper generator.

**Fields**:
- `services` (array, required): List of service configurations
  - `name` (string): Service identifier
  - `url` (string): HTTP base URL (e.g., "http://localhost:8001")
  - `enabled` (boolean): Whether to include in generation

**File Format** (`services.yaml`):
```yaml
services:
  - name: ai-gateway
    url: http://localhost:8000
    enabled: true
  
  - name: code-graph-rag
    url: http://localhost:8001
    enabled: true
  
  - name: seekr
    url: http://localhost:8002
    enabled: true
  
  - name: docwell
    url: http://localhost:8003
    enabled: false  # Disabled during development
```

---

## Entity Relationships

```text
ServiceConfiguration
    ↓ configures
HTTPServer
    ↓ exposes
[ToolSchema, ToolSchema, ...]
    ↓ consumed by
WrapperGenerator
    ↓ uses
WrapperTemplate
    ↓ produces
GeneratedWrappers (bash scripts, Python modules, etc.)

ToolRequest
    ↓ sent to
HTTPServer
    ↓ executes
MCPTool
    ↓ returns
ResponseEnvelope
```

## Data Flow

### 1. Tool Execution Flow
```text
Client → ToolRequest (POST /call-tool)
    ↓
HTTPServer validates request
    ↓
MCPToolExecutor invokes MCP tool
    ↓
MCP tool queries Memgraph / performs action
    ↓
HTTPServer wraps result in ResponseEnvelope
    ↓
Client receives ResponseEnvelope with data or error
```

### 2. Wrapper Generation Flow
```text
WrapperGenerator reads ServiceRegistry (services.yaml)
    ↓
For each enabled service:
    Fetch ToolsResponse (GET /tools)
        ↓
    For each ToolSchema:
        Load WrapperTemplate (bash, python, cli, skills)
            ↓
        Render template with tool metadata
            ↓
        Write generated wrapper to output directory
```

### 3. Health Check Flow
```text
Monitoring system → GET /health
    ↓
HTTPServer checks service dependencies
    ↓
For each dependency (e.g., Memgraph):
    Execute health check query (RETURN 1)
    Record status + response time
    ↓
HTTPServer aggregates dependency statuses
    ↓
Determine overall status (healthy/degraded/unavailable)
    ↓
Return HealthResponse
```

---

## Validation Summary

All entities have validation rules derived from functional requirements:

- **ResponseEnvelope**: Ensures consistent response format (FR-004)
- **ErrorCode**: Enforces standard error codes (FR-005)
- **ToolSchema**: Validates tool metadata structure (FR-002)
- **ServiceConfiguration**: Ensures valid configuration (FR-038, FR-039)
- **ToolRequest**: Validates tool execution requests (FR-001)
- **ToolsResponse**: Ensures discoverability (FR-002)
- **HealthResponse**: Enforces health status reporting (FR-003)
- **WrapperTemplate**: Enables automated wrapper generation (FR-041-051)
- **ServiceRegistry**: Configures wrapper generator (FR-042)

No circular dependencies exist between entities. All relationships are unidirectional or mediated by the HTTP server.
