# HTTP Server Configuration Guide

This guide documents all configuration options for the code-graph-rag HTTP server.

## Table of Contents

- [Overview](#overview)
- [Configuration File Structure](#configuration-file-structure)
- [Configuration Sections](#configuration-sections)
  - [Service Configuration](#service-configuration)
  - [Server Configuration](#server-configuration)
  - [Monitoring Configuration](#monitoring-configuration)
  - [Security Configuration](#security-configuration)
  - [Dependencies Configuration](#dependencies-configuration)
- [Environment Variable Overrides](#environment-variable-overrides)
- [Command-Line Arguments](#command-line-arguments)
- [Common Configuration Scenarios](#common-configuration-scenarios)
- [Validation and Error Messages](#validation-and-error-messages)

## Overview

The HTTP server uses a YAML configuration file located at `config/http-server.yaml` by default. Configuration values can be overridden using:

1. **Environment variables** (highest precedence)
2. **Command-line arguments** (override config file)
3. **YAML configuration file** (default values)

The configuration system is built on `pydantic-settings` and provides:
- Type validation with clear error messages
- Environment variable overrides with nested delimiter support
- Default values for all optional settings
- Comprehensive validation on startup (fail-fast approach)

## Configuration File Structure

Default location: `config/http-server.yaml`

```yaml
service:
  name: "code-graph-rag"
  port: 8001
  host: "127.0.0.1"

server:
  workers: 1
  timeout: 30
  graceful_shutdown_seconds: 5

monitoring:
  metrics_enabled: false
  health_check_interval: 30

security:
  api_keys_enabled: false
  rate_limit: 1000
  cors:
    enabled: true
    allowed_origins:
      - "http://localhost:*"
      - "http://127.0.0.1:*"

dependencies:
  memgraph:
    host: "localhost"
    port: 7687
    timeout: 1000
```

## Configuration Sections

### Service Configuration

Defines service identity and network binding.

| Field | Type | Required | Default | Description | Validation |
|-------|------|----------|---------|-------------|------------|
| `name` | string | Yes | - | Service identifier | Must start with lowercase letter, contain only lowercase letters, digits, and hyphens |
| `port` | integer | Yes | - | HTTP port to listen on | Must be between 1024 and 65535 |
| `host` | string | No | `"127.0.0.1"` | IP address to bind to | Valid IP address or hostname |

**Examples:**

```yaml
# Development (localhost only)
service:
  name: "code-graph-rag"
  port: 8001
  host: "127.0.0.1"

# Production (all interfaces)
service:
  name: "code-graph-rag"
  port: 8001
  host: "0.0.0.0"

# Custom service for testing
service:
  name: "code-graph-rag-dev"
  port: 9000
  host: "127.0.0.1"
```

### Server Configuration

Controls server runtime behavior and resource management.

| Field | Type | Required | Default | Description | Validation |
|-------|------|----------|---------|-------------|------------|
| `workers` | integer | No | `1` | Number of worker processes | Must be >= 1 |
| `timeout` | integer | No | `30` | Request timeout in seconds | Must be between 1 and 300 |
| `graceful_shutdown_seconds` | integer | No | `5` | Time to wait for in-flight requests during shutdown | Must be between 1 and 60 |

**Examples:**

```yaml
# Development (single worker, fast timeout)
server:
  workers: 1
  timeout: 30
  graceful_shutdown_seconds: 5

# Production (multiple workers, longer timeout)
server:
  workers: 4
  timeout: 60
  graceful_shutdown_seconds: 10

# Heavy workloads (extended timeout)
server:
  workers: 2
  timeout: 120
  graceful_shutdown_seconds: 15
```

**Important Notes:**

- **Workers**: Multiple workers improve throughput but increase memory usage. Start with 1 and increase based on load testing.
- **Timeout**: Controls how long tool executions can run. Graph queries may need longer timeouts.
- **Graceful Shutdown**: Ensures in-flight requests complete before server stops. Important for data consistency.

### Monitoring Configuration

Controls health checks and metrics collection.

| Field | Type | Required | Default | Description | Validation |
|-------|------|----------|---------|-------------|------------|
| `metrics_enabled` | boolean | No | `false` | Enable Prometheus-style metrics endpoint | - |
| `health_check_interval` | integer | No | `30` | Seconds between background dependency health checks | Must be >= 10 |

**Examples:**

```yaml
# Development (no metrics, standard health checks)
monitoring:
  metrics_enabled: false
  health_check_interval: 30

# Production (with metrics, frequent health checks)
monitoring:
  metrics_enabled: true
  health_check_interval: 10

# Resource-constrained (less frequent checks)
monitoring:
  metrics_enabled: false
  health_check_interval: 60
```

**Important Notes:**

- **Metrics**: When enabled, exposes `/metrics` endpoint with Prometheus-compatible metrics.
- **Health Check Interval**: Affects how quickly dependency failures are detected. Lower values increase database load.

### Security Configuration

Controls authentication, rate limiting, and CORS policies.

| Field | Type | Required | Default | Description | Validation |
|-------|------|----------|---------|-------------|------------|
| `api_keys_enabled` | boolean | No | `false` | Require API key authentication | - |
| `rate_limit` | integer | No | `1000` | Max requests per minute per client | Must be >= 10 |
| `cors.enabled` | boolean | No | `true` | Enable CORS middleware | - |
| `cors.allowed_origins` | list[string] | No | See below | List of allowed origin patterns | - |

**Default CORS Origins:**
```yaml
cors:
  allowed_origins:
    - "http://localhost:*"
    - "http://127.0.0.1:*"
```

**Examples:**

```yaml
# Development (permissive CORS, no auth)
security:
  api_keys_enabled: false
  rate_limit: 1000
  cors:
    enabled: true
    allowed_origins:
      - "http://localhost:*"
      - "http://127.0.0.1:*"

# Production (restricted CORS, API keys)
security:
  api_keys_enabled: true
  rate_limit: 100
  cors:
    enabled: true
    allowed_origins:
      - "https://myapp.com"
      - "https://app.mycompany.com"

# Internal service (CORS disabled)
security:
  api_keys_enabled: false
  rate_limit: 5000
  cors:
    enabled: false
```

**Important Notes:**

- **API Keys**: When enabled, all requests must include `X-API-Key` header. Configure keys separately.
- **Rate Limit**: Applied per client IP address. Prevents abuse and ensures fair resource allocation.
- **CORS Origins**: Use wildcards (`*`) for port matching. Be restrictive in production.

### Dependencies Configuration

Configures connections to external services.

| Field | Type | Required | Default | Description | Validation |
|-------|------|----------|---------|-------------|------------|
| `memgraph.host` | string | No | `"localhost"` | Memgraph database host | Valid hostname or IP |
| `memgraph.port` | integer | No | `7687` | Memgraph database port | Must be between 1 and 65535 |
| `memgraph.timeout` | integer | No | `1000` | Connection timeout in milliseconds | Must be >= 100 |

**Examples:**

```yaml
# Local development
dependencies:
  memgraph:
    host: "localhost"
    port: 7687
    timeout: 1000

# Docker Compose (service name)
dependencies:
  memgraph:
    host: "memgraph"
    port: 7687
    timeout: 2000

# Remote database
dependencies:
  memgraph:
    host: "db.mycompany.com"
    port: 7687
    timeout: 5000
```

**Important Notes:**

- **Host**: Use Docker service names in containerized environments, not `localhost`.
- **Timeout**: Health checks fail if connection takes longer than this value. Increase for remote databases.

## Environment Variable Overrides

All configuration values can be overridden using environment variables with the pattern:

```
HTTP_SERVER__<SECTION>__<KEY>=value
```

**Examples:**

```bash
# Override service port
export HTTP_SERVER__SERVICE__PORT=8002

# Override server timeout
export HTTP_SERVER__SERVER__TIMEOUT=60

# Override monitoring interval
export HTTP_SERVER__MONITORING__HEALTH_CHECK_INTERVAL=60

# Override Memgraph host
export HTTP_SERVER__DEPENDENCIES__MEMGRAPH__HOST=memgraph.local

# Override CORS enabled flag
export HTTP_SERVER__SECURITY__CORS__ENABLED=false
```

**Nested Configuration:**

For nested structures like `security.cors.enabled`, use double underscores:

```bash
export HTTP_SERVER__SECURITY__CORS__ENABLED=true
export HTTP_SERVER__SECURITY__CORS__ALLOWED_ORIGINS='["http://localhost:*"]'
```

**Case Sensitivity:**

Environment variable matching is case-insensitive, so these are equivalent:

```bash
export HTTP_SERVER__SERVICE__PORT=8002
export http_server__service__port=8002
export Http_Server__Service__Port=8002
```

## Command-Line Arguments

The HTTP server accepts command-line arguments that override both YAML config and environment variables:

```bash
# Basic usage
uv run python -m codebase_rag.http

# Override host and port
uv run python -m codebase_rag.http --host 0.0.0.0 --port 9000

# Use custom config file
uv run python -m codebase_rag.http --config /path/to/custom-config.yaml

# Combine config file with overrides
uv run python -m codebase_rag.http --config custom.yaml --port 8888

# Enable development mode with auto-reload
uv run python -m codebase_rag.http --reload --log-level debug
```

**Available Arguments:**

| Argument | Type | Description | Default |
|----------|------|-------------|---------|
| `--host` | string | Host address to bind to | From config file |
| `--port` | integer | Port to listen on | From config file |
| `--config` | string | Path to YAML configuration file | `config/http-server.yaml` |
| `--reload` | flag | Enable auto-reload for development | `false` |
| `--log-level` | string | Logging level (debug/info/warning/error/critical) | `info` |

## Common Configuration Scenarios

### Scenario 1: Development Environment

**Goal:** Run locally with debug logging and auto-reload.

```yaml
# config/http-server.yaml
service:
  name: "code-graph-rag-dev"
  port: 8001
  host: "127.0.0.1"

server:
  workers: 1
  timeout: 30
  graceful_shutdown_seconds: 5

monitoring:
  metrics_enabled: false
  health_check_interval: 30

security:
  api_keys_enabled: false
  rate_limit: 1000
  cors:
    enabled: true
    allowed_origins:
      - "http://localhost:*"
      - "http://127.0.0.1:*"

dependencies:
  memgraph:
    host: "localhost"
    port: 7687
    timeout: 1000
```

**Start Command:**

```bash
uv run python -m codebase_rag.http --reload --log-level debug
```

### Scenario 2: Production Deployment

**Goal:** Run in production with multiple workers, metrics, and security.

```yaml
# config/http-server.yaml
service:
  name: "code-graph-rag"
  port: 8001
  host: "0.0.0.0"  # Bind to all interfaces

server:
  workers: 4
  timeout: 60
  graceful_shutdown_seconds: 10

monitoring:
  metrics_enabled: true
  health_check_interval: 10

security:
  api_keys_enabled: true
  rate_limit: 100
  cors:
    enabled: true
    allowed_origins:
      - "https://myapp.com"
      - "https://app.mycompany.com"

dependencies:
  memgraph:
    host: "memgraph"  # Docker service name
    port: 7687
    timeout: 2000
```

**Start Command:**

```bash
uv run python -m codebase_rag.http --log-level info
```

### Scenario 3: Docker Compose Deployment

**Goal:** Run in Docker with environment variable overrides.

```yaml
# config/http-server.yaml (minimal, use env vars for deployment-specific values)
service:
  name: "code-graph-rag"
  port: 8001
  host: "0.0.0.0"

server:
  workers: 2
  timeout: 60
  graceful_shutdown_seconds: 10

monitoring:
  metrics_enabled: true
  health_check_interval: 30

security:
  api_keys_enabled: false
  rate_limit: 500
  cors:
    enabled: true

dependencies:
  memgraph:
    host: "memgraph"
    port: 7687
```

**docker-compose.yml:**

```yaml
services:
  code-graph-rag:
    image: code-graph-rag:latest
    ports:
      - "8001:8001"
    environment:
      HTTP_SERVER__SERVICE__HOST: "0.0.0.0"
      HTTP_SERVER__DEPENDENCIES__MEMGRAPH__HOST: "memgraph"
      HTTP_SERVER__MONITORING__HEALTH_CHECK_INTERVAL: "15"
    depends_on:
      - memgraph

  memgraph:
    image: memgraph/memgraph:latest
    ports:
      - "7687:7687"
```

### Scenario 4: Testing with Custom Port

**Goal:** Run on different port for testing without modifying config file.

```bash
# Start on port 9000
uv run python -m codebase_rag.http --port 9000

# Or use environment variable
HTTP_SERVER__SERVICE__PORT=9000 uv run python -m codebase_rag.http
```

### Scenario 5: High-Throughput Graph Queries

**Goal:** Optimize for heavy graph query workloads.

```yaml
service:
  name: "code-graph-rag"
  port: 8001
  host: "0.0.0.0"

server:
  workers: 8  # More workers for parallel processing
  timeout: 120  # Extended timeout for complex queries
  graceful_shutdown_seconds: 15

monitoring:
  metrics_enabled: true
  health_check_interval: 30

security:
  api_keys_enabled: false
  rate_limit: 500  # Lower rate limit to prevent overload
  cors:
    enabled: true

dependencies:
  memgraph:
    host: "memgraph"
    port: 7687
    timeout: 5000  # Longer timeout for complex queries
```

## Validation and Error Messages

The configuration system provides detailed error messages when validation fails.

### Example: Missing Required Field

**Config:**
```yaml
service:
  # Missing 'port' field
  name: "code-graph-rag"
  host: "127.0.0.1"
```

**Error Message:**
```
Configuration validation failed for: config/http-server.yaml

Validation errors:
  - Field: config.service.port
    Error: Field required
    Type: missing
    Environment override: HTTP_SERVER__SERVICE__PORT

Please fix the configuration file or set environment variables to override.
```

**Solution:**
```bash
# Option 1: Fix YAML file
echo "  port: 8001" >> config/http-server.yaml

# Option 2: Use environment variable
export HTTP_SERVER__SERVICE__PORT=8001
```

### Example: Invalid Port Number

**Config:**
```yaml
service:
  name: "code-graph-rag"
  port: 100  # Port must be >= 1024
  host: "127.0.0.1"
```

**Error Message:**
```
Configuration validation failed for: config/http-server.yaml

Validation errors:
  - Field: config.service.port
    Error: Input should be greater than or equal to 1024
    Type: greater_than_equal
    Environment override: HTTP_SERVER__SERVICE__PORT

Please fix the configuration file or set environment variables to override.
```

### Example: Invalid Service Name

**Config:**
```yaml
service:
  name: "CodeGraphRAG"  # Must be lowercase with hyphens only
  port: 8001
  host: "127.0.0.1"
```

**Error Message:**
```
Configuration validation failed for: config/http-server.yaml

Validation errors:
  - Field: config.service.name
    Error: Service name must start with lowercase letter and contain only lowercase letters, digits, and hyphens
    Type: value_error
    Environment override: HTTP_SERVER__SERVICE__NAME

Please fix the configuration file or set environment variables to override.
```

### Example: Invalid YAML Syntax

**Config:**
```yaml
service:
  name: "code-graph-rag"
  port: 8001
  host: "127.0.0.1"
server:
workers: 1  # Indentation error
```

**Error Message:**
```
Invalid YAML syntax in configuration file: config/http-server.yaml
YAML parsing error: mapping values are not allowed here
  in "config/http-server.yaml", line 7, column 9
Please check the YAML syntax at the location indicated above.
```

### Example: File Not Found

**Error Message:**
```
Configuration file not found: config/http-server.yaml
Expected location: /Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag/config/http-server.yaml
Please create the configuration file or specify a different path.
```

**Solution:**
```bash
# Create from example
cp config/http-server.yaml.example config/http-server.yaml

# Or specify different location
uv run python -m codebase_rag.http --config /path/to/config.yaml
```

## Configuration Precedence

When the same setting is defined in multiple places, the precedence order is:

1. **Command-line arguments** (highest precedence)
2. **Environment variables**
3. **YAML configuration file**
4. **Default values** (lowest precedence)

**Example:**

```yaml
# config/http-server.yaml
service:
  port: 8001
```

```bash
# Environment variable
export HTTP_SERVER__SERVICE__PORT=8002

# Command-line argument
uv run python -m codebase_rag.http --port 8003
```

**Result:** Server starts on port **8003** (CLI argument wins).

## Best Practices

1. **Use YAML for defaults**: Store common configuration in `config/http-server.yaml`.
2. **Use environment variables for deployment**: Override per-environment settings (host, database).
3. **Use CLI arguments for testing**: Quick overrides during development.
4. **Validate early**: Run with `--config` flag to validate configuration before deployment.
5. **Version control**: Commit `config/http-server.yaml.example`, not production configs.
6. **Document custom values**: Add comments in YAML explaining non-standard settings.
7. **Monitor logs**: Watch startup logs to confirm loaded configuration.

## Troubleshooting

### Server Won't Start

1. **Check configuration file exists:**
   ```bash
   ls -la config/http-server.yaml
   ```

2. **Validate YAML syntax:**
   ```bash
   python -c "import yaml; yaml.safe_load(open('config/http-server.yaml'))"
   ```

3. **Check port availability:**
   ```bash
   lsof -i :8001
   ```

4. **Review startup logs:**
   ```bash
   uv run python -m codebase_rag.http --log-level debug
   ```

### Configuration Not Applied

1. **Check precedence order** (CLI > ENV > YAML > defaults)
2. **Verify environment variable names** (use double underscores)
3. **Review startup logs** for "Configuration loaded" section
4. **Check for typos** in YAML field names

### Health Checks Failing

1. **Verify Memgraph is running:**
   ```bash
   docker ps | grep memgraph
   ```

2. **Check Memgraph connectivity:**
   ```bash
   nc -zv localhost 7687
   ```

3. **Review health check interval:**
   ```yaml
   monitoring:
     health_check_interval: 10  # Faster detection
   ```

4. **Check health endpoint:**
   ```bash
   curl http://localhost:8001/health
   ```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Uvicorn Configuration](https://www.uvicorn.org/settings/)
- [YAML Syntax Guide](https://yaml.org/spec/1.2/spec.html)
- [Memgraph Documentation](https://memgraph.com/docs)

## Support

For configuration issues or questions:
1. Check this documentation
2. Review example configurations in `config/http-server.yaml.example`
3. Enable debug logging: `--log-level debug`
4. Check GitHub issues for similar problems
5. Open a new issue with configuration details and error messages
