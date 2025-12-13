"""FastAPI HTTP server for exposing MCP tools."""

import asyncio
import json
import os
import signal
import time
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jsonschema import Draft7Validator, ValidationError as JSONSchemaValidationError
from loguru import logger

from weavr.config import settings
from weavr.http.config import HttpServerConfig
from weavr.http.health import HealthChecker
from weavr.http.models import (
    CallToolRequest,
    DependencyStatus,
    ErrorCode,
    HealthStatus,
    ResponseEnvelope,
    ServiceInfo,
    ToolSchema,
)
from weavr.mcp.tools import MCPToolsRegistry, create_mcp_tools_registry
from weavr.services.graph_service import MemgraphIngestor
from weavr.services.llm import CypherGenerator

# Global state
_server_start_time: Optional[float] = None
_config: Optional[HttpServerConfig] = None
_shutdown_requested = False
_mcp_tools_registry: Optional[MCPToolsRegistry] = None
_server_initialized = False
_health_checker: Optional[HealthChecker] = None


def get_config() -> HttpServerConfig:
    """Get the global server configuration."""
    global _config
    if _config is None:
        raise RuntimeError("Server configuration not initialized")
    return _config


def get_uptime_seconds() -> int:
    """Get server uptime in seconds."""
    global _server_start_time
    if _server_start_time is None:
        return 0
    return int(time.time() - _server_start_time)


def get_tools_registry() -> MCPToolsRegistry:
    """Get the global MCP tools registry.

    Returns:
        MCPToolsRegistry instance

    Raises:
        RuntimeError: If the server is not initialized
    """
    global _mcp_tools_registry, _server_initialized
    if not _server_initialized or _mcp_tools_registry is None:
        raise RuntimeError("Server not initialized - MCP tools registry not available")
    return _mcp_tools_registry


def is_server_initialized() -> bool:
    """Check if the server has completed initialization.

    Returns:
        True if server is ready to serve requests
    """
    global _server_initialized
    return _server_initialized


