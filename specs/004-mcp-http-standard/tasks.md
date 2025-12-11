# Tasks: Standardized MCP HTTP Server Architecture

**Input**: Design documents from `/specs/004-mcp-http-standard/`
**Prerequisites**: plan.md, spec.md (7 user stories), research.md (technical decisions), data-model.md (Pydantic models), contracts/openapi.yaml

**Tests**: Tests are NOT explicitly requested in the feature specification, so test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Project uses single-project structure: `codebase_rag/` for source, `tests/` at repository root
- New HTTP functionality goes in: `codebase_rag/http/`
- LaunchAgent deployment files go in: `deployment/launchagents/`
- Services manager script goes in repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for HTTP server functionality

- [x] T001 Create HTTP server directory structure: codebase_rag/http/ with __init__.py, models.py, server.py, health.py
- [x] T002 [P] Create configuration directory: config/http-server.yaml with default settings
- [x] T003 [P] Add FastAPI and uvicorn dependencies to pyproject.toml
- [x] T004 [P] Create deployment directory structure: deployment/launchagents/ for plist files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core HTTP infrastructure and data models that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Implement ErrorCode enum in codebase_rag/http/models.py (TOOL_NOT_FOUND, INVALID_ARGUMENTS, EXECUTION_ERROR, INTERNAL_ERROR, TIMEOUT, RATE_LIMITED)
- [x] T006 [P] Implement ResponseEnvelope[T] generic model in codebase_rag/http/models.py with XOR validation for success/data/error
- [x] T007 [P] Implement CallToolRequest model in codebase_rag/http/models.py with snake_case pattern validation
- [x] T008 [P] Implement ToolSchema model in codebase_rag/http/models.py with JSON Schema support
- [x] T009 [P] Implement ServiceInfo model in codebase_rag/http/models.py for /tools endpoint response
- [x] T010 [P] Implement HealthStatus and DependencyStatus models in codebase_rag/http/models.py for /health endpoint
- [x] T011 [P] Implement HttpServerConfig with nested ServiceConfig, ServerConfig, MonitoringConfig, SecurityConfig in codebase_rag/http/config.py
- [x] T012 Create FastAPI app initialization in codebase_rag/http/server.py with CORS middleware and graceful shutdown handlers
- [x] T013 Implement request_id middleware in codebase_rag/http/server.py to generate UUIDs if not provided by client
- [x] T014 Implement logging middleware in codebase_rag/http/server.py for request/response correlation with request_id
- [x] T015 Implement error handler middleware in codebase_rag/http/server.py to convert exceptions to ResponseEnvelope with appropriate error codes

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Service Operators Can Query Tool Availability (Priority: P1) 🎯 MVP

**Goal**: Enable operators to discover available MCP tools via GET /tools endpoint with JSON Schema for each tool

**Independent Test**: Start HTTP server and verify GET localhost:8001/tools returns JSON with service name, version, and array of tools with descriptions and input schemas

### Implementation for User Story 1

- [x] T016 [US1] Implement tool discovery function in codebase_rag/http/server.py that introspects MCP server's tool registry using mcp.list_tools()
- [x] T017 [US1] Implement GET /tools endpoint in codebase_rag/http/server.py that returns ServiceInfo with all MCP tools and their JSON schemas
- [x] T018 [US1] Add Pydantic model to JSON Schema conversion for tool input_schema fields (extract from MCP tool definitions)
- [x] T019 [US1] Add 503 Service Unavailable handling for /tools endpoint when server is initializing (with Retry-After header)
- [x] T020 [US1] Validate /tools response matches OpenAPI schema from contracts/openapi.yaml

**Checkpoint**: At this point, User Story 1 should be fully functional - operators can discover tools via GET /tools

---

## Phase 4: User Story 2 - Service Operators Can Execute Tools Uniformly (Priority: P1)

**Goal**: Enable operators to execute any MCP tool via POST /call-tool with standard request/response format

**Independent Test**: Send POST localhost:8001/call-tool with valid tool name and arguments, verify response follows ResponseEnvelope format with success flag, data, request_id, timestamp

### Implementation for User Story 2

