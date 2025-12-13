"""HTTP server configuration models."""

from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceConfig(BaseModel):
    """Service identification configuration."""

    name: str = Field(description="Service identifier (e.g., 'weavr')")
    port: int = Field(description="HTTP port to listen on", ge=1024, le=65535)
    host: str = Field(default="127.0.0.1", description="Bind address")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate service name follows lowercase-with-hyphens pattern."""
        import re

        if not re.match(r"^[a-z][a-z0-9-]*$", v):
            raise ValueError(
                "Service name must start with lowercase letter and contain only lowercase letters, digits, and hyphens"
            )
        return v


class ServerConfig(BaseModel):
    """Server runtime configuration."""

    workers: int = Field(default=1, description="Number of worker processes", ge=1)
    timeout: int = Field(
        default=30, description="Request timeout in seconds", ge=1, le=300
    )
    graceful_shutdown_seconds: int = Field(
        default=5,
        description="Time to wait for in-flight requests during shutdown",
        ge=1,
        le=60,
    )


class CorsConfig(BaseModel):
    """CORS configuration."""

    enabled: bool = Field(default=True, description="Enable CORS middleware")
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:*", "http://127.0.0.1:*"],
        description="List of allowed origin patterns",
    )


class SecurityConfig(BaseModel):
    """Security configuration."""

    api_keys_enabled: bool = Field(
        default=False, description="Require API key authentication"
    )
    rate_limit: int = Field(
        default=1000,
        description="Max requests per minute per client",
        ge=10,
    )
    cors: CorsConfig = Field(
        default_factory=CorsConfig, description="CORS configuration"
    )


class MonitoringConfig(BaseModel):
    """Monitoring and health check configuration."""

    metrics_enabled: bool = Field(
        default=False, description="Enable Prometheus-style metrics endpoint"
    )
    health_check_interval: int = Field(
        default=30,
        description="Seconds between background dependency health checks",
        ge=10,
    )


class MemgraphDependencyConfig(BaseModel):
    """Memgraph dependency configuration."""

    host: str = Field(default="localhost", description="Memgraph host")
    port: int = Field(default=7687, description="Memgraph port", ge=1, le=65535)
    timeout: int = Field(
        default=1000, description="Connection timeout in milliseconds", ge=100
    )


class DependenciesConfig(BaseModel):
    """Service-specific dependency configuration."""

    memgraph: MemgraphDependencyConfig = Field(
        default_factory=MemgraphDependencyConfig,
        description="Memgraph configuration",
    )


class HttpServerConfig(BaseSettings):
    """HTTP server configuration loaded from YAML file with environment variable overrides.

    Configuration can be overridden via environment variables using the pattern:
    HTTP_SERVER__<SECTION>__<KEY>=value

    Examples:
        HTTP_SERVER__SERVICE__PORT=8002
        HTTP_SERVER__SERVER__TIMEOUT=60
        HTTP_SERVER__MONITORING__HEALTH_CHECK_INTERVAL=60
        HTTP_SERVER__DEPENDENCIES__MEMGRAPH__HOST=memgraph.local
    """

    service: ServiceConfig
    server: ServerConfig = Field(default_factory=ServerConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    dependencies: DependenciesConfig = Field(default_factory=DependenciesConfig)

    model_config = SettingsConfigDict(
        # Enable YAML file loading
        yaml_file="config/http-server.yaml",
        # Enable environment variable overrides with double underscore as nested delimiter
        env_prefix="HTTP_SERVER__",
        env_nested_delimiter="__",
        # Case insensitive environment variable matching
        case_sensitive=False,
        # Allow extra fields in YAML for forward compatibility
        extra="ignore",
    )

    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> "HttpServerConfig":
        """Load configuration from YAML file with environment variable overrides.

        Args:
            config_path: Path to YAML config file. If None, uses default from model_config.

        Returns:
            HttpServerConfig instance with YAML values and environment overrides applied

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config validation fails with detailed error messages
        """
        import os
        import yaml

        # Determine config path
        if config_path is None:
            config_path = Path("config/http-server.yaml")

        # Check file exists
        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Expected location: {config_path.absolute()}\n"
                f"Please create the configuration file or specify a different path."
            )

        # Load and parse YAML
        try:
            with open(config_path) as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(
                f"Invalid YAML syntax in configuration file: {config_path}\n"
                f"YAML parsing error: {e}\n"
                f"Please check the YAML syntax at the location indicated above."
            ) from e

        # Apply environment variable overrides manually
        # This is more reliable than relying on pydantic-settings auto-loading
        def apply_env_overrides(data: dict[str, Any], prefix: str = "HTTP_SERVER") -> dict[str, Any]:
            """Recursively apply environment variable overrides to config data."""
            for key, value in data.items():
                env_key = f"{prefix}__{key.upper()}"

                if isinstance(value, dict):
                    # Recursively apply to nested dicts
                    apply_env_overrides(value, env_key)
                else:
                    # Check for environment variable override
                    env_value = os.environ.get(env_key)
                    if env_value is not None:
                        # Convert string to appropriate type
                        if isinstance(value, bool):
                            data[key] = env_value.lower() in ('true', '1', 'yes', 'on')
                        elif isinstance(value, int):
                            data[key] = int(env_value)
                        elif isinstance(value, list):
                            # Support JSON array format for lists
                            import json
                            try:
                                data[key] = json.loads(env_value)
                            except json.JSONDecodeError:
                                # Fall back to comma-separated values
                                data[key] = [s.strip() for s in env_value.split(',')]
                        else:
                            data[key] = env_value

            return data

        # Apply environment overrides
        config_data = apply_env_overrides(config_data)

        # Validate and create config instance
        try:
            return cls(**config_data)
        except ValidationError as e:
            # Format validation errors with YAML path and specific error details
            error_messages = []
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                error_type = error["type"]
                error_msg = error["msg"]

                # Add context about the error
                yaml_path = f"config.{field_path}"
                env_var = f"HTTP_SERVER__{field_path.replace('.', '__').upper()}"

                error_messages.append(
                    f"  - Field: {yaml_path}\n"
                    f"    Error: {error_msg}\n"
                    f"    Type: {error_type}\n"
                    f"    Environment override: {env_var}"
                )

            formatted_errors = "\n".join(error_messages)
            raise ValueError(
                f"Configuration validation failed for: {config_path}\n"
                f"\n"
                f"Validation errors:\n"
                f"{formatted_errors}\n"
                f"\n"
                f"Please fix the configuration file or set environment variables to override."
            ) from e
        except Exception as e:
            raise ValueError(
                f"Unexpected error loading configuration from: {config_path}\n"
                f"Error: {e}\n"
                f"Please check the configuration file format and values."
            ) from e
