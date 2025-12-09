"""Base class for stress tests."""

import time
from typing import Any

try:
    from loguru import logger
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


class BaseStressTest:
    """Base class for all stress tests providing common utilities."""

    def __init__(self, project_name: str, tools: Any, ingestor: Any):
        """Initialize base stress test.

        Args:
            project_name: Name of the project being tested
            tools: MCPToolsRegistry instance
            ingestor: MemgraphIngestor instance
        """
        self.project_name = project_name
        self.tools = tools
        self.ingestor = ingestor

    def create_result(
        self,
        status: str,
        response_time_ms: int = 0,
        **kwargs: Any
    ) -> dict[str, Any]:
        """Create a standardized test result.

        Args:
            status: Test status ("pass", "fail", "partial", "skipped")
            response_time_ms: Response time in milliseconds
            **kwargs: Additional result fields

        Returns:
            Standardized test result dictionary
        """
        result = {
            "status": status,
            "response_time_ms": response_time_ms,
        }
        result.update(kwargs)
        return result

    async def run_with_timing(self, coro):
        """Run a coroutine and return result with timing.

        Args:
            coro: Coroutine to run

        Returns:
            Tuple of (result, elapsed_ms)
        """
        start = time.time()
        try:
            result = await coro
            elapsed = int((time.time() - start) * 1000)
            return result, elapsed
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            raise

    def log_test(self, test_id: str, description: str):
        """Log test execution.

        Args:
            test_id: Test identifier
            description: Test description
        """
        logger.info(f"Running {test_id}: {description}")

    def log_error(self, test_id: str, error: Exception):
        """Log test error.

        Args:
            test_id: Test identifier
            error: Exception that occurred
        """
        logger.error(f"Test {test_id} failed: {str(error)[:100]}")

    async def get_test_results(self) -> dict[str, Any]:
        """Run all tests in this test class.

        Must be implemented by subclasses.

        Returns:
            Dictionary mapping test IDs to test results
        """
        raise NotImplementedError("Subclasses must implement get_test_results()")
