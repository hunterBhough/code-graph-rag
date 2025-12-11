# Feature Specification: Standardized MCP HTTP Server Architecture

**Feature Branch**: `004-mcp-http-standard`
**Created**: 2025-12-09
**Status**: Draft
**Input**: User description: "Standardized MCP HTTP Server Architecture: Create a unified HTTP server architecture across all MCP services (ai-gateway, code-graph-rag, seekr, docwell) with consistent POST /call-tool, GET /tools, and GET /health endpoints deployed via macOS LaunchAgents. Implement standard response envelopes with {success, data, error, code, request_id, timestamp, meta} format. Standardize error codes (TOOL_NOT_FOUND, INVALID_ARGUMENTS, EXECUTION_ERROR, etc). Standardize existing ai-gateway HTTP server (port 8000) and build new HTTP wrappers for code-graph-rag (port 8001), seekr (port 8002), and docwell (port 8003) using FastAPI. Deploy all services in ../mcp-http-gateway with LaunchAgent plists for auto-start/restart. Create services-manager.sh script for unified service management (start, stop, status, logs, health). All services must support YAML configuration, graceful shutdown, request ID tracking, structured logging, and dependency health checks. Services connect to native Memgraph at localhost:7687. mcp-service-wrappers will consume HTTP /tools schemas to auto-generate bash scripts, prime commands, skills, CLI tools, and Python modules. Generator uses Jinja2 templates and services.yaml configuration. Success criteria: all four services implement standard spec with LaunchAgents, services-manager.sh provides docker-compose-like UX, wrapper generator creates working wrappers for all tools, >90% test coverage, complete documentation."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Service Operators Can Query Tool Availability (Priority: P1)

**Description**: Service operators and automated systems need a uniform way to discover what tools are available across all MCP services without consulting documentation or source code.

**Why this priority**: This is the foundation for all automation and wrapper generation. Without discoverable tool schemas, operators cannot programmatically interact with services or generate client libraries.

**Independent Test**: Can be fully tested by starting any standardized service and making a GET request to /tools endpoint. Delivers immediate value by enabling service discovery and runtime introspection.

**Acceptance Scenarios**:

1. **Given** services are running via LaunchAgents, **When** operator sends GET localhost:8001/tools, **Then** code-graph-rag returns JSON response containing service name, version, and array of available tools with their descriptions and input schemas
2. **Given** services are running via LaunchAgents, **When** operator sends GET localhost:8002/tools, **Then** seekr returns identical response structure as code-graph-rag (same format, different tools)
3. **Given** services are running via LaunchAgents, **When** operator sends GET localhost:8000/tools, **Then** ai-gateway returns identical response structure as other services
4. **Given** services are running via LaunchAgents, **When** operator sends GET localhost:8003/tools, **Then** docwell returns identical response structure as other services
5. **Given** any standardized service is running, **When** operator parses /tools response, **Then** each tool entry contains name, description, and JSON Schema for input validation

---

### User Story 2 - Service Operators Can Execute Tools Uniformly (Priority: P1)

**Description**: Service operators and client applications need to execute tools across all MCP services using the same request format and receive responses in a predictable structure.

**Why this priority**: This enables operators to write generic client code that works across all services, reducing development time and maintenance burden. Critical for building the wrapper generator.

**Independent Test**: Can be fully tested by calling POST /call-tool on any service with a valid tool name and arguments. Delivers value by enabling immediate tool execution without service-specific clients.

**Acceptance Scenarios**:

1. **Given** code-graph-rag HTTP server is running, **When** operator posts to /call-tool with {tool: "query_callers", arguments: {function_name: "foo"}}, **Then** system returns {success: true, data: {tool results}, request_id: "uuid", timestamp: "ISO-8601"}
2. **Given** any tool execution fails due to invalid arguments, **When** operator reviews error response, **Then** system returns {success: false, error: "descriptive message", code: "INVALID_ARGUMENTS", request_id: "uuid", timestamp: "ISO-8601"}
3. **Given** operator calls a non-existent tool, **When** system processes request, **Then** system returns {success: false, error: "Tool not found: xyz", code: "TOOL_NOT_FOUND"}
4. **Given** a tool takes 150ms to execute, **When** operator reviews response, **Then** response includes meta: {execution_time_ms: 150}
5. **Given** operator provides custom request_id in request, **When** system processes and returns response, **Then** response echoes the same request_id for correlation

