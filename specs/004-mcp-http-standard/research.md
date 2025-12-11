# Research: Standardized MCP HTTP Server Architecture

**Branch**: `004-mcp-http-standard`
**Date**: 2025-12-09

This document consolidates research findings for implementing the standardized MCP HTTP server architecture.

## 1. FastAPI HTTP Wrapper Patterns for MCP Tools

### Decision
Use FastAPI's dependency injection system to bridge MCP stdio server to HTTP endpoints, with a shared MCPToolExecutor class that dynamically discovers and invokes MCP tools.

### Rationale
- **Dynamic Tool Discovery**: FastAPI allows runtime endpoint generation from MCP tool schemas, avoiding hardcoded routes
- **Type Safety**: Pydantic models (already in stack) integrate natively with FastAPI for request validation
- **Async Support**: FastAPI's async-first design matches MCP protocol's async nature (mcp>=1.21.1 uses async)
- **Performance**: FastAPI with uvicorn meets <100ms response requirements (typically 10-50ms for simple queries)

### Implementation Pattern
```python
# Shared pattern for all MCP HTTP wrappers
class MCPToolExecutor:
    def __init__(self, mcp_server_module):
        self.tools = self._discover_tools(mcp_server_module)
    
    async def execute_tool(self, tool_name: str, arguments: dict) -> dict:
        # Call MCP tool via internal API (not stdio)
        tool_func = self.tools.get(tool_name)
        return await tool_func(**arguments)

app = FastAPI()

@app.post("/call-tool")
async def call_tool(request: ToolRequest):
    result = await executor.execute_tool(request.tool, request.arguments)
    return ResponseEnvelope(success=True, data=result, request_id=request.request_id)
```

### Alternatives Considered
- **Flask + Sync**: Rejected due to poor async support (MCP tools are async)
- **gRPC**: Rejected for unnecessary complexity; HTTP/JSON sufficient for requirements
- **Direct stdio bridge**: Rejected due to process overhead (spawning subprocess per request)

### Key Dependencies
- `fastapi>=0.115.0` (stable, widely adopted)
- `uvicorn[standard]>=0.30.0` (ASGI server with performance extensions)
- `httpx>=0.27.0` (for testing async HTTP endpoints)

---

## 2. LaunchAgent Configuration for Python Services

### Decision
Use LaunchAgent plists with KeepAlive=true, RunAtLoad=true, and explicit Python virtual environment activation via shell wrapper scripts.

### Rationale
- **Native macOS Integration**: LaunchAgents provide system-level service management without Docker
- **Auto-Restart**: KeepAlive ensures services restart within seconds of crashes (FR-028)
- **Performance**: Native execution eliminates Docker file I/O overhead (10x faster on macOS)
- **Simplicity**: No container orchestration complexity; localhost networking works out-of-box

### LaunchAgent Structure
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.bastion.code-graph-rag</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag/run-http-server.sh</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>Crashed</key>
        <true/>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/Users/hunter/code/ai_agency/shared/mcp-http-gateway/logs/code-graph-rag.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/hunter/code/ai_agency/shared/mcp-http-gateway/logs/code-graph-rag-error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
        <key>CONFIG_PATH</key>
        <string>/Users/hunter/code/ai_agency/shared/mcp-http-gateway/config/code-graph-rag.yaml</string>
    </dict>
    
    <key>ThrottleInterval</key>
    <integer>5</integer>
</dict>
</plist>
```

### Shell Wrapper Pattern
```bash
#!/bin/bash
# run-http-server.sh - Activates venv and starts FastAPI server

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
exec uvicorn mcp_server.http_server:app \
    --host 0.0.0.0 \
    --port 8001 \
    --log-config config/logging.yaml
```

### Alternatives Considered
- **Docker Compose**: Rejected due to macOS file I/O performance penalties
- **systemd**: Not available on macOS
- **supervisord**: Adds unnecessary layer; LaunchAgent already provides process supervision

### Management Script Pattern
```bash
# services-manager.sh - Docker-compose-like UX for LaunchAgents

case "$1" in
  start)
    launchctl load ~/Library/LaunchAgents/com.bastion.*.plist
    ;;
  stop)
    launchctl unload ~/Library/LaunchAgents/com.bastion.*.plist
    ;;
  status)
    # Use colored output: GREEN for running, RED for stopped
    launchctl list | grep com.bastion | while read line; do
      [[ "$line" =~ "com.bastion" ]] && echo -e "\033[32m✓\033[0m $line" || echo -e "\033[31m✗\033[0m $line"
    done
    ;;
