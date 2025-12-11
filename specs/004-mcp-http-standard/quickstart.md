# Quick Start: Standardized MCP HTTP Server Architecture

**Branch**: `004-mcp-http-standard`
**Date**: 2025-12-09

This guide walks you through setting up, deploying, and using the standardized MCP HTTP server architecture.

## Overview

This feature provides:
- **Unified HTTP API** across four MCP services (ai-gateway, code-graph-rag, seekr, docwell)
- **LaunchAgent deployment** for native macOS integration with auto-restart
- **Wrapper generator** for automatic client creation (bash, Python, CLI, skills)
- **Standard endpoints**: POST /call-tool, GET /tools, GET /health
- **Response standardization**: Consistent envelopes and error codes

## Prerequisites

- macOS with LaunchAgent support
- Python 3.12+ with uv installed
- Memgraph running at localhost:7687 (for code-graph-rag)
- Ports 8000-8003 available

## Installation

### Step 1: Install HTTP Server Dependencies

```bash
# Navigate to code-graph-rag repo
cd /Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag

# Add HTTP server dependencies to pyproject.toml
uv add fastapi uvicorn[standard] httpx jinja2

# Install dependencies
uv sync
```

### Step 2: Deploy Services with LaunchAgents

```bash
# Navigate to mcp-http-gateway directory
cd /Users/hunter/code/ai_agency/shared/mcp-http-gateway

# Install LaunchAgent plists
./install.sh

# Start all services
./services-manager.sh start

# Verify services are running
./services-manager.sh status
```

Expected output:
```
✓ ai-gateway       [8000]  healthy
✓ code-graph-rag   [8001]  healthy
✓ seekr            [8002]  healthy
✓ docwell          [8003]  healthy
```

### Step 2 (Alternative): Run HTTP Server Manually

Instead of using LaunchAgents, you can run the HTTP server directly:

```bash
# Navigate to code-graph-rag repo
cd /Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag

# Start server with default configuration (config/http-server.yaml)
uv run python -m codebase_rag.http

# Override host and port via CLI arguments
uv run python -m codebase_rag.http --host 0.0.0.0 --port 9000

# Use custom configuration file
uv run python -m codebase_rag.http --config /path/to/custom-config.yaml

# Combine config file with CLI overrides (CLI args take precedence)
uv run python -m codebase_rag.http --config custom.yaml --port 8888

# Enable auto-reload for development
uv run python -m codebase_rag.http --reload

# Set logging level
uv run python -m codebase_rag.http --log-level debug
```

Expected startup output:
```
================================================================================
Code Graph RAG HTTP Server
================================================================================
Service:  code-graph-rag
Version:  0.0.24
Host:     127.0.0.1
Port:     8001
Workers:  1
Timeout:  30s
Reload:   False
================================================================================
Configuration loaded:
  - CORS enabled: True
  - Allowed origins: http://localhost:*, http://127.0.0.1:*
  - Health check interval: 30s
  - Memgraph: localhost:7687
  - Graceful shutdown: 5s
================================================================================
Starting server on http://127.0.0.1:8001
Press Ctrl+C to stop
================================================================================
```

#### Configuration File Format

The default configuration file is `config/http-server.yaml`:

```yaml
service:
  name: "code-graph-rag"
  port: 8001
  host: "127.0.0.1"  # Use localhost for development

server:
  workers: 1
  timeout: 30  # Request timeout in seconds
  graceful_shutdown_seconds: 5  # Wait for in-flight requests

monitoring:
  metrics_enabled: false
  health_check_interval: 30  # Background health check interval

security:
  api_keys_enabled: false
  rate_limit: 1000  # Max requests per minute
  cors:
    enabled: true
    allowed_origins:
      - "http://localhost:*"
      - "http://127.0.0.1:*"

dependencies:
  memgraph:
    host: "localhost"
    port: 7687
    timeout: 1000  # Connection timeout in milliseconds
```

#### CLI Arguments Reference

| Argument | Type | Description | Default |
|----------|------|-------------|---------|
| `--host` | string | Host address to bind to | `127.0.0.1` |
| `--port` | integer | Port to listen on | `8001` |
| `--config` | path | Path to YAML config file | `config/http-server.yaml` |
| `--reload` | flag | Enable auto-reload (dev only) | `false` |
| `--log-level` | choice | Logging level (debug/info/warning/error/critical) | `info` |

**Note**: CLI arguments override values from the configuration file.

#### Error Handling

