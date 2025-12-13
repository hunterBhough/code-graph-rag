"""Data models for graph-code HTTP server.

Auto-generated on 2025-12-11T16:22:29.154434+00:00
"""

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
            raise ValueError(
                "Tool name must contain only alphanumeric characters and underscores"
            )
        return v


class ServiceInfo(BaseModel):
    """Service information returned from GET /tools endpoint."""

    service: str = Field(description="Service name")
    version: str = Field(description="Service version")
    tools: list[ToolSchema] = Field(
        default_factory=list, description="Available tools"
    )