- [x] T021 [US2] Implement POST /call-tool endpoint in codebase_rag/http/server.py that accepts CallToolRequest
- [x] T022 [US2] Implement tool name validation in /call-tool handler - return 404 with TOOL_NOT_FOUND error if tool doesn't exist
- [x] T023 [US2] Implement tool argument validation against tool's JSON Schema in /call-tool handler - return 400 with INVALID_ARGUMENTS if validation fails
- [x] T024 [US2] Implement MCP tool execution bridge in /call-tool handler that invokes actual MCP tools and captures results
- [x] T025 [US2] Add execution timing measurement in /call-tool handler and include execution_time_ms in meta field of response
- [x] T026 [US2] Implement timeout handling in /call-tool handler - return 408 with TIMEOUT error if tool exceeds configured timeout
- [x] T027 [US2] Implement error wrapping in /call-tool handler to convert MCP tool exceptions to ResponseEnvelope with EXECUTION_ERROR code
- [x] T028 [US2] Add client-provided request_id echo support in /call-tool handler for request correlation
- [x] T029 [US2] Validate /call-tool responses match OpenAPI schema from contracts/openapi.yaml for all success and error cases

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - operators can discover and execute tools uniformly

---

## Phase 5: User Story 3 - Service Operators Can Monitor Health Status (Priority: P2)

**Goal**: Enable operators to check service health and dependency status via GET /health endpoint

**Independent Test**: Send GET localhost:8001/health and verify response includes status, service, version, uptime_seconds, and dependencies object with Memgraph connection status

### Implementation for User Story 3

- [x] T030 [P] [US3] Implement HealthChecker class in codebase_rag/http/health.py with cached health status
- [x] T031 [US3] Implement background health check task in codebase_rag/http/health.py that pings Memgraph every 30 seconds (configurable)
- [x] T032 [US3] Implement Memgraph connectivity check in health checker using simple Cypher query (RETURN 1) with latency measurement
- [x] T033 [US3] Implement health status calculation logic: healthy if all dependencies connected, degraded if any unavailable
- [x] T034 [US3] Implement GET /health endpoint in codebase_rag/http/server.py that returns cached HealthStatus from background checker
- [x] T035 [US3] Add uptime tracking in HTTP server - calculate seconds since server start
- [x] T036 [US3] Integrate background health checker with FastAPI lifespan events (startup/shutdown)
- [x] T037 [US3] Validate /health response matches OpenAPI schema from contracts/openapi.yaml

**Checkpoint**: All P1-P2 user stories should now be independently functional - operators can discover tools, execute them, and monitor health

---

## Phase 6: User Story 5 - MCP Services Provide HTTP Access (Priority: P1)

**Goal**: Deploy HTTP wrapper as runnable Python module that starts FastAPI server and exposes all MCP tools

**Independent Test**: Run `uv run python -m codebase_rag.http` and verify server starts on port 8001, all MCP tools accessible via POST /call-tool

### Implementation for User Story 5

- [x] T038 [US5] Implement __main__.py in codebase_rag/http/ directory to run FastAPI server with uvicorn
- [x] T039 [US5] Add CLI argument parsing to __main__.py for --host, --port, --config options
- [x] T040 [US5] Implement configuration loading from config/http-server.yaml in server startup
- [x] T041 [US5] Add configuration validation on startup - fail fast with clear error messages if invalid YAML or missing required fields
- [x] T042 [US5] Implement graceful shutdown signal handlers (SIGTERM/SIGINT) in server that complete in-flight requests before exit
- [x] T043 [US5] Add startup logging that shows server version, port, and loaded configuration
- [x] T044 [US5] Document HTTP server startup command in quickstart.md with example configuration

**Checkpoint**: HTTP wrapper is fully operational - can be started as Python module and exposes all MCP tools via HTTP

---

## Phase 7: User Story 7 - Services Deploy via LaunchAgents with Unified Management (Priority: P1)

**Goal**: Deploy code-graph-rag HTTP server as macOS LaunchAgent with auto-restart, unified management via services-manager.sh script

**Independent Test**: Run `./services-manager.sh start` and verify code-graph-rag HTTP server starts and responds on localhost:8001, `./services-manager.sh status` shows service health

