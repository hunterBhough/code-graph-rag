# Phase 10 Validation Tasks

This document provides step-by-step instructions for completing the validation tasks (T100-T106) from Phase 10.

## Prerequisites

- HTTP server dependencies installed: `uv sync`
- Memgraph running: `docker compose up -d`
- Repository indexed (optional but recommended for realistic tests)

## T100: Quickstart.md Validation

**Goal**: Verify all example commands in quickstart.md work end-to-end

### Test 1: Manual Server Startup

```bash
# Navigate to code-graph-rag repo
cd /Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag

# Start with default configuration
uv run python -m codebase_rag.http

# Expected: Server starts on port 8001 with startup banner
# Look for: "Starting server on http://127.0.0.1:8001"
```

**Success criteria**: Server starts without errors, displays configuration, port 8001 accessible

### Test 2: Configuration Overrides

```bash
# Override host and port
uv run python -m codebase_rag.http --host 0.0.0.0 --port 9000

# Expected: Server starts on port 9000, accessible from all interfaces
```

**Success criteria**: Server respects CLI overrides, starts on correct port

### Test 3: Health Check

```bash
# In a new terminal
curl http://localhost:8001/health | jq

# Expected response:
# {
#   "status": "healthy" or "degraded",
#   "service": "code-graph-rag",
#   "version": "0.0.24",
#   "uptime_seconds": <number>,
#   "dependencies": {
#     "memgraph": {
#       "status": "connected" or "unavailable",
#       "latency_ms": <number>
#     }
#   }
# }
```

**Success criteria**: Health endpoint returns valid JSON with correct structure

### Test 4: Tool Discovery

```bash
curl http://localhost:8001/tools | jq

# Expected: JSON response with:
# - service: "code-graph-rag"
# - version: "0.0.24"
# - tools: array with objects containing name, description, input_schema
```

**Success criteria**: Tools endpoint returns list of available MCP tools

### Test 5: Tool Execution

```bash
# Call query_callers tool
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "query_callers",
    "arguments": {
      "function_name": "codebase_rag.services.graph_service.MemgraphIngestor.ensure_node_batch",
      "max_depth": 3
    }
  }' | jq

# Expected response:
# {
#   "success": true,
#   "data": { ... },
#   "request_id": "<uuid>",
#   "timestamp": "<iso8601>",
#   "meta": {
#     "execution_time_ms": <number>
#   }
# }
```

**Success criteria**: Tool executes successfully, returns standardized envelope

### Test 6: Error Handling

```bash
# Try non-existent tool
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "invalid_tool",
    "arguments": {}
  }' | jq

# Expected response:
# {
#   "success": false,
#   "error": "Tool not found: invalid_tool",
#   "code": "TOOL_NOT_FOUND",
#   "request_id": "<uuid>",
#   "timestamp": "<iso8601>"
# }
```

**Success criteria**: Error responses follow standardized envelope format

## T101: OpenAPI Examples Validation

**Goal**: Verify all OpenAPI examples match actual server behavior

### Test 1: Verify /call-tool Examples

Open `specs/004-mcp-http-standard/contracts/openapi.yaml` and test each example:

```bash
# Example 1: query_callers
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "query_callers",
    "arguments": {
      "function_name": "process_data",
      "max_depth": 3
    }
  }' | jq

# Compare response structure with OpenAPI spec
```

### Test 2: Verify Error Responses

Test each error scenario documented in openapi.yaml:

```bash
# 400 - Invalid Arguments
curl -X POST http://localhost:8001/call-tool \
  -d '{"tool": "query_callers", "arguments": {"max_depth": 999}}'

# 404 - Tool Not Found
curl -X POST http://localhost:8001/call-tool \
  -d '{"tool": "nonexistent", "arguments": {}}'
```

**Success criteria**: All examples produce responses matching OpenAPI specification

## T102: Logging Verification

**Already completed** - Enhanced logging added for configuration loading, tool discovery, and dependency checks.

Verify by reviewing logs:
```bash
uv run python -m codebase_rag.http --log-level debug

# Look for log messages:
# - "Loading configuration from: ..."
# - "Configuring dependencies:"
# - "Initializing MCP tools registry..."
# - "Available tools: ..."
```

## T103: Performance Validation

**Goal**: Verify <200ms p95 latency for tool execution

### Test 1: Measure /tools Response Time

```bash
# Install httpstat if not available
# brew install httpstat

# Measure /tools endpoint
for i in {1..100}; do
  curl -o /dev/null -s -w '%{time_total}\n' http://localhost:8001/tools
done | sort -n | awk 'NR==95 {print "P95: " $1*1000 "ms"}'

# Expected: P95 < 100ms
```

### Test 2: Measure /call-tool Response Time

```bash
# Create request file
cat > /tmp/call-tool-request.json << 'EOF'
{
  "tool": "query_callers",
  "arguments": {
    "function_name": "codebase_rag.http.server.create_app",
    "max_depth": 1
  }
}
EOF

# Measure 100 requests
for i in {1..100}; do
  curl -o /dev/null -s -w '%{time_total}\n' \
    -X POST http://localhost:8001/call-tool \
    -H "Content-Type: application/json" \
    -d @/tmp/call-tool-request.json
done | sort -n | awk 'NR==95 {print "P95: " $1*1000 "ms"}'

# Expected: P95 < 200ms for typical codebases
```

**Success criteria**: P95 latency meets SC-011 requirement (<200ms)

**Note**: Performance depends on:
- Codebase size (nodes in Memgraph)
- Query complexity (max_depth, traversal depth)
- Memgraph connection latency
- System resources