The server will fail fast with clear error messages if configuration is invalid:

```bash
# Missing config file
$ uv run python -m codebase_rag.http --config missing.yaml
ERROR: Configuration file not found: missing.yaml
ERROR: Please create config/http-server.yaml or specify a valid config file with --config

# Invalid YAML syntax
$ uv run python -m codebase_rag.http
ERROR: Configuration validation failed: Invalid YAML in config/http-server.yaml: ...
ERROR: Please check your YAML file for syntax errors and ensure all required fields are present

# Invalid port value
$ uv run python -m codebase_rag.http --port 99999
ERROR: Configuration validation failed after applying CLI overrides: ...
ERROR: Please check that your --host and --port values are valid
```

### Step 3: Verify Service Health

```bash
# Check code-graph-rag health
curl http://localhost:8001/health | jq

# Expected response:
# {
#   "status": "healthy",
#   "service": "code-graph-rag",
#   "version": "0.0.24",
#   "uptime_seconds": 120,
#   "dependencies": {
#     "memgraph": {
#       "status": "connected",
#       "response_time_ms": 8
#     }
#   },
#   "timestamp": "2025-12-09T14:30:00.000Z"
# }
```

## Basic Usage

### Discover Available Tools

```bash
# List code-graph-rag tools
curl http://localhost:8001/tools | jq

# Response includes all tools with their schemas
# {
#   "service": "code-graph-rag",
#   "version": "0.0.24",
#   "tools": [
#     {
#       "name": "query_callers",
#       "description": "Find all functions that call a specified function",
#       "input_schema": { ... }
#     },
#     ...
#   ]
# }
```

### Execute a Tool

```bash
# Call query_callers tool
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "query_callers",
    "arguments": {
      "function_name": "codebase_rag.services.graph_service.MemgraphIngestor.ensure_node_batch",
      "max_depth": 3
    },
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }' | jq

# Success response:
# {
#   "success": true,
#   "data": {
#     "callers": ["function_a", "function_b"]
#   },
#   "request_id": "550e8400-e29b-41d4-a716-446655440000",
#   "timestamp": "2025-12-09T12:34:56.789Z",
#   "meta": {
#     "execution_time_ms": 150
#   }
# }
```

### Handle Errors

```bash
# Try calling non-existent tool
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "invalid_tool",
    "arguments": {}
  }' | jq

# Error response:
# {
#   "success": false,
#   "error": "Tool not found: invalid_tool",
#   "code": "TOOL_NOT_FOUND",
#   "request_id": "550e8400-e29b-41d4-a716-446655440001",
#   "timestamp": "2025-12-09T12:34:57.123Z"
# }
```

## Service Management

### Start/Stop/Restart Services

```bash
# Start all services
./services-manager.sh start

# Stop all services (graceful shutdown)
./services-manager.sh stop

# Restart all services
./services-manager.sh restart

# Check service status
./services-manager.sh status
```

### View Service Logs

```bash
# Tail logs for specific service
./services-manager.sh logs code-graph-rag

# View error logs
tail -f logs/code-graph-rag-error.log

# View all logs
tail -f logs/*.log
```

### Health Monitoring

```bash
# Monitor all service health
./services-manager.sh health

# Expected output:
# ai-gateway:      healthy  (200ms)
# code-graph-rag:  healthy  (150ms)
# seekr:           healthy  (180ms)
# docwell:         degraded (500ms) - Dependency unavailable
```

## Wrapper Generator

### Generate Client Wrappers

```bash
# Navigate to wrapper generator
cd /Users/hunter/code/ai_agency/shared/mcp-service-wrappers

# Generate wrappers for all services
python generator.py

# Generate for specific service only
python generator.py --service code-graph-rag

# Generate specific wrapper types only
python generator.py --type bash,python
```

### Using Generated Bash Scripts

```bash
# Generated scripts are in output/scripts/
cd output/scripts/code-graph-rag

# Execute tool via bash script
./query_callers.sh "codebase_rag.services.graph_service.MemgraphIngestor.ensure_node_batch" 3

# Output is formatted and exits with status code
# Exit 0 on success, 1 on error
```

### Using Generated Python Module

```python
# Generated Python modules are in output/python/
from mcp_clients.code_graph_rag import CodeGraphRagClient

client = CodeGraphRagClient(base_url="http://localhost:8001")

# Call tools with type hints
result = client.query_callers(
    function_name="codebase_rag.services.graph_service.MemgraphIngestor.ensure_node_batch",
    max_depth=3
)

print(result)  # {'callers': [...]}
```