---

### User Story 3 - Service Operators Can Monitor Health Status (Priority: P2)

**Description**: Service operators and monitoring systems need a standardized way to check if services are healthy and what their dependencies status is.

**Why this priority**: Essential for production operations and automated health checks, but services can technically run without it. Enables operators to quickly diagnose service availability issues.

**Independent Test**: Can be fully tested by sending GET /health to any service and verifying response structure includes status, uptime, and dependency checks. Delivers value by enabling monitoring and alerting.

**Acceptance Scenarios**:

1. **Given** code-graph-rag HTTP server is running with Memgraph available, **When** operator sends GET /health, **Then** system returns {status: "healthy", service: "code-graph-rag", version: "x.y.z", uptime_seconds: N, dependencies: {memgraph: "connected"}}
2. **Given** seekr HTTP server is running, **When** monitoring system polls GET /health every 30 seconds, **Then** system consistently returns 200 OK with current health status
3. **Given** ai-gateway has a dependency failure, **When** operator checks GET /health, **Then** system returns {status: "degraded", dependencies: {offline_service: "unavailable"}}
4. **Given** any service has been running for 2 hours, **When** operator checks /health, **Then** response shows uptime_seconds: 7200 (accurate runtime tracking)

---

### User Story 4 - Developers Can Generate Service Wrappers Automatically (Priority: P2)

**Description**: Developers working with MCP services need to automatically generate bash scripts, CLI tools, Python modules, and skills from service schemas without manual coding.

**Why this priority**: Dramatically reduces development time and ensures consistency across all service clients. However, services can be used manually via curl/HTTP clients if wrapper generation isn't available yet.

**Independent Test**: Can be fully tested by running wrapper generator against any standardized service and verifying it produces working scripts/modules. Delivers value by eliminating manual client development.

**Acceptance Scenarios**:

1. **Given** wrapper generator is configured with code-graph-rag URL (localhost:8001), **When** developer runs generator, **Then** system fetches /tools schema and generates bash scripts for each tool (query_callers.sh, query_hierarchy.sh, etc.)
2. **Given** generated bash scripts exist, **When** developer executes ./query_callers.sh "function_name", **Then** script makes HTTP request to code-graph-rag and displays formatted results
3. **Given** wrapper generator runs against all three services, **When** developer reviews generated Python modules, **Then** each module contains typed methods matching the service's tools (with type hints from JSON schemas)
4. **Given** wrapper generator completes successfully, **When** developer reviews output directory, **Then** directory contains scripts/, skills/, cli/, and python/ subdirectories for each service

---

### User Story 5 - MCP Services Provide HTTP Access (Priority: P1)

**Description**: Users of MCP services (code-graph-rag, seekr, docwell) need HTTP access to all tools without requiring direct MCP protocol connections.

**Why this priority**: This is a new capability for these services. It's P1 because HTTP wrappers must exist before standardization can be applied. ai-gateway already has HTTP server that just needs standardization.

**Independent Test**: Can be fully tested by starting HTTP wrappers and executing any tool via POST /call-tool. Delivers immediate value by enabling HTTP-based access to MCP tools.

**Acceptance Scenarios**:

1. **Given** code-graph-rag MCP tools are available (query_callers, query_hierarchy, etc.), **When** HTTP wrapper starts on port 8001 in mcp-http-gateway container, **Then** all MCP tools are accessible via POST /call-tool endpoint
2. **Given** seekr MCP tools are available, **When** HTTP wrapper starts on port 8002 in mcp-http-gateway container, **Then** all MCP tools are accessible via POST /call-tool endpoint
3. **Given** docwell MCP tools are available, **When** HTTP wrapper starts on port 8003 in mcp-http-gateway container, **Then** all MCP tools are accessible via POST /call-tool endpoint
4. **Given** HTTP wrapper encounters dependency failure, **When** user tries to execute a tool, **Then** system returns {success: false, error: "Dependency connection failed", code: "EXECUTION_ERROR"}
5. **Given** mcp-http-gateway container receives SIGTERM signal, **When** system shuts down, **Then** all in-flight requests complete before container stops (graceful shutdown)

---

### User Story 6 - Services Support Configuration Management (Priority: P3)

**Description**: Service operators need to configure HTTP server settings (port, host, log level, timeouts) via configuration files without modifying code.

**Why this priority**: Improves operational flexibility but services can function with default settings. Nice-to-have for production deployments.

**Independent Test**: Can be fully tested by creating config/http-server.yaml, starting service, and verifying it uses configured settings. Delivers value by enabling environment-specific customization.

**Acceptance Scenarios**:

1. **Given** code-graph-rag has config/http-server.yaml with port: 8001, **When** operator starts HTTP server, **Then** server listens on port 8001
2. **Given** configuration file specifies log_level: "debug", **When** server processes requests, **Then** system outputs debug-level logs
3. **Given** operator updates config file while server is running, **When** server receives SIGHUP signal, **Then** system reloads configuration without dropping connections
4. **Given** configuration file contains invalid YAML syntax, **When** operator attempts to start server, **Then** system displays clear error message and refuses to start

---

### User Story 7 - Services Deploy via LaunchAgents with Unified Management (Priority: P1)

**Description**: Service operators need to deploy all four HTTP services as macOS LaunchAgents with automatic start/restart, unified management via services-manager.sh script, and docker-compose-like UX for service orchestration.

**Why this priority**: LaunchAgent deployment is P1 because it provides native macOS integration, auto-restart on failure, superior filesystem performance (10x faster than Docker on Mac), simple networking (all localhost), and eliminates Docker complexity. This is the optimal deployment model for Mac development.

**Independent Test**: Can be fully tested by running `./services-manager.sh start` and verifying all four services are accessible on their respective ports. Delivers value by enabling production-ready deployment with minimal configuration and native performance.

**Acceptance Scenarios**:

1. **Given** LaunchAgent plists are installed in ~/Library/LaunchAgents/, **When** operator runs `./services-manager.sh start`, **Then** all four services start (ai-gateway:8000, code-graph-rag:8001, seekr:8002, docwell:8003)
2. **Given** services are running, **When** operator runs `./services-manager.sh status`, **Then** system displays service status table with ports, names, and health check results
3. **Given** services are running, **When** operator sends requests to any of the four ports, **Then** requests are processed and responses returned with <100ms latency
4. **Given** operator runs `./services-manager.sh stop`, **When** services shut down, **Then** all services complete gracefully within 5 seconds
5. **Given** operator runs `./services-manager.sh restart`, **When** services restart, **Then** all services stop gracefully and restart successfully within 10 seconds
6. **Given** a service crashes, **When** LaunchAgent detects failure, **Then** service automatically restarts within 5 seconds (KeepAlive functionality)
7. **Given** operator runs `./services-manager.sh logs docwell`, **When** logs are tailed, **Then** system displays real-time logs from docwell service

---

### Edge Cases

- **What happens when a tool execution times out?** System returns {success: false, error: "Tool execution exceeded timeout", code: "TIMEOUT"} with request_id for tracking
- **How does system handle malformed JSON in POST /call-tool?** System returns 400 Bad Request with {success: false, error: "Invalid JSON", code: "INVALID_REQUEST"}
- **What if /tools endpoint is called when service is initializing?** System returns 503 Service Unavailable with Retry-After header until initialization completes
- **How does system behave under concurrent load (100+ simultaneous requests)?** System queues requests and processes them in order, returning 503 with Retry-After if queue is full
- **What happens if dependency health check times out?** System marks dependency as "unknown" in /health response and logs timeout error
- **How are circular references in tool schemas handled?** System uses JSON Schema $ref pointers to avoid infinite recursion in /tools response
- **What if wrapper generator loses connection mid-generation?** Generator retries failed requests up to 3 times before failing with partial output warning
- **How does system handle Unicode in tool arguments and responses?** System properly encodes/decodes UTF-8 in all requests and responses