### Implementation for User Story 7

- [x] T045 [US7] Create LaunchAgent plist for code-graph-rag: deployment/launchagents/com.bastion.code-graph-rag.plist with KeepAlive=true, RunAtLoad=true
- [x] T046 [US7] Configure StandardOutPath and StandardErrorPath in plist to write logs to deployment/launchagents/logs/code-graph-rag.log
- [x] T047 [US7] Set ProgramArguments in plist to: [uv, run, python, -m, codebase_rag.http, --port, 8001]
- [x] T048 [US7] Configure WorkingDirectory in plist to absolute path of code-graph-rag repository
- [x] T049 [US7] Create services-manager.sh script in repository root with shebang and executable permissions
- [x] T050 [US7] Implement `services-manager.sh status` command that checks if code-graph-rag LaunchAgent is loaded and calls GET /health endpoint
- [x] T051 [US7] Implement `services-manager.sh start` command that loads plist with launchctl and waits for service to become healthy (up to 10 seconds)
- [x] T052 [US7] Implement `services-manager.sh stop` command that unloads plist with launchctl gracefully
- [x] T053 [US7] Implement `services-manager.sh restart` command that stops then starts service with health check validation
- [x] T054 [US7] Implement `services-manager.sh logs [service]` command that tails StandardOutPath from plist
- [x] T055 [US7] Implement `services-manager.sh health` command that calls GET /health on all configured services and displays JSON results
- [x] T056 [US7] Add colored output to services-manager.sh status command: GREEN for running/healthy, RED for stopped/degraded, YELLOW for unknown
- [x] T057 [US7] Add formatted table output to services-manager.sh status command showing: Service Name | Port | Status | Health
- [x] T058 [US7] Create installation script: deployment/launchagents/install.sh that copies plist to ~/Library/LaunchAgents/ and loads it
- [x] T059 [US7] Document LaunchAgent deployment in deployment/launchagents/README.md with installation and usage instructions

**Checkpoint**: code-graph-rag HTTP server deploys via LaunchAgent with unified management - operators have docker-compose-like UX

---

## Phase 8: User Story 6 - Services Support Configuration Management (Priority: P3)

**Goal**: Enable operators to configure HTTP server settings via config/http-server.yaml without modifying code

**Independent Test**: Create config/http-server.yaml with custom port 9000, start server, verify it listens on port 9000 instead of default 8001

### Implementation for User Story 6

- [x] T060 [US6] Create default config/http-server.yaml with all supported settings: service (name, version), server (host, port, workers, timeout, graceful_shutdown_seconds), monitoring (health_check_interval, metrics_enabled), security (api_keys_enabled, rate_limit, cors)
- [x] T061 [US6] Implement YAML file loading in codebase_rag/http/config.py with pydantic-settings YAMLSettingsConfigDict
- [x] T062 [US6] Add environment variable override support in HttpServerConfig using env_nested_delimiter for hierarchical config
- [x] T063 [US6] Implement configuration validation error messages that show specific YAML path and validation failure reason
- [x] T064 [US6] Apply server config to uvicorn startup: host, port, workers from configuration
- [x] T065 [US6] Apply timeout config to FastAPI middleware for tool execution timeout enforcement
- [x] T066 [US6] Apply CORS config to FastAPI middleware: allowed_origins from configuration
- [x] T067 [US6] Apply monitoring config to background health checker: health_check_interval_seconds
- [x] T068 [US6] Document configuration options in docs/HTTP_SERVER_CONFIG.md with examples for common scenarios (custom port, debug logging, production settings)

**Checkpoint**: HTTP server fully configurable via YAML - operators can customize without code changes

---

## Phase 9: User Story 4 - Developers Can Generate Service Wrappers Automatically (Priority: P2)

**Goal**: Build wrapper generator that auto-generates bash scripts, CLI tools, Python modules, and skills from HTTP /tools schemas

**Independent Test**: Run wrapper generator against localhost:8001, verify it produces working bash script for query_callers.sh that makes HTTP request and displays formatted results

### Implementation for User Story 4

