"""Data models for HTTP server."""

from datetime import datetime
from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field, field_validator, model_validator

T = TypeVar("T")


class ErrorCode(str, Enum):
    """Standardized error codes across all services."""

    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    INVALID_ARGUMENTS = "INVALID_ARGUMENTS"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standard response structure for all HTTP endpoints."""

    success: bool = Field(description="Indicates whether the request succeeded")
    data: Optional[T] = Field(
        default=None, description="Response payload when success=true"
    )
    error: Optional[str] = Field(
        default=None, description="Human-readable error message when success=false"
    )
    code: Optional[ErrorCode] = Field(
        default=None, description="Machine-readable error code"
    )
    request_id: str = Field(description="UUID for request correlation")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")[
            :-3
        ]
        + "Z",
        description="ISO 8601 timestamp of response generation",
    )
    meta: Optional[dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )

    @model_validator(mode="after")
    def validate_xor(self) -> "ResponseEnvelope[T]":
        """Validate XOR constraint: success=true requires data, success=false requires error+code."""
        if self.success:
            if self.data is None:
                raise ValueError("data must be present when success=true")
            if self.error is not None or self.code is not None:
                raise ValueError("error and code must be null when success=true")
        else:
            if self.error is None or self.code is None:
                raise ValueError("error and code must be present when success=false")
            if self.data is not None:
                raise ValueError("data must be null when success=false")
        return self


class CallToolRequest(BaseModel):
    """Request payload for POST /call-tool endpoint."""

    tool: str = Field(description="Name of tool to execute")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Tool-specific arguments"
    )
    request_id: Optional[str] = Field(
        default=None, description="Client-provided UUID for request correlation"
    )

    @field_validator("tool")
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        """Validate tool name follows snake_case pattern."""
        if not v.replace("_", "").isalnum():
            raise ValueError(
                "Tool name must contain only alphanumeric characters and underscores"
            )
        return v


class ToolSchema(BaseModel):
    """Metadata about a single tool exposed by an MCP service."""

    name: str = Field(description="Unique identifier for the tool")
    description: str = Field(description="Human-readable description of tool's purpose")
    input_schema: dict[str, Any] = Field(
        description="JSON Schema defining valid input arguments"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate tool name is valid Python identifier."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Tool name must be a valid Python identifier")
        if not v:
            raise ValueError("Tool name must be non-empty")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate description is non-empty."""
        if not v.strip():
            raise ValueError("Description must be non-empty")
        return v

    @field_validator("input_schema")
    @classmethod
    def validate_input_schema(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate input_schema is valid JSON Schema."""
        if v.get("type") != "object":
            raise ValueError("input_schema.type must equal 'object'")
        if "properties" not in v:
            raise ValueError("input_schema must include 'properties' field")
        return v


class ServiceInfo(BaseModel):
    """Response from GET /tools endpoint listing available tools."""

    service: str = Field(description="Service name")
    version: str = Field(description="Semantic version of service")
    tools: list[ToolSchema] = Field(
        default_factory=list, description="List of available tools"
    )


class DependencyStatus(BaseModel):
    """Status of a single service dependency."""

    status: str = Field(description="Connection status: 'connected', 'unavailable', or 'unknown'")
    latency_ms: Optional[int] = Field(
        default=None, description="Last health check latency in milliseconds"
    )
    error: Optional[str] = Field(default=None, description="Error message if unavailable")


class HealthStatus(BaseModel):
    """Response from GET /health endpoint indicating service status."""

    status: str = Field(
        description="Overall status: 'healthy', 'degraded', or 'unavailable'"
    )
    service: str = Field(description="Service name")
    version: str = Field(description="Service version")
    uptime_seconds: int = Field(description="Seconds since service started")
    dependencies: dict[str, DependencyStatus] = Field(
        description="Map of dependency names to status objects"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")[
            :-3
        ]
        + "Z",
        description="ISO 8601 timestamp of health check",
    )