## Requirements *(mandatory)*

### Functional Requirements

#### HTTP Server Standards (All Services)

- **FR-001**: All HTTP servers MUST expose POST /call-tool endpoint that accepts {tool: string, arguments: object, request_id?: string} and returns standard response envelope
- **FR-002**: All HTTP servers MUST expose GET /tools endpoint that returns {service: string, version: string, tools: [{name, description, input_schema}]}
- **FR-003**: All HTTP servers MUST expose GET /health endpoint that returns {status, service, version, uptime_seconds, dependencies, timestamp}
- **FR-004**: All responses MUST use standard envelope format: {success: boolean, data?: object, error?: string, code?: string, request_id: string, timestamp: string, meta?: object}
- **FR-005**: System MUST support standard error codes: TOOL_NOT_FOUND, INVALID_ARGUMENTS, EXECUTION_ERROR, INTERNAL_ERROR, TIMEOUT, RATE_LIMITED
- **FR-006**: All HTTP servers MUST assign unique UUIDs to requests if client doesn't provide request_id
- **FR-007**: All responses MUST include ISO 8601 timestamps
- **FR-008**: All services MUST log requests and responses with request_id for correlation
- **FR-009**: System MUST return appropriate HTTP status codes (200 OK for success, 400 for invalid requests, 404 for tool not found, 500 for server errors, 503 for unavailable)

#### MCP HTTP Wrappers (New Implementation)

- **FR-010**: code-graph-rag MUST create new HTTP wrapper that bridges MCP tools to HTTP endpoints
- **FR-011**: code-graph-rag HTTP wrapper MUST listen on port 8001 within mcp-http-gateway container
- **FR-012**: code-graph-rag wrapper MUST expose all existing MCP tools (query_callers, query_hierarchy, query_dependencies, etc.) via POST /call-tool
- **FR-013**: code-graph-rag wrapper MUST check Memgraph connectivity and report status in GET /health dependencies section
- **FR-014**: seekr MUST create new HTTP wrapper that bridges MCP tools to HTTP endpoints
- **FR-015**: seekr HTTP wrapper MUST listen on port 8002 within mcp-http-gateway container
- **FR-016**: docwell MUST create new HTTP wrapper that bridges MCP tools to HTTP endpoints
- **FR-017**: docwell HTTP wrapper MUST listen on port 8003 within mcp-http-gateway container
- **FR-018**: All HTTP wrappers MUST handle graceful shutdown on SIGTERM/SIGINT signals, completing in-flight requests before exit
- **FR-019**: All HTTP wrappers MUST support CORS for cross-origin requests from localhost origins

#### AI-Gateway HTTP Server (Standardization)

- **FR-020**: ai-gateway HTTP server MUST be updated to use standard response envelope format for all endpoints
- **FR-021**: ai-gateway MUST implement standard /call-tool endpoint alongside existing domain-specific endpoints
- **FR-022**: ai-gateway MUST implement standard /tools endpoint listing all available tools (generate, list_models, get_usage, etc.)
- **FR-023**: ai-gateway MUST implement standard /health endpoint with dependency status
- **FR-024**: ai-gateway MUST replace ad-hoc error responses with standard error codes
- **FR-025**: ai-gateway MUST keep port 8000 (no change from current default)
- **FR-026**: ai-gateway MUST be compatible with mcp-http-gateway container orchestration

#### LaunchAgent Deployment

