"""Health check functionality for graph-code.

Auto-generated on 2025-12-11T16:22:29.154434+00:00
"""

import time
from typing import Any

from loguru import logger


class HealthChecker:
    """Simplified health checker for HTTP server."""

    def __init__(self, service_name: str, version: str) -> None:
        """Initialize health checker.

        Args:
            service_name: Name of the service
            version: Version of the service
        """
        self.service_name = service_name
        self.version = version
        self.start_time = time.time()

    def get_uptime_seconds(self) -> int:
        """Get service uptime in seconds."""
        return int(time.time() - self.start_time)

    def check_health(self) -> dict[str, Any]:
        """Check service health.

        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy",
            "service": self.service_name,
            "version": self.version,
            "uptime_seconds": self.get_uptime_seconds(),
        }