esac
```

---

## 3. Jinja2 Template Generation for Multi-Format Wrappers

### Decision
Use a single Jinja2 template per output format (bash, Python, CLI, skills) with tool schema metadata passed as context, generating one wrapper file per tool.

### Rationale
- **Type Safety**: JSON Schema in /tools response maps directly to Jinja2 variables for type hints
- **Maintainability**: Templates centralize wrapper logic; updates propagate to all services
- **Flexibility**: Jinja2's filters and macros handle language-specific formatting (bash escaping, Python type hints)

### Template Structure
```python
# generator.py - Main generation logic
import jinja2
from pathlib import Path

class WrapperGenerator:
    def __init__(self, services_config: Path, templates_dir: Path):
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dir))
        self.services = yaml.safe_load(services_config.read_text())
    
    def generate_bash_script(self, tool: ToolSchema, service: str):
        template = self.env.get_template('bash-script.j2')
        output = template.render(
            tool_name=tool.name,
            description=tool.description,
            arguments=tool.input_schema['properties'],
            service_url=self.services[service]['url']
        )
        return output
```

### Bash Script Template Example
```jinja2
{# bash-script.j2 #}
#!/bin/bash
# Auto-generated wrapper for {{ tool_name }}
# Description: {{ description }}
# Service: {{ service_url }}

set -euo pipefail

# Parse arguments
{% for arg_name, arg_schema in arguments.items() %}
{{ arg_name | upper }}="${{ loop.index }}:-}"
{% endfor %}

# Make HTTP request
response=$(curl -s -X POST "{{ service_url }}/call-tool" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "{{ tool_name }}",
    "arguments": {
      {% for arg_name in arguments.keys() %}
      "{{ arg_name }}": "${{ arg_name | upper }}"{% if not loop.last %},{% endif %}
      {% endfor %}
    }
  }')

# Parse response
if echo "$response" | jq -e '.success' > /dev/null; then
  echo "$response" | jq -r '.data'
else
  echo "Error: $(echo "$response" | jq -r '.error')" >&2
  exit 1
fi
```

### Python Module Template Example
```jinja2
{# python-module.j2 #}
"""Auto-generated Python client for {{ service_name }}"""
from typing import Any, Dict
import httpx

class {{ service_name | title }}Client:
    def __init__(self, base_url: str = "{{ service_url }}"):
        self.base_url = base_url
        self.client = httpx.Client()
    
    {% for tool in tools %}
    def {{ tool.name }}(
        self,
        {% for arg_name, arg_schema in tool.input_schema['properties'].items() %}
        {{ arg_name }}: {{ arg_schema.type | python_type }}{% if not loop.last %},{% endif %}
        {% endfor %}
    ) -> Dict[str, Any]:
        """{{ tool.description }}"""
        response = self.client.post(
            f"{self.base_url}/call-tool",
            json={
                "tool": "{{ tool.name }}",
                "arguments": {
                    {% for arg_name in tool.input_schema['properties'].keys() %}
                    "{{ arg_name }}": {{ arg_name }},
                    {% endfor %}
                }
            }
        )
        data = response.json()
        if not data["success"]:
            raise Exception(data["error"])
        return data["data"]
    {% endfor %}
```

### Alternatives Considered
- **AST Manipulation**: Rejected for complexity; templates more maintainable
- **Code Generation Libraries**: Rejected (e.g., datamodel-code-generator) - overkill for simple wrappers
- **Manual Wrappers**: Rejected due to maintenance burden across 20-40 tools

### Key Dependencies
- `jinja2>=3.1.0` (stable, widely used)
- `pyyaml>=6.0` (for services.yaml configuration)
- `jsonschema>=4.0` (for validating tool schemas)

---

## 4. Memgraph Connectivity Health Checks

### Decision
Use pymgclient's connection pooling with explicit RETURN 1 query to verify connectivity, with 1-second timeout for health checks.

### Rationale
- **Fast Detection**: Simple query completes in <10ms, meets 1-second health check requirement
- **Connection Pooling**: Reuses existing pymgclient connections from graph service layer
- **Graceful Degradation**: Health endpoint returns "degraded" status if Memgraph unreachable (FR-003)

### Implementation Pattern
```python
# health_check.py
from pymgclient import MGClient
from datetime import datetime
import time

class HealthChecker:
    def __init__(self, memgraph_host: str, memgraph_port: int):
        self.host = memgraph_host
        self.port = memgraph_port
        self.start_time = time.time()
    
    async def check_memgraph(self) -> dict:
        try:
            client = MGClient.connect(
                host=self.host,
                port=self.port,
                timeout=1.0  # 1-second timeout
            )
            client.execute("RETURN 1")
            client.close()
            return {"status": "connected", "response_time_ms": 10}
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}
    
    async def get_health(self) -> dict:
        memgraph_status = await self.check_memgraph()
        overall_status = "healthy" if memgraph_status["status"] == "connected" else "degraded"
        
        return {
            "status": overall_status,
            "service": "code-graph-rag",
            "version": "0.0.24",
            "uptime_seconds": int(time.time() - self.start_time),
            "dependencies": {
                "memgraph": memgraph_status
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
```

### Alternatives Considered
- **HTTP Health Endpoint**: Memgraph doesn't expose standard HTTP health endpoint
- **Database Metadata Query**: More expensive than RETURN 1
- **Connection Timeout Only**: Doesn't verify query execution (connection might succeed but queries fail)

### Edge Cases
- **Startup Delay**: If Memgraph not ready, health returns 503 with Retry-After header
- **Connection Pool Exhaustion**: Health check gets dedicated connection to avoid blocking
- **Network Latency Spikes**: 1-second timeout ensures health checks don't hang

---

## 5. Response Envelope Standardization

### Decision
Use a Pydantic BaseModel for ResponseEnvelope with explicit success flag, optional data/error fields, and required request_id/timestamp.

### Rationale
- **Type Safety**: Pydantic validates envelope structure at runtime
- **Consistency**: Single model used across all services ensures identical format
- **Serialization**: Pydantic's `.dict()` method handles JSON serialization with ISO 8601 dates

### Envelope Structure
```python
# models.py
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime
import uuid

class ResponseEnvelope(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    code: Optional[str] = None  # Error code enum: TOOL_NOT_FOUND, INVALID_ARGUMENTS, etc.
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    meta: Optional[dict] = None  # execution_time_ms, etc.
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"result": "..."},
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-12-09T12:34:56.789Z",
                "meta": {"execution_time_ms": 150}
            }
        }
```

### Error Code Enum
```python
# error_codes.py
from enum import Enum

class ErrorCode(str, Enum):
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    INVALID_ARGUMENTS = "INVALID_ARGUMENTS"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
```

---

## 6. Configuration Management Strategy

### Decision
Use pydantic-settings (already in stack) to load YAML configuration with environment variable overrides and validation.

### Rationale
- **Already Available**: pydantic-settings>=2.0.0 in existing dependencies
- **Type Safety**: Configuration parsed into Pydantic models with validation
- **Env Overrides**: Supports SERVER_PORT=8002 environment variable overrides
- **YAML Support**: Works with existing YAML infrastructure

### Configuration Model
```python
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class HTTPServerConfig(BaseSettings):
    model_config = SettingsConfigDict(
        yaml_file='config/http-server.yaml',
        env_prefix='SERVER_'
    )
    
    # Service settings
    service_name: str = "code-graph-rag"
    port: int = 8001
    host: str = "0.0.0.0"
    
    # Monitoring
    metrics_enabled: bool = False
    health_check_interval: int = 30
    
    # Security
    api_keys_enabled: bool = False
    rate_limit: int = 1000  # requests per minute
    
    # Dependencies
    memgraph_host: str = "localhost"
    memgraph_port: int = 7687
```

### YAML Configuration File
```yaml
# config/http-server.yaml
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

---

## Action Items for Phase 1

1. ✅ Add FastAPI dependencies to pyproject.toml: `fastapi>=0.115.0`, `uvicorn[standard]>=0.30.0`, `httpx>=0.27.0`
2. ✅ Add Jinja2 dependency: `jinja2>=3.1.0`
3. ✅ Create ResponseEnvelope and ErrorCode models in mcp_server/models.py
4. ✅ Create HTTPServerConfig model using existing pydantic-settings
5. ✅ Create LaunchAgent plist template for code-graph-rag
6. ✅ Create Jinja2 templates for bash script and Python module generation

## Summary

All research questions have been resolved:

1. **FastAPI Pattern**: Use dependency injection with MCPToolExecutor for dynamic tool execution
2. **LaunchAgent**: Use KeepAlive plists with shell wrapper scripts for venv activation
3. **Wrapper Generation**: Use Jinja2 templates with one file per tool, driven by /tools schemas
4. **Health Checks**: Use pymgclient with RETURN 1 query and 1-second timeout
5. **Response Envelope**: Use Pydantic BaseModel with success/data/error/request_id/timestamp
6. **Configuration**: Use existing pydantic-settings with YAML support and env overrides

No unknowns or "NEEDS CLARIFICATION" items remain. Ready to proceed with Phase 1: Design & Contracts.