- **FR-027**: System MUST provide LaunchAgent plist files for all four services (com.bastion.ai-gateway.plist, com.bastion.code-graph-rag.plist, com.bastion.seekr.plist, com.bastion.docwell.plist)
- **FR-028**: Each LaunchAgent plist MUST specify KeepAlive=true for automatic restart on failure
- **FR-029**: Each LaunchAgent plist MUST specify RunAtLoad=true for automatic start on system boot
- **FR-030**: Each LaunchAgent plist MUST configure StandardOutPath and StandardErrorPath for log collection
- **FR-031**: System MUST provide services-manager.sh script for unified service management
- **FR-032**: services-manager.sh MUST support commands: status, start, stop, restart, logs, health
- **FR-033**: services-manager.sh status command MUST display formatted table with service name, port, and health status
- **FR-034**: services-manager.sh MUST use colored output (GREEN for running, RED for down) for better UX
- **FR-035**: System MUST provide installation script that copies plists to ~/Library/LaunchAgents/ and loads them via launchctl
- **FR-036**: All services MUST start successfully within 10 seconds of running services-manager.sh start
- **FR-037**: All services MUST stop gracefully within 5 seconds of running services-manager.sh stop

#### Configuration Management

- **FR-038**: All services MUST support configuration via config/http-server.yaml file
- **FR-039**: Configuration MUST include: service.name, service.port, service.host, monitoring.metrics_enabled, monitoring.health_check_interval, security.api_keys_enabled, security.rate_limit
- **FR-040**: System MUST validate configuration on startup and fail fast with clear error messages if invalid

#### Wrapper Generator (New Implementation)

- **FR-041**: System MUST create wrapper generator in ../mcp-service-wrappers directory
- **FR-042**: Generator MUST read services from config/services.yaml containing: [{name, url, enabled}]
- **FR-043**: Generator MUST fetch /tools schema from each enabled service
- **FR-044**: Generator MUST create bash scripts for each tool that call POST /call-tool and format output
- **FR-045**: Generator MUST create Python modules with typed methods matching tool signatures
- **FR-046**: Generator MUST create CLI tools with argument parsing and help text
- **FR-047**: Generator MUST create skill definitions with tool metadata
- **FR-048**: Generated wrappers MUST handle success/error responses appropriately
- **FR-049**: Generator MUST use templates (Jinja2 format) for code generation
- **FR-050**: System MUST support --service flag to generate for specific service only
- **FR-051**: System MUST support --type flag to generate only specific wrapper types (scripts, python, cli, skills)

### Key Entities

- **ServiceConfiguration**: Represents HTTP server configuration for a single MCP service, including name, port, host, monitoring settings, and security options
- **ToolSchema**: Represents metadata about an available tool, including name, description, and JSON Schema for input validation
- **ResponseEnvelope**: Standard response structure containing success flag, data/error, request_id, timestamp, and optional metadata
- **ErrorCode**: Enumeration of standardized error conditions across all services
- **WrapperTemplate**: Code generation template (Jinja2) for producing service client wrappers
- **ServiceRegistry**: Collection of service configurations used by wrapper generator to discover and interact with services

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four services (ai-gateway, code-graph-rag, seekr, docwell) respond to GET /tools with valid JSON schema within 100ms
- **SC-002**: Operator can execute any tool on any service using identical POST /call-tool request format
- **SC-003**: All tool executions return responses in standard envelope format with success flag, request_id, and timestamp
- **SC-004**: All services return consistent error codes (TOOL_NOT_FOUND, INVALID_ARGUMENTS, etc.) for equivalent failure scenarios
- **SC-005**: `./services-manager.sh start` starts all four services successfully within 10 seconds
- **SC-006**: All services accessible on correct ports (8000, 8001, 8002, 8003) via localhost
- **SC-007**: `./services-manager.sh stop` gracefully shuts down all services within 5 seconds
- **SC-008-new**: services-manager.sh status displays formatted table with service health (GREEN/RED indicators)
- **SC-008**: Wrapper generator successfully produces working bash scripts for 100% of tools across all four services
- **SC-009**: Generated Python modules pass type checking and execute tools correctly
- **SC-010**: Health checks accurately reflect dependency status (responding within 1 second)
- **SC-011**: Services handle 100 concurrent requests without errors or degraded response times beyond 2x baseline
- **SC-012**: Test coverage exceeds 90% for all new HTTP wrapper code and wrapper generator
- **SC-013**: Complete API documentation exists for all endpoints, request/response formats, and error codes
- **SC-014**: Wrapper generator completes full generation for all four services in under 10 seconds
- **SC-015**: Configuration changes take effect without requiring code modifications (via YAML files)
- **SC-016**: All error responses include actionable error messages that help operators diagnose issues
- **SC-017**: Container restart does not affect memgraph data persistence (volumes properly configured)