def discover_tools() -> ServiceInfo:
    """Discover all available MCP tools and their schemas.

    This function introspects the MCP server's tool registry and converts
    tool definitions to the HTTP API's ServiceInfo format.

    Returns:
        ServiceInfo containing service metadata and list of available tools

    Raises:
        RuntimeError: If the server is not initialized
    """
    registry = get_tools_registry()

    # Get tool schemas from MCP registry
    mcp_schemas = registry.get_tool_schemas()

    # Convert MCP schemas to HTTP API ToolSchema format
    tools = [
        ToolSchema(
            name=schema["name"],
            description=schema["description"],
            input_schema=schema["inputSchema"],
        )
        for schema in mcp_schemas
    ]

    # Build ServiceInfo response
    return ServiceInfo(
        service=_config.service.name if _config else "weavr",
        version="0.0.24",
        tools=tools,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager for startup/shutdown."""
    global _server_start_time, _shutdown_requested, _mcp_tools_registry, _server_initialized, _health_checker

    # Startup
    _server_start_time = time.time()
    _shutdown_requested = False
    _server_initialized = False

    logger.info(f"Starting {app.title} v{app.version}")
    if _config:
        logger.info(f"Listening on {_config.service.host}:{_config.service.port}")
    logger.info(f"Configuration loaded from: config/http-server.yaml")

    # Initialize health checker (T036)
    if _config:
        _health_checker = HealthChecker(
            service_name=_config.service.name,
            version="0.0.24",
            memgraph_host=_config.dependencies.memgraph.host,
            memgraph_port=_config.dependencies.memgraph.port,
            check_interval=_config.monitoring.health_check_interval,
        )
    else:
        _health_checker = HealthChecker(
            service_name="weavr",
            version="0.0.24",
        )
    await _health_checker.start()

    # Initialize MCP tools registry
    try:
        logger.info("Initializing MCP tools registry...")

        # For HTTP server, use current directory as project root
        # This can be overridden via TARGET_REPO_PATH environment variable
        project_root = (
            os.environ.get("TARGET_REPO_PATH")
            or settings.TARGET_REPO_PATH
            or str(Path.cwd())
        )

        logger.info(f"Project root: {project_root}")

        # Derive project name from path
        project_path = Path(project_root).resolve()
        project_name = project_path.name or "unknown"  # Fallback if name is empty

        logger.info(f"Project name: {project_name}")

        # T102: Log dependency configuration
        logger.info(f"Configuring dependencies:")
        logger.info(f"  - Memgraph host: {settings.MEMGRAPH_HOST}")
        logger.info(f"  - Memgraph port: {settings.MEMGRAPH_PORT}")
        logger.info(f"  - Batch size: {settings.MEMGRAPH_BATCH_SIZE}")

        # Initialize Memgraph connection
        logger.debug("Initializing Memgraph ingestor...")
        ingestor = MemgraphIngestor(
            host=settings.MEMGRAPH_HOST,
            port=settings.MEMGRAPH_PORT,
            batch_size=settings.MEMGRAPH_BATCH_SIZE,
            project_name=project_name,
        )
        logger.debug("Memgraph ingestor initialized successfully")

        # Initialize Cypher generator
        logger.debug("Initializing Cypher generator...")
        cypher_gen = CypherGenerator()
        logger.debug("Cypher generator initialized successfully")

        # Create tools registry
        logger.debug("Creating MCP tools registry...")
        _mcp_tools_registry = create_mcp_tools_registry(
            project_root=project_root,
            ingestor=ingestor,
            cypher_gen=cypher_gen,
        )

        _server_initialized = True
        tool_names = _mcp_tools_registry.list_tool_names()
        logger.info(
            f"MCP tools registry initialized with {len(tool_names)} tools"
        )
        logger.debug(f"Available tools: {', '.join(tool_names)}")

    except Exception as e:
        logger.error(f"Failed to initialize MCP tools registry: {e}", exc_info=True)
        # Don't prevent server startup, but mark as not initialized
        _server_initialized = False

    yield

    # Shutdown
    logger.info("Initiating graceful shutdown...")
    _shutdown_requested = True

    # Stop health checker (T036)
    if _health_checker:
        await _health_checker.stop()

    # Wait for in-flight requests to complete
    shutdown_timeout = _config.server.graceful_shutdown_seconds if _config else 5
    logger.info(f"Waiting up to {shutdown_timeout}s for in-flight requests...")
    time.sleep(0.5)  # Give middleware a chance to finish current requests

    # Clean up MCP tools registry
    if _mcp_tools_registry is not None:
        logger.info("Cleaning up MCP tools registry...")
        # The MemgraphIngestor will be cleaned up when it goes out of scope
        _mcp_tools_registry = None

    logger.info("Shutdown complete")


def create_app(config: Optional[HttpServerConfig] = None) -> FastAPI:
    """Create and configure FastAPI application.

    Args:
        config: Server configuration. If None, loads from default location.

    Returns:
        Configured FastAPI application
    """
    global _config

    # Load configuration
    if config is None:
        _config = HttpServerConfig.load_from_file()
    else:
        _config = config

    # Create FastAPI app
    app = FastAPI(
        title="Code Graph RAG HTTP Server",
        description="HTTP wrapper for MCP tools",
        version="0.0.24",
        lifespan=lifespan,
    )

    # Register signal handlers for graceful shutdown
    def signal_handler(signum: int, frame: Any) -> None:
        logger.info(f"Received signal {signum}, initiating shutdown...")

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Add CORS middleware
    if _config.security.cors.enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=_config.security.cors.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info(
            f"CORS enabled with origins: {_config.security.cors.allowed_origins}"
        )

    # Add request_id middleware (T013)
    @app.middleware("http")
    async def request_id_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Generate or extract request_id from headers."""
        # Check if client provided X-Request-ID header
        request_id = request.headers.get("x-request-id")

        # Generate UUID if not provided
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store in request state for access by handlers
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request_id to response headers
        response.headers["x-request-id"] = request_id

        return response

    # Add logging middleware (T014)
    @app.middleware("http")
    async def logging_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Log all requests and responses with request_id correlation."""
        request_id = getattr(request.state, "request_id", "unknown")
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started | request_id={request_id} | method={request.method} | path={request.url.path}"
        )

        # Process request
        try:
            response = await call_next(request)
            duration_ms = int((time.time() - start_time) * 1000)

            # Log response
            logger.info(
                f"Request completed | request_id={request_id} | status={response.status_code} | duration_ms={duration_ms}"
            )

            return response
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Request failed | request_id={request_id} | error={str(e)} | duration_ms={duration_ms}"
            )
            raise

    # Add error handler middleware (T015)
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Convert all exceptions to ResponseEnvelope format."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

        # Determine error code based on exception type
        if isinstance(exc, ValueError):
            error_code = ErrorCode.INVALID_ARGUMENTS
            status_code = 400
        elif isinstance(exc, FileNotFoundError):
            error_code = ErrorCode.TOOL_NOT_FOUND
            status_code = 404
        elif isinstance(exc, TimeoutError):
            error_code = ErrorCode.TIMEOUT
            status_code = 504
        else:
            error_code = ErrorCode.INTERNAL_ERROR
            status_code = 500

        # Create error envelope
        envelope = ResponseEnvelope[None](
            success=False,
            error=str(exc),
            code=error_code,
            request_id=request_id,
        )

        logger.error(
            f"Exception in request | request_id={request_id} | error_code={error_code} | error={str(exc)}"
        )

        return JSONResponse(
            status_code=status_code,
            content=envelope.model_dump(mode="json", exclude_none=True),
        )

    # Root endpoint
    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {
            "service": _config.service.name,
            "version": "0.0.24",
            "status": "operational",
        }

    # GET /tools endpoint (T017)
    @app.get("/tools", response_model=ServiceInfo, tags=["discovery"])
    async def list_tools(request: Request) -> ServiceInfo | JSONResponse:
        """List all available MCP tools with their schemas.

        Returns metadata about all available MCP tools including their
        input schemas for validation.

        Returns:
            ServiceInfo containing service name, version, and list of tools

        Raises:
            HTTPException: 503 if server is still initializing
        """
        # Check if server is initialized (T019)
        if not is_server_initialized():
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

            # Create error envelope
            envelope = ResponseEnvelope[None](
                success=False,
                error="Service is initializing, please retry in a few seconds",
                code=ErrorCode.SERVICE_UNAVAILABLE,
                request_id=request_id,
            )

            # Return 503 with Retry-After header
            return JSONResponse(
                status_code=503,
                content=envelope.model_dump(mode="json", exclude_none=True),
                headers={"Retry-After": "5"},  # Suggest retry after 5 seconds
            )

        # Discover tools from MCP registry
        try:
            service_info = discover_tools()
            return service_info
        except Exception as e:
            # This should not happen if initialization succeeded, but handle it gracefully
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            logger.error(
                f"Error discovering tools | request_id={request_id} | error={str(e)}"
            )

            envelope = ResponseEnvelope[None](
                success=False,
                error=f"Failed to discover tools: {str(e)}",
                code=ErrorCode.INTERNAL_ERROR,
                request_id=request_id,
            )

            return JSONResponse(
                status_code=500,
                content=envelope.model_dump(mode="json", exclude_none=True),
            )

    # POST /call-tool endpoint (T021-T029)
    @app.post("/call-tool", tags=["tools"])
    async def call_tool(tool_request: CallToolRequest, request: Request) -> JSONResponse:
        """Execute an MCP tool with the provided arguments.

        This endpoint handles:
        - Tool name validation (T022)
        - Argument validation against JSON Schema (T023)
        - MCP tool execution (T024)
        - Execution timing (T025)
        - Timeout handling (T026)
        - Error wrapping (T027)
        - Client request_id echo (T028)

        Args:
            tool_request: CallToolRequest containing tool name and arguments
            request: FastAPI request object (for request_id)

        Returns:
            JSONResponse with ResponseEnvelope containing results or errors
        """
        # T028: Use client-provided request_id or fall back to middleware-generated one
        request_id: str = str(
            tool_request.request_id
            or getattr(request.state, "request_id", str(uuid.uuid4()))
        )

        # Check if server is initialized
        if not is_server_initialized():
            envelope = ResponseEnvelope[None](
                success=False,
                error="Service is initializing, please retry in a few seconds",
                code=ErrorCode.SERVICE_UNAVAILABLE,
                request_id=request_id,
            )
            return JSONResponse(
                status_code=503,
                content=envelope.model_dump(mode="json", exclude_none=True),
                headers={"Retry-After": "5"},
            )

        try:
            registry = get_tools_registry()

            # T022: Validate tool exists
            handler_info = registry.get_tool_handler(tool_request.tool)
            if handler_info is None:
                envelope = ResponseEnvelope[None](
                    success=False,
                    error=f"Tool not found: {tool_request.tool}",
                    code=ErrorCode.TOOL_NOT_FOUND,
                    request_id=request_id,
                )
                return JSONResponse(
                    status_code=404,
                    content=envelope.model_dump(mode="json", exclude_none=True),
                )

            handler, returns_json = handler_info

            # T023: Validate arguments against tool's JSON Schema
            # Get tool schema for validation
            tool_schemas = registry.get_tool_schemas()
            tool_schema = next(
                (s for s in tool_schemas if s["name"] == tool_request.tool),
                None
            )

            if tool_schema is None:
                # This shouldn't happen if handler exists, but handle gracefully
                envelope = ResponseEnvelope[None](
                    success=False,
                    error=f"Tool schema not found: {tool_request.tool}",
                    code=ErrorCode.INTERNAL_ERROR,
                    request_id=request_id,
                )
                return JSONResponse(
                    status_code=500,
                    content=envelope.model_dump(mode="json", exclude_none=True),
                )

            # Validate arguments against input schema
            try:
                validator = Draft7Validator(tool_schema["inputSchema"])
                validator.validate(tool_request.arguments)
            except JSONSchemaValidationError as e:
                # Format validation error message
                error_path = ".".join(str(p) for p in e.path) if e.path else "root"
                error_msg = f"Invalid argument at {error_path}: {e.message}"

                envelope = ResponseEnvelope[None](
                    success=False,
                    error=error_msg,
                    code=ErrorCode.INVALID_ARGUMENTS,
                    request_id=request_id,
                )
                return JSONResponse(
                    status_code=400,
                    content=envelope.model_dump(mode="json", exclude_none=True),
                )

            # T025: Start execution timing
            start_time = time.time()

            # T026: Execute with timeout
            config = get_config()
            timeout_seconds = config.server.timeout

            try:
                # T024: Execute MCP tool
                result = await asyncio.wait_for(
                    handler(**tool_request.arguments),
                    timeout=timeout_seconds
                )

                # T025: Calculate execution time
                execution_time_ms = int((time.time() - start_time) * 1000)

                # T024: Process result based on return type
                if returns_json:
                    # Tool returns structured data (dict)
                    if isinstance(result, dict):
                        result_data = result
                    else:
                        # Try to parse as JSON string
                        try:
                            result_data = json.loads(str(result))
                        except json.JSONDecodeError:
                            result_data = {"result": str(result)}
                else:
                    # Tool returns plain text - wrap in data object
                    result_data = {"result": str(result)}

                # Create success envelope with execution time in meta
                success_envelope = ResponseEnvelope[dict[str, Any]](
                    success=True,
                    data=result_data,
                    request_id=request_id,
                    meta={"execution_time_ms": execution_time_ms}
                )

                return JSONResponse(
                    status_code=200,
                    content=success_envelope.model_dump(mode="json", exclude_none=True),
                )

            except asyncio.TimeoutError:
                # T026: Handle timeout
                execution_time_ms = int((time.time() - start_time) * 1000)

                envelope = ResponseEnvelope[None](
                    success=False,
                    error=f"Tool execution exceeded timeout of {timeout_seconds} seconds",
                    code=ErrorCode.TIMEOUT,
                    request_id=request_id,
                    meta={"execution_time_ms": execution_time_ms}
                )

                logger.warning(
                    f"Tool execution timeout | tool={tool_request.tool} | "
                    f"timeout={timeout_seconds}s | request_id={request_id}"
                )

                return JSONResponse(
                    status_code=408,
                    content=envelope.model_dump(mode="json", exclude_none=True),
                )

        except Exception as e:
            # T027: Wrap tool execution errors
            execution_time_ms = int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0

            # Log the exception with full traceback
            logger.error(
                f"Tool execution error | tool={tool_request.tool} | "
                f"error={str(e)} | request_id={request_id}",
                exc_info=True
            )

            envelope = ResponseEnvelope[None](
                success=False,
                error=f"Tool execution error: {str(e)}",
                code=ErrorCode.EXECUTION_ERROR,
                request_id=request_id,
                meta={"execution_time_ms": execution_time_ms} if execution_time_ms > 0 else None
            )

            return JSONResponse(
                status_code=500,
                content=envelope.model_dump(mode="json", exclude_none=True),
            )

    # GET /health endpoint (T034)
    @app.get("/health", response_model=HealthStatus, tags=["health"])
    async def health() -> HealthStatus:
        """Check service health and dependency status.

        Returns cached health status from background health checker.
        Health checks run every N seconds (configured via monitoring.health_check_interval).

        Returns:
            HealthStatus with overall status, uptime, and dependency details
        """
        if _health_checker is None:
            # Return degraded status if health checker not initialized
            return HealthStatus(
                status="degraded",
                service=_config.service.name,
                version="0.0.24",
                uptime_seconds=get_uptime_seconds(),
                dependencies={
                    "memgraph": DependencyStatus(
                        status="unknown",
                        error="Health checker not initialized",
                    )
                },
            )

        return _health_checker.get_cached_status()

    return app


# Create default app instance for uvicorn
app = create_app()