## T104: LaunchAgent Auto-Restart Verification

**Goal**: Verify LaunchAgent restarts within 5 seconds on failure

### Prerequisites

```bash
# Install LaunchAgent
cd deployment/launchagents
./install.sh

# Start service
cd /Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag
./services-manager.sh start
```

### Test 1: Kill Process and Verify Restart

```bash
# Get process ID
ps aux | grep "codebase_rag.http" | grep -v grep

# Kill the process
pkill -f "codebase_rag.http"

# Wait 5 seconds
sleep 5

# Check if restarted
./services-manager.sh status

# Verify health endpoint responds
curl http://localhost:8001/health
```

**Success criteria**: Service automatically restarts within 5 seconds, health endpoint accessible

### Test 2: Monitor Restart in Logs

```bash
# Tail logs in one terminal
tail -f deployment/launchagents/logs/code-graph-rag.log

# Kill process in another terminal
pkill -f "codebase_rag.http"

# Expected: Log shows shutdown followed by startup within 5 seconds
```

**Success criteria**: Logs show automatic restart, no manual intervention required

## T105: Concurrent Request Handling

**Goal**: Send 100 parallel requests to /call-tool and verify all succeed

### Test 1: Parallel Requests Test

```bash
# Create test script
cat > /tmp/concurrent-test.sh << 'EOF'
#!/bin/bash
for i in {1..100}; do
  curl -s -X POST http://localhost:8001/call-tool \
    -H "Content-Type: application/json" \
    -d '{
      "tool": "query_callers",
      "arguments": {
        "function_name": "codebase_rag.http.server.create_app",
        "max_depth": 1
      }
    }' &
done
wait
EOF

chmod +x /tmp/concurrent-test.sh

# Run test
/tmp/concurrent-test.sh > /tmp/concurrent-results.txt

# Count successful responses
grep -c '"success": true' /tmp/concurrent-results.txt

# Expected: 100 (all requests succeeded)
```

**Success criteria**: All 100 concurrent requests return success responses

### Test 2: Use Apache Bench

```bash
# Install ab if not available
# brew install apr-util

# Create request body
cat > /tmp/post-data.json << 'EOF'
{
  "tool": "query_callers",
  "arguments": {
    "function_name": "codebase_rag.http.server.create_app",
    "max_depth": 1
  }
}
EOF

# Run 100 concurrent requests
ab -n 100 -c 10 -p /tmp/post-data.json -T application/json \
  http://localhost:8001/call-tool

# Expected:
# - Complete requests: 100
# - Failed requests: 0
# - Non-2xx responses: 0 (assuming all succeed)
```

**Success criteria**: No failed requests, all complete successfully

## T106: Graceful Shutdown Verification

**Goal**: Verify graceful shutdown completes in-flight requests within 5 seconds

### Test 1: Shutdown During Request Processing

```bash
# Start long-running request in background
curl -X POST http://localhost:8001/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "query_call_graph",
    "arguments": {
      "entry_point": "codebase_rag.main",
      "max_depth": 5,
      "max_nodes": 100
    }
  }' &

# Wait 1 second to ensure request is processing
sleep 1

# Send SIGTERM to server
pkill -TERM -f "codebase_rag.http"

# Wait for background job to complete
wait

# Check if response was received
echo "Request completed with exit code: $?"
```

**Success criteria**: In-flight request completes successfully before shutdown

### Test 2: Monitor Shutdown Timing

```bash
# Start server with timestamp logging
uv run python -m codebase_rag.http --log-level info

# In another terminal, start a request and send SIGTERM
curl -X POST http://localhost:8001/call-tool \
  -d '{"tool": "query_callers", "arguments": {"function_name": "test"}}' &
sleep 0.5
pkill -TERM -f "codebase_rag.http"

# Expected log output:
# - "Received signal 15, initiating shutdown..."
# - "Waiting up to 5s for in-flight requests..."
# - "Shutdown complete"
# - Total time from signal to shutdown complete: <5 seconds
```

**Success criteria**: Server waits for in-flight requests and completes shutdown within 5 seconds

### Test 3: Configuration Verification

Verify graceful_shutdown_seconds configuration is applied:

```bash
# Check config
grep graceful_shutdown_seconds config/http-server.yaml

# Expected: 5
```

**Success criteria**: Configuration matches timeout requirement

## Validation Summary

After completing all tests, document results:

### Checklist

- [ ] T100: All quickstart.md examples work
- [ ] T101: OpenAPI examples match server behavior
- [ ] T102: Logging is comprehensive (already verified)
- [ ] T103: P95 latency <200ms
- [ ] T104: LaunchAgent auto-restart <5 seconds
- [ ] T105: 100 concurrent requests succeed
- [ ] T106: Graceful shutdown <5 seconds

### Issues Found

Document any issues discovered during validation:

1. Issue: [description]
   - Test: [which test]
   - Expected: [expected behavior]
   - Actual: [actual behavior]
   - Resolution: [how to fix]

### Performance Metrics

Document measured metrics:

- /tools P95 latency: _____ ms
- /call-tool P95 latency: _____ ms
- Concurrent requests success rate: _____ %
- LaunchAgent restart time: _____ seconds
- Graceful shutdown time: _____ seconds

## Notes

- Validation tasks are designed to be run against a locally running instance
- Some tests require Memgraph to be running and the repository to be indexed
- Performance results may vary based on system resources and codebase size
- All tests should be repeatable and produce consistent results
