"""Health check functionality for HTTP server."""

import asyncio
import time
from typing import Optional

import mgclient
from loguru import logger

from codebase_rag.http.models import DependencyStatus, HealthStatus


class HealthChecker:
    """Manages health checks for service dependencies with background monitoring."""

    def __init__(
        self,
        service_name: str,
        version: str,
        memgraph_host: str = "localhost",
        memgraph_port: int = 7687,
        check_interval: int = 30,
    ) -> None:
        """Initialize health checker.

        Args:
            service_name: Name of the service
            version: Version of the service
            memgraph_host: Memgraph server host
            memgraph_port: Memgraph server port
            check_interval: Seconds between background health checks
        """
        self.service_name = service_name
        self.version = version
        self.memgraph_host = memgraph_host
        self.memgraph_port = memgraph_port
        self.check_interval = check_interval
        self.start_time = time.time()
        self._cached_status: Optional[HealthStatus] = None
        self._background_task: Optional[asyncio.Task[None]] = None
        self._running = False

    def get_uptime_seconds(self) -> int:
        """Get service uptime in seconds."""
        return int(time.time() - self.start_time)

    async def check_memgraph(self) -> DependencyStatus:
        """Check Memgraph connectivity and measure latency.

        Returns:
            DependencyStatus with connection status and latency
        """
        start_time = time.time()
        try:
            # Create connection and execute simple query
            conn = mgclient.connect(host=self.memgraph_host, port=self.memgraph_port)
            try:
                cursor = conn.cursor()
                cursor.execute("RETURN 1")
                cursor.fetchall()
                cursor.close()

                # Calculate latency in milliseconds
                latency_ms = int((time.time() - start_time) * 1000)

                return DependencyStatus(
                    status="connected",
                    latency_ms=latency_ms,
                )
            finally:
                conn.close()

        except Exception as e:
            logger.warning(f"Memgraph health check failed: {e}")
            return DependencyStatus(
                status="unavailable",
                error=str(e),
            )

    async def check_health(self) -> HealthStatus:
        """Check health of all dependencies and return overall status.

        Returns:
            HealthStatus object with overall status and dependency details
        """
        dependencies: dict[str, DependencyStatus] = {}

        # Check Memgraph connectivity
        dependencies["memgraph"] = await self.check_memgraph()

        # Determine overall status
        all_connected = all(
            dep.status == "connected" for dep in dependencies.values()
        )
        status = "healthy" if all_connected else "degraded"

        return HealthStatus(
            status=status,
            service=self.service_name,
            version=self.version,
            uptime_seconds=self.get_uptime_seconds(),
            dependencies=dependencies,
        )

    async def _background_health_check(self) -> None:
        """Background task that periodically checks health and updates cache."""
        logger.info(
            f"Starting background health checker (interval: {self.check_interval}s)"
        )

        while self._running:
            try:
                # Perform health check
                status = await self.check_health()
                self._cached_status = status

                # Log status changes
                if status.status != "healthy":
                    logger.warning(f"Health check: {status.status} - {status.dependencies}")
                else:
                    logger.debug(f"Health check: {status.status}")

            except Exception as e:
                logger.error(f"Background health check failed: {e}")

            # Wait for next check interval
            await asyncio.sleep(self.check_interval)

        logger.info("Background health checker stopped")

    async def start(self) -> None:
        """Start the background health check task."""
        if self._running:
            logger.warning("Health checker already running")
            return

        self._running = True

        # Perform initial health check immediately
        self._cached_status = await self.check_health()
        logger.info(f"Initial health check: {self._cached_status.status}")

        # Start background task
        self._background_task = asyncio.create_task(self._background_health_check())

    async def stop(self) -> None:
        """Stop the background health check task."""
        if not self._running:
            return

        logger.info("Stopping background health checker...")
        self._running = False

        if self._background_task:
            # Cancel the background task
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
            self._background_task = None

    def get_cached_status(self) -> HealthStatus:
        """Get the most recent cached health status.

        Returns:
            Cached HealthStatus, or a degraded status if not yet initialized

        Note:
            This is a synchronous method that returns the last known status
            from the background health checker. Use this in HTTP endpoints.
        """
        if self._cached_status is None:
            # Return degraded status if health check hasn't run yet
            return HealthStatus(
                status="degraded",
                service=self.service_name,
                version=self.version,
                uptime_seconds=self.get_uptime_seconds(),
                dependencies={
                    "memgraph": DependencyStatus(
                        status="unknown",
                        error="Health check not initialized",
                    )
                },
            )

        return self._cached_status