## Configuration

### Service Configuration

Each service has a YAML configuration file in `config/`:

```yaml
# config/code-graph-rag.yaml
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

### Environment Variable Overrides

```bash
# Override port via environment variable
SERVER_PORT=8005 ./run-http-server.sh

# Override Memgraph host
SERVER_DEPENDENCIES__MEMGRAPH__HOST=192.168.1.100 ./run-http-server.sh
```

### Wrapper Generator Configuration

```yaml
# config/services.yaml
services:
  - name: ai-gateway
    url: http://localhost:8000
    enabled: true
  
  - name: code-graph-rag
    url: http://localhost:8001
    enabled: true
  
  - name: seekr
    url: http://localhost:8002
    enabled: false  # Disable during development
  
  - name: docwell
    url: http://localhost:8003
    enabled: true
```

## Troubleshooting

### Service Won't Start

```bash
# Check if port is already in use
lsof -i :8001

# Check LaunchAgent status
launchctl list | grep com.bastion

# View service logs
tail -f logs/code-graph-rag-error.log

# Unload and reload LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.bastion.code-graph-rag.plist
launchctl load ~/Library/LaunchAgents/com.bastion.code-graph-rag.plist
```

### Dependency Connection Failures

```bash
# Check Memgraph status
docker ps | grep memgraph

# Restart Memgraph
docker compose restart memgraph

# Verify Memgraph is reachable
nc -zv localhost 7687

# Check service health
curl http://localhost:8001/health | jq '.dependencies'
```

### Wrapper Generator Fails

```bash
# Verify service is running
curl http://localhost:8001/tools

# Check service URL in services.yaml
cat config/services.yaml

# Run generator with verbose logging
python generator.py --verbose

# Test generated wrapper
bash output/scripts/code-graph-rag/query_callers.sh "test.function" 1
```

### Request Errors

```bash
# Check error code in response
curl -X POST http://localhost:8001/call-tool -d '...' | jq '.code'

# Common error codes:
# TOOL_NOT_FOUND - Check tool name against /tools list
# INVALID_ARGUMENTS - Verify arguments against tool's input_schema
# EXECUTION_ERROR - Check service logs and dependency health

# Debug with request_id
REQUEST_ID=$(uuidgen)
curl -X POST http://localhost:8001/call-tool \
  -d "{\"tool\": \"...\", \"arguments\": {...}, \"request_id\": \"$REQUEST_ID\"}" | jq

# Search logs for request_id
grep "$REQUEST_ID" logs/code-graph-rag.log
```

## Testing

### Manual Testing

```bash
# Test POST /call-tool
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d '{"tool": "query_callers", "arguments": {"function_name": "test.func"}}' | jq

# Test GET /tools
curl http://localhost:8001/tools | jq '.tools | length'

# Test GET /health
curl http://localhost:8001/health | jq '.status'
```

### Automated Testing

```bash
# Run HTTP server tests
cd /Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag
uv run pytest tests/http/

# Run integration tests (requires services running)
uv run pytest tests/integration/test_launchagent_deployment.py

# Run wrapper generator tests
cd /Users/hunter/code/ai_agency/shared/mcp-service-wrappers
python -m pytest tests/
```

## Performance Benchmarking

```bash
# Benchmark /tools endpoint (<100ms requirement)
ab -n 1000 -c 10 http://localhost:8001/tools

# Benchmark /call-tool endpoint
ab -n 100 -c 10 -p request.json -T application/json \
  http://localhost:8001/call-tool

# Monitor response times
./services-manager.sh health --watch
```

## Next Steps

1. **Integrate with Claude Code**: Add HTTP endpoints to Claude Code MCP configuration
2. **Custom Wrappers**: Create custom Jinja2 templates for specialized output formats
3. **Monitoring**: Enable metrics_enabled in config for Prometheus integration
4. **Security**: Enable api_keys_enabled for authenticated access
5. **Scaling**: Deploy multiple instances with load balancer for high availability

## API Reference

See contracts/ directory for complete OpenAPI specifications:
- `contracts/http-api.yaml` - Full endpoint documentation
- `contracts/response-envelope.yaml` - Response format schema
- `contracts/error-codes.yaml` - Error code definitions

## Support

- View logs: `./services-manager.sh logs <service>`
- Check health: `./services-manager.sh health`
- Report issues with request_id for faster debugging
- Consult error-codes.yaml for error resolution guidance