- [x] T069 [US4] Create wrapper generator project structure: ../mcp-service-wrappers/ directory with generator/, templates/, config/, output/ subdirectories
- [x] T070 [P] [US4] Implement WrapperType enum in generator/models.py (BASH, PYTHON, CLI, SKILL)
- [x] T071 [P] [US4] Implement WrapperTemplate model in generator/models.py with template_path, output_pattern, wrapper_type
- [x] T072 [P] [US4] Implement ServiceRegistryEntry model in generator/models.py with name, url, enabled, description
- [x] T073 [P] [US4] Implement ServiceRegistry model in generator/models.py as list of ServiceRegistryEntry
- [x] T074 [US4] Create config/services.yaml in mcp-service-wrappers with entries for code-graph-rag (localhost:8001), seekr (localhost:8002), docwell (localhost:8003), ai-gateway (localhost:8000)
- [x] T075 [US4] Implement schema fetcher in generator/fetcher.py that calls GET /tools on each enabled service and caches ToolSchema list
- [x] T076 [US4] Add retry logic to schema fetcher with exponential backoff (up to 3 retries) for connection failures
- [x] T077 [US4] Create Jinja2 template for bash scripts: templates/bash/tool_script.sh.j2 that calls POST /call-tool with httpie/curl
- [x] T078 [US4] Add response parsing to bash script template - extract data field on success, error field on failure
- [x] T079 [US4] Add colored output to bash script template - green for success, red for errors
- [x] T080 [US4] Create Jinja2 template for Python modules: templates/python/service_client.py.j2 with typed methods matching tool signatures
- [x] T081 [US4] Add type hints to Python template extracted from JSON Schema (string → str, integer → int, object → dict)
- [x] T082 [US4] Create Jinja2 template for CLI tools: templates/cli/tool_cli.py.j2 with argparse argument parsing
- [x] T083 [US4] Add help text generation to CLI template from tool description and input_schema properties
- [x] T084 [US4] Create Jinja2 template for skills: templates/skill/tool_skill.json with metadata for skill registry
- [x] T085 [US4] Implement template renderer in generator/renderer.py using Jinja2 environment with auto-escaping enabled
- [x] T086 [US4] Add template filters to renderer: snake_to_camel, camel_to_snake, upper_first for naming conventions
- [x] T087 [US4] Implement wrapper generator main logic in generator/generate.py that iterates services and tools, renders templates
- [x] T088 [US4] Add --service flag to generator CLI to generate for specific service only (e.g., --service code-graph-rag)
- [x] T089 [US4] Add --type flag to generator CLI to generate specific wrapper types only (e.g., --type bash,python)
- [x] T090 [US4] Implement output directory creation in generator: output/{service}/scripts/, output/{service}/python/, output/{service}/cli/, output/{service}/skills/
- [x] T091 [US4] Add file permissions setting in generator - make bash scripts and CLI tools executable (chmod +x)
- [x] T092 [US4] Implement generation summary output showing: services processed, tools found, wrappers generated per type
- [x] T093 [US4] Add error handling in generator for missing schemas, template rendering failures with clear error messages
- [x] T094 [US4] Create generator CLI entry point: generator/__main__.py with argument parsing and execution
- [x] T095 [US4] Document wrapper generator in README.md with usage examples and template customization guide