## Assumptions

1. **MCP Infrastructure**: Three MCP services (code-graph-rag, seekr, docwell) have existing MCP tool implementations that can be wrapped by HTTP servers; ai-gateway already has HTTP server
2. **Unified Technology Stack**: All services will use Python + FastAPI for HTTP layer (simplifies Docker deployment and standardization)
3. **Port Availability**: Ports 8000-8003 are available on target deployment hosts
4. **Docker Available**: Target hosts have Docker and docker-compose installed
5. **Configuration Format**: YAML is acceptable configuration format for all services
6. **Template Engine**: Jinja2 is appropriate for wrapper generation (widely used, well-documented)
7. **Process Management**: Supervisor is acceptable for managing multiple services within single container
8. **Authentication**: API key authentication is optional (FR-036 security.api_keys_enabled defaults to false)
9. **Rate Limiting**: Rate limits are configurable per service but default to reasonable values (1000 req/min suggested)
10. **Logging Format**: Structured JSON logging is standard across all services
11. **CORS Policy**: Localhost origins are safe to allow by default; production deployments may tighten restrictions
12. **Shared Database**: All services can share single Memgraph instance via internal Docker network

## Dependencies

- **Existing MCP Servers**: Three services (code-graph-rag, seekr, docwell) have working MCP server implementations with tools
- **Existing HTTP Server**: ai-gateway has existing HTTP server that needs standardization
- **Docker Infrastructure**: Docker and docker-compose available on deployment hosts
- **Network Connectivity**: Docker can create internal networks and expose ports to host
- **Configuration Files**: Services can read YAML configuration from config/ directory
- **Python Environment**: Container includes Python 3.12+ environment with FastAPI, mcp, pymgclient
- **Memgraph Database**: Memgraph container running and accessible via Docker network
- **Volume Persistence**: Docker volumes configured for memgraph data persistence
- **File System Access**: Wrapper generator needs write access to ../mcp-service-wrappers output directories

## Scope Boundaries

### In Scope

- Standardizing HTTP API interfaces across four services (ai-gateway, code-graph-rag, seekr, docwell)
- Creating new HTTP wrappers for three MCP services (code-graph-rag, seekr, docwell)
- Standardizing existing HTTP server (ai-gateway) to match standard
- Building Docker container (mcp-http-gateway) that hosts all four services
- Creating docker-compose configuration for container orchestration
- Building wrapper generator for automatic client creation
- Configuration management via YAML files
- Health checks and monitoring endpoints
- Error handling and standardization
- Graceful shutdown handling
- Request/response logging
- Process management via supervisor within container
- Docker networking configuration
- Volume configuration for memgraph data persistence
- Documentation for all HTTP APIs and Docker deployment

### Out of Scope

- Authentication implementation (optional feature, not required for MVP)
- Rate limiting implementation (configurable but not enforced in MVP)
- Metrics/observability beyond basic health checks
- API versioning strategy
- WebSocket or SSE support
- Batch request processing
- Caching layers
- Load balancing across multiple container instances
- Kubernetes/orchestration beyond docker-compose
- CI/CD pipeline integration
- Performance optimization beyond meeting success criteria
- Backward compatibility with existing non-standard clients (breaking change acceptable)
- Individual per-service containers (all services run in single mcp-http-gateway container)
