"""HTTP server entry point for weavr.

This module provides a runnable entry point for starting the FastAPI HTTP server
that exposes all MCP tools via standardized HTTP endpoints.

Usage:
    # Start with defaults (config/http-server.yaml)
    uv run python -m weavr.http

    # Override host and port
    uv run python -m weavr.http --host 0.0.0.0 --port 9000

    # Use custom config file
    uv run python -m weavr.http --config /path/to/config.yaml
"""

import argparse
import sys
from pathlib import Path

import uvicorn
from loguru import logger

from weavr.http.config import HttpServerConfig
from weavr.http.server import create_app


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments with host, port, and config options
    """
    parser = argparse.ArgumentParser(
        description="Code Graph RAG HTTP Server - Expose MCP tools via HTTP endpoints",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default configuration
  uv run python -m weavr.http

  # Override host and port
  uv run python -m weavr.http --host 0.0.0.0 --port 9000

  # Use custom config file
  uv run python -m weavr.http --config /path/to/custom-config.yaml

  # Combine config file with overrides (CLI args take precedence)
  uv run python -m weavr.http --config custom.yaml --port 8888
        """,
    )

    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host address to bind to (overrides config file). Default: 127.0.0.1",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to listen on (overrides config file). Default: 8001",
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML configuration file. Default: config/http-server.yaml",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development (not recommended for production)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="Logging level. Default: info",
    )

    return parser.parse_args()


def load_configuration(args: argparse.Namespace) -> HttpServerConfig:
    """Load and validate configuration from file and CLI arguments.

    CLI arguments override values from the configuration file.

    Args:
        args: Parsed command-line arguments

    Returns:
        HttpServerConfig instance with merged configuration

    Raises:
        FileNotFoundError: If specified config file doesn't exist
        ValueError: If configuration validation fails
    """
    # T040: Load configuration from YAML file
    config_path = Path(args.config) if args.config else None

    try:
        logger.info(
            f"Loading configuration from: {config_path or 'config/http-server.yaml'}"
        )
        config = HttpServerConfig.load_from_file(config_path)
    except FileNotFoundError as e:
        # T041: Fail fast with clear error message
        logger.error(f"Configuration file not found: {e}")
        logger.error(
            "Please create config/http-server.yaml or specify a valid config file with --config"
        )
        sys.exit(1)
    except ValueError as e:
        # T041: Fail fast with clear error message for validation errors
        logger.error(f"Configuration validation failed: {e}")
        logger.error(
            "Please check your YAML file for syntax errors and ensure all required fields are present"
        )
        sys.exit(1)
    except Exception as e:
        # T041: Catch any other configuration loading errors
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # T039: Apply CLI argument overrides (CLI args take precedence over config file)
    if args.host is not None:
        logger.info(f"Overriding host from CLI: {args.host}")
        config.service.host = args.host

    if args.port is not None:
        logger.info(f"Overriding port from CLI: {args.port}")
        config.service.port = args.port

    # T041: Validate final configuration
    try:
        # Trigger Pydantic validation by creating a new instance with the updated values
        config = HttpServerConfig(**config.model_dump())
    except Exception as e:
        logger.error(f"Configuration validation failed after applying CLI overrides: {e}")
        logger.error("Please check that your --host and --port values are valid")
        sys.exit(1)

    return config


def main() -> None:
    """Main entry point for HTTP server.

    This function:
    1. Parses CLI arguments (T039)
    2. Loads and validates configuration (T040, T041)
    3. Displays startup logging (T043)
    4. Creates FastAPI app
    5. Starts uvicorn server (T038)
    6. Handles graceful shutdown via signal handlers (T042 - handled by uvicorn)
    """
    # T039: Parse command-line arguments
    args = parse_args()

    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=args.log_level.upper(),
    )

    # T040, T041: Load and validate configuration
    config = load_configuration(args)

    # T043: Display startup information
    logger.info("=" * 80)
    logger.info("Code Graph RAG HTTP Server")
    logger.info("=" * 80)
    logger.info(f"Service:  {config.service.name}")
    logger.info(f"Version:  0.0.24")
    logger.info(f"Host:     {config.service.host}")
    logger.info(f"Port:     {config.service.port}")
    logger.info(f"Workers:  {config.server.workers}")
    logger.info(f"Timeout:  {config.server.timeout}s")
    logger.info(f"Reload:   {args.reload}")
    logger.info("=" * 80)
    logger.info(f"Configuration loaded:")
    logger.info(f"  - CORS enabled: {config.security.cors.enabled}")
    logger.info(
        f"  - Allowed origins: {', '.join(config.security.cors.allowed_origins)}"
    )
    logger.info(
        f"  - Health check interval: {config.monitoring.health_check_interval}s"
    )
    logger.info(f"  - Memgraph: {config.dependencies.memgraph.host}:{config.dependencies.memgraph.port}")
    logger.info(f"  - Graceful shutdown: {config.server.graceful_shutdown_seconds}s")
    logger.info("=" * 80)
    logger.info(f"Starting server on http://{config.service.host}:{config.service.port}")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80)

    # Create FastAPI app with loaded configuration
    app = create_app(config)

    # T038: Start uvicorn server
    # T042: Graceful shutdown is handled by uvicorn automatically via SIGTERM/SIGINT
    # T064: Apply server config to uvicorn startup
    try:
        uvicorn.run(
            app,
            host=config.service.host,
            port=config.service.port,
            workers=config.server.workers,
            log_level=args.log_level,
            reload=args.reload,
            timeout_graceful_shutdown=config.server.graceful_shutdown_seconds,
            # Uvicorn handles SIGTERM/SIGINT gracefully by default
            # It will wait for in-flight requests to complete before shutting down
        )
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down gracefully...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