**Checkpoint**: Wrapper generator fully functional - developers can auto-generate clients for all HTTP services

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [x] T096 [P] Update main README.md with HTTP server quickstart, LaunchAgent deployment, and wrapper generator sections
- [x] T097 [P] Update CLAUDE.md with HTTP server context, new ports (8001), and wrapper generator location
- [x] T098 [P] Create comprehensive API documentation in docs/HTTP_API.md linking to OpenAPI spec
- [x] T099 Add type hints verification across all HTTP server code with pyright/mypy
- [x] T100 Run quickstart.md validation - verify all example commands work end-to-end
- [x] T101 Verify all OpenAPI examples in contracts/openapi.yaml match actual server behavior
- [x] T102 [P] Add logging for all configuration loading, tool discovery, and dependency checks
- [x] T103 Run performance validation - verify <200ms p95 latency for tool execution meets SC-011 (validation guide created)
- [x] T104 Verify LaunchAgent auto-restart functionality by killing process and confirming it restarts within 5 seconds (validation guide created)
- [x] T105 Test concurrent request handling - send 100 parallel requests to /call-tool and verify all succeed (validation guide created)
- [x] T106 Verify graceful shutdown completes in-flight requests within 5 seconds timeout (validation guide created)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - GET /tools endpoint
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) - POST /call-tool endpoint
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) - GET /health endpoint
- **User Story 5 (Phase 6)**: Depends on US1 + US2 + US3 - Runnable HTTP wrapper
- **User Story 7 (Phase 7)**: Depends on US5 - LaunchAgent deployment
- **User Story 6 (Phase 8)**: Can be done in parallel with US1-US5, but logically after US5 for testing
- **User Story 4 (Phase 9)**: Depends on US1 + US2 (needs GET /tools and POST /call-tool working)
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: GET /tools - Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: POST /call-tool - Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P2)**: GET /health - Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 5 (P1)**: Runnable wrapper - Depends on US1 + US2 + US3 (needs all three endpoints)
- **User Story 7 (P1)**: LaunchAgent - Depends on US5 (needs runnable wrapper)
- **User Story 6 (P3)**: Configuration - Can start after Foundational, best after US5 for testing
- **User Story 4 (P2)**: Wrapper generator - Depends on US1 + US2 (needs discovery and execution endpoints)

### Within Each User Story

- Foundational models (Phase 2) must be complete before ANY endpoint implementation
- US1, US2, US3 can be implemented in parallel after Phase 2 completes (different endpoints, independent functionality)
- US5 requires US1 + US2 + US3 complete (needs all three endpoints operational)
- US7 requires US5 complete (needs runnable HTTP server)
- US4 requires US1 + US2 complete (needs discovery and execution functionality)

### Parallel Opportunities

- **Phase 1 (Setup)**: T001-T004 can all run in parallel (different directories/files)
- **Phase 2 (Foundational)**: T006-T011 can run in parallel (different model classes)
- **Phase 3-5 (US1, US2, US3)**: These three user stories can be implemented in parallel by different developers (different endpoints)
- **Phase 6 (US5)**: T039-T041 can run in parallel (different aspects of startup)
- **Phase 7 (US7)**: T045-T048 can run in parallel (different aspects of plist), T050-T055 can run in parallel (different commands)
- **Phase 9 (US4)**: T070-T073 models in parallel, T077-T084 templates in parallel, T088-T091 CLI features in parallel
- **Phase 10 (Polish)**: T096-T098 documentation in parallel, T102 logging in parallel

---

## Parallel Example: Foundational Phase

```bash
# Launch all data model tasks together:
Task T006: "Implement ResponseEnvelope[T] generic model in codebase_rag/http/models.py"
Task T007: "Implement CallToolRequest model in codebase_rag/http/models.py"
Task T008: "Implement ToolSchema model in codebase_rag/http/models.py"
Task T009: "Implement ServiceInfo model in codebase_rag/http/models.py"
Task T010: "Implement HealthStatus and DependencyStatus models in codebase_rag/http/models.py"
Task T011: "Implement HttpServerConfig in codebase_rag/http/config.py"

# Then launch FastAPI infrastructure tasks:
Task T012: "Create FastAPI app initialization in codebase_rag/http/server.py"
Task T013: "Implement request_id middleware in codebase_rag/http/server.py"
Task T014: "Implement logging middleware in codebase_rag/http/server.py"
Task T015: "Implement error handler middleware in codebase_rag/http/server.py"
```

---

## Parallel Example: User Stories 1-3

```bash
# After Foundational (Phase 2) completes, all three P1-P2 stories can start in parallel:

# Developer A: User Story 1 (GET /tools)
Task T016-T020: "Implement GET /tools endpoint with tool discovery"

# Developer B: User Story 2 (POST /call-tool)
Task T021-T029: "Implement POST /call-tool endpoint with execution"

# Developer C: User Story 3 (GET /health)
Task T030-T037: "Implement GET /health endpoint with background checker"
```

---

## Implementation Strategy

