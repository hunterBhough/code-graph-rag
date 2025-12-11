# Implementation Plan: Standardized MCP HTTP Server Architecture

**Branch**: `004-mcp-http-standard` | **Date**: 2025-12-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-mcp-http-standard/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a unified HTTP server architecture across all MCP services (ai-gateway, code-graph-rag, seekr, docwell) with standardized endpoints (POST /call-tool, GET /tools, GET /health), consistent response envelopes, and deployment via macOS LaunchAgents. Build HTTP wrappers for three MCP-only services (code-graph-rag, seekr, docwell) using FastAPI, standardize existing ai-gateway HTTP server, and create a wrapper generator that auto-generates bash scripts, CLI tools, Python modules, and skills from /tools schemas using Jinja2 templates.

## Technical Context

**Language/Version**: Python 3.12+ (existing project constraint from pyproject.toml)
**Primary Dependencies**:
- FastAPI (new HTTP server framework)
- mcp>=1.21.1 (existing MCP protocol)
- pymgclient>=1.4.0 (Memgraph client for code-graph-rag)
- Jinja2 (new - for wrapper generation)
- uvicorn (new - ASGI server for FastAPI)
- pydantic>=2.0 (existing - for data validation)

**Storage**: Memgraph graph database at localhost:7687 (existing infrastructure for code-graph-rag)
**Testing**: pytest>=8.4.1 (existing), pytest-asyncio (for async HTTP tests)
**Target Platform**: macOS with LaunchAgents for service management
**Project Type**: Single repository with multiple FastAPI HTTP wrappers + wrapper generator utility
**Performance Goals**:
- <100ms response time for /tools endpoint (SC-001)
- <2x baseline latency under 100 concurrent requests (SC-011)
- Wrapper generator completes in <10 seconds for all services (SC-014)

**Constraints**:
- Port assignments: 8000 (ai-gateway), 8001 (code-graph-rag), 8002 (seekr), 8003 (docwell)
- LaunchAgents must auto-restart on failure within 5 seconds (FR-028, FR-029)
- Graceful shutdown within 5 seconds (FR-037, SC-007)
- Must work with Memgraph Community Edition (no enterprise features)

**Scale/Scope**:
- Four HTTP services with unified management
- Support all existing MCP tools across four services (~20-40 tools total)
- 90%+ test coverage (SC-012)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principle Alignment

**I. Graph-First Intelligence** (code-graph-rag specific)
- ✅ **COMPLIANT**: HTTP wrappers expose existing MCP tools which already query Memgraph. No new non-graph data paths introduced.
- ✅ **COMPLIANT**: FR-013 requires Memgraph connectivity check in /health endpoint, maintaining graph as authoritative source.

**II. Multi-Language Universality** (code-graph-rag specific)
- ✅ **COMPLIANT**: HTTP layer is transport-agnostic; doesn't affect graph schema or language handling.
- ✅ **COMPLIANT**: Wrapper generator uses /tools schema which reflects unified graph query interface.

**III. AI-Native Interface**
- ✅ **COMPLIANT**: MCP tools remain first-class interface; HTTP wrappers provide additional access path for non-MCP clients.
- ⚠️ **REVIEW NEEDED**: Ensure wrapper generator preserves structured LLM-friendly responses from MCP tools.

**IV. Parse Precision** (code-graph-rag specific)
- ✅ **COMPLIANT**: HTTP layer doesn't touch parsing logic; Tree-sitter analysis remains unchanged.

**V. Safe Code Operations**
- ✅ **COMPLIANT**: HTTP wrappers are read-only for query tools; no new write operations introduced.
- ✅ **COMPLIANT**: FR-018 requires graceful shutdown preventing data corruption.

### Technical Standards Alignment

**Database Requirements**
- ✅ **COMPLIANT**: FR-013 requires Memgraph connectivity at localhost:7687 (existing config).
- ⚠️ **REVIEW NEEDED**: Project-based isolation must work through HTTP wrapper (confirm CONTAINS relationship filtering).

**Configuration Standards**
- ✅ **COMPLIANT**: FR-038/FR-039 require YAML configuration with explicit settings.
- ✅ **COMPLIANT**: No hardcoded endpoints; all config-driven.

### Gates Summary

**PASS**: All Core Principles align. No violations requiring justification.

**Action Items for Phase 0/1**:
1. Confirm wrapper generator preserves MCP tool response structure (III. AI-Native Interface)
2. Verify HTTP wrapper correctly filters by project name for isolation (Database Requirements)

## Project Structure

### Documentation (this feature)

```text
specs/004-mcp-http-standard/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
└── contracts/           # Phase 1 output (/speckit.plan command)
    ├── http-api.yaml         # OpenAPI schema for standardized endpoints
    ├── response-envelope.yaml # Response format schema
    └── error-codes.yaml      # Standard error code definitions
```

### Source Code (repository root)

```text
# HTTP Server Infrastructure (code-graph-rag)
mcp_server/
├── http_server.py       # NEW: FastAPI HTTP wrapper for code-graph-rag
├── server.py            # EXISTING: MCP stdio server
└── middleware/          # NEW: HTTP middleware
    ├── request_id.py        # Request ID tracking
    ├── logging.py           # Structured logging
    └── error_handler.py     # Standard error responses

config/
└── http-server.yaml     # NEW: HTTP server configuration

# LaunchAgent Deployment (mcp-http-gateway sibling directory)
../mcp-http-gateway/
├── services-manager.sh      # NEW: Unified service management script
├── install.sh               # NEW: LaunchAgent installation script
├── config/
│   ├── ai-gateway.yaml         # Service-specific configs
│   ├── code-graph-rag.yaml
│   ├── seekr.yaml
│   └── docwell.yaml
└── launchagents/
    ├── com.bastion.ai-gateway.plist
    ├── com.bastion.code-graph-rag.plist
    ├── com.bastion.seekr.plist
    └── com.bastion.docwell.plist

# Wrapper Generator (mcp-service-wrappers sibling directory)
../mcp-service-wrappers/
├── generator.py         # NEW: Main generator script
├── config/
│   ├── services.yaml        # Service registry
│   └── templates/           # Jinja2 templates
│       ├── bash-script.j2
│       ├── python-module.j2
│       ├── cli-tool.j2
│       └── skill-definition.j2
└── output/              # Generated wrappers
    ├── scripts/
    ├── python/
    ├── cli/
    └── skills/

# Tests
tests/
├── http/                # NEW: HTTP server tests
│   ├── test_endpoints.py
│   ├── test_response_envelope.py
│   └── test_error_codes.py
├── integration/         # NEW: End-to-end tests
│   ├── test_launchagent_deployment.py
│   └── test_wrapper_generator.py
└── unit/                # EXISTING: Existing unit tests
```

**Structure Decision**: Single repository approach for code-graph-rag HTTP wrapper with sibling directories for shared infrastructure (mcp-http-gateway) and wrapper generator (mcp-service-wrappers). This follows the existing pattern where code-graph-rag is one of several MCP services in `/shared/mcp-servers/`.

## Complexity Tracking

> **No violations requiring justification** - Constitution Check passed all gates.