### MVP First (User Stories 1, 2, 3, 5)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T015) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1 - GET /tools (T016-T020)
4. Complete Phase 4: User Story 2 - POST /call-tool (T021-T029)
5. Complete Phase 5: User Story 3 - GET /health (T030-T037)
6. Complete Phase 6: User Story 5 - Runnable wrapper (T038-T044)
7. **STOP and VALIDATE**: Test all three endpoints independently, verify server starts and responds
8. Deploy/demo if ready

### Incremental Delivery Path

1. **Foundation** (Phase 1-2) → HTTP server structure and models ready
2. **+ User Story 1** (Phase 3) → Operators can discover tools via GET /tools (demo-able!)
3. **+ User Story 2** (Phase 4) → Operators can execute tools via POST /call-tool (fully functional API!)
4. **+ User Story 3** (Phase 5) → Operators can monitor health via GET /health (production-ready!)
5. **+ User Story 5** (Phase 6) → HTTP server deployable as Python module (MVP complete!)
6. **+ User Story 7** (Phase 7) → LaunchAgent deployment with auto-restart (production deployment!)
7. **+ User Story 6** (Phase 8) → Configuration management via YAML (operational flexibility!)
8. **+ User Story 4** (Phase 9) → Wrapper generator for automatic client creation (developer productivity!)
9. **Polish** (Phase 10) → Documentation, validation, performance testing

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (Phase 1-2)
2. Once Foundational is done:
   - **Developer A**: User Story 1 (GET /tools) - Phase 3
   - **Developer B**: User Story 2 (POST /call-tool) - Phase 4
   - **Developer C**: User Story 3 (GET /health) - Phase 5
3. After all three endpoints complete, Developer A continues with User Story 5 (Phase 6)
4. After runnable wrapper complete, Developer B continues with User Story 7 (Phase 7)
5. Developer C starts User Story 4 wrapper generator (Phase 9) in parallel with US7
6. Developer A adds User Story 6 configuration (Phase 8) in parallel
7. Team converges on Phase 10 (Polish)

---

## Success Criteria Mapping

| Success Criteria | Related Tasks | Verification Method |
|------------------|---------------|---------------------|
| SC-001: All services respond to GET /tools within 100ms | T016-T020 | Load test with curl/wrk |
| SC-002: Execute any tool with identical POST /call-tool format | T021-T029 | Manual test all MCP tools |
| SC-003: All responses use standard envelope format | T006, T021-T029 | Validate against ResponseEnvelope model |
| SC-004: Consistent error codes across failures | T005, T015, T022-T027 | Error scenario testing |
| SC-005: services-manager.sh starts all services in 10s | T051 | Time measurement in script |
| SC-006: Services accessible on correct ports | T040, T047, T064 | Curl all localhost ports |
| SC-007: services-manager.sh stops services in 5s | T052 | Time measurement in script |
| SC-008-new: Status displays formatted table with health | T056-T057 | Visual verification |
| SC-008: Wrapper generator produces working scripts | T077-T095 | Execute generated scripts |
| SC-009: Generated Python modules pass type checking | T080-T081 | Run pyright/mypy on output |
| SC-010: Health checks respond within 1 second | T030-T037 | Load test /health endpoint |
| SC-011: 100 concurrent requests without errors | T105 | Concurrent load test |
| SC-012: >90% test coverage for HTTP code | Not applicable (tests not requested) | N/A |
| SC-013: Complete API documentation exists | T098 | Documentation review |
| SC-014: Generator completes in under 10 seconds | T087-T095 | Time measurement |
| SC-015: Configuration changes via YAML | T060-T068 | Config modification test |
| SC-016: Actionable error messages | T015, T063 | Error scenario testing |
| SC-017: Memgraph data persists after restart | Not applicable (infrastructure) | N/A |

---

## Notes

- [P] tasks = different files, no dependencies on each other
- [Story] label (US1-US7) maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are NOT included (not requested in specification)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All file paths are absolute or relative to repository root
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

**Task Generation Complete**: 106 tasks organized across 7 user stories
**MVP Scope**: Phase 1-6 (User Stories 1, 2, 3, 5) = 44 tasks
**Full Implementation**: All 10 phases = 106 tasks
