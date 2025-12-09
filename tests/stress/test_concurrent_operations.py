"""Concurrent operations stress tests.

Tests concurrent execution of structural query tools:
- Multiple simultaneous queries of same tool
- Mixed tool types concurrently
- High load scenarios (10+ concurrent queries)
- Variable depth concurrent queries
- Thread safety verification
"""

import asyncio
import time
from typing import Any

from tests.stress.base import BaseStressTest


class ConcurrentOperationsTest(BaseStressTest):
    """Comprehensive concurrent operations tests."""

    async def get_test_results(self) -> dict[str, Any]:
        """Run all concurrent operations tests.

        Returns:
            Dictionary mapping test IDs to test results
        """
        results = {}

        # CONC1: Multiple simultaneous query_callers
        self.log_test("CONC1", "Concurrent query_callers (3 simultaneous)")
        try:
            handler, _ = self.tools.get_tool_handler("query_callers")
            start = time.time()

            tasks = [
                handler(
                    function_name=f"{self.project_name}.scripts.benchmark.benchmark_models.main",
                    max_depth=1
                ),
                handler(
                    function_name=f"{self.project_name}.scripts.benchmark.benchmark_models.parse_args",
                    max_depth=1
                ),
                handler(
                    function_name=f"{self.project_name}.scripts.benchmark.utils.api_client.APIClient.generate",
                    max_depth=1
                )
            ]

            concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = int((time.time() - start) * 1000)

            successful = sum(1 for r in concurrent_results if not isinstance(r, Exception))

            results["CONC1"] = self.create_result(
                status="pass" if successful == len(tasks) else "partial",
                successful_queries=successful,
                total_queries=len(tasks),
                response_time_ms=elapsed,
                notes=f"{successful}/{len(tasks)} concurrent queries succeeded in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("CONC1", e)
            results["CONC1"] = self.create_result(
                status="fail",
                error_message=str(e)[:100],
                notes="Concurrent queries failed"
            )

        # CONC2: Mixed tool types concurrently
        self.log_test("CONC2", "Mixed tool types concurrent execution")
        try:
            start = time.time()

            caller_handler, _ = self.tools.get_tool_handler("query_callers")
            hierarchy_handler, _ = self.tools.get_tool_handler("query_hierarchy")
            deps_handler, _ = self.tools.get_tool_handler("query_dependencies")

            tasks = [
                caller_handler(
                    function_name=f"{self.project_name}.scripts.benchmark.benchmark_models.main",
                    max_depth=1
                ),
                hierarchy_handler(
                    class_name=f"{self.project_name}.scripts.benchmark.utils.api_client.APIError",
                    direction="both"
                ),
                deps_handler(
                    target=f"{self.project_name}.scripts.benchmark.benchmark_models",
                    dependency_type="all"
                )
            ]

            mixed_results = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = int((time.time() - start) * 1000)

            successful = sum(1 for r in mixed_results if not isinstance(r, Exception))

            results["CONC2"] = self.create_result(
                status="pass" if successful == len(tasks) else "partial",
                successful_queries=successful,
                total_queries=len(tasks),
                response_time_ms=elapsed,
                notes=f"Mixed concurrent execution: {successful}/{len(tasks)} in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("CONC2", e)
            results["CONC2"] = self.create_result(
                status="fail",
                error_message=str(e)[:100],
                notes="Mixed concurrent execution failed"
            )

        # CONC3: High load - 10 simultaneous queries
        self.log_test("CONC3", "High load test (10 concurrent queries)")
        try:
            start = time.time()

            handler, _ = self.tools.get_tool_handler("query_module_exports")

            tasks = [
                handler(
                    module_name=f"{self.project_name}.scripts.benchmark.utils.api_client",
                    include_private=False
                )
                for _ in range(10)
            ]

            high_load_results = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = int((time.time() - start) * 1000)

            successful = sum(1 for r in high_load_results if not isinstance(r, Exception))

            results["CONC3"] = self.create_result(
                status="pass" if successful >= 8 else "partial",  # Allow some failures
                successful_queries=successful,
                total_queries=len(tasks),
                response_time_ms=elapsed,
                avg_time_per_query=elapsed // len(tasks),
                notes=f"High load: {successful}/{len(tasks)} succeeded in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("CONC3", e)
            results["CONC3"] = self.create_result(
                status="fail",
                error_message=str(e)[:100],
                notes="High load test failed"
            )

        # CONC4: Variable depth concurrent queries
        self.log_test("CONC4", "Variable depth concurrent queries")
        try:
            start = time.time()

            handler, _ = self.tools.get_tool_handler("query_callers")

            # Different depths to test query complexity variance
            tasks = [
                handler(
                    function_name=f"{self.project_name}.scripts.benchmark.benchmark_models.main",
                    max_depth=d
                )
                for d in [1, 2, 3, 1, 2]
            ]

            depth_results = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = int((time.time() - start) * 1000)

            successful = sum(1 for r in depth_results if not isinstance(r, Exception))

            results["CONC4"] = self.create_result(
                status="pass" if successful == len(tasks) else "partial",
                successful_queries=successful,
                total_queries=len(tasks),
                response_time_ms=elapsed,
                notes=f"Variable depth queries: {successful}/{len(tasks)} in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("CONC4", e)
            results["CONC4"] = self.create_result(
                status="fail",
                error_message=str(e)[:100],
                notes="Variable depth concurrent test failed"
            )

        # CONC5: Extreme load - 20 simultaneous complex queries
        self.log_test("CONC5", "Extreme load test (20 concurrent complex queries)")
        try:
            start = time.time()

            # Mix of different tools for realistic load
            caller_handler, _ = self.tools.get_tool_handler("query_callers")
            hierarchy_handler, _ = self.tools.get_tool_handler("query_hierarchy")
            deps_handler, _ = self.tools.get_tool_handler("query_dependencies")
            exports_handler, _ = self.tools.get_tool_handler("query_module_exports")

            tasks = []
            # 5 caller queries
            for _ in range(5):
                tasks.append(caller_handler(
                    function_name=f"{self.project_name}.scripts.benchmark.benchmark_models.main",
                    max_depth=2
                ))
            # 5 hierarchy queries
            for _ in range(5):
                tasks.append(hierarchy_handler(
                    class_name=f"{self.project_name}.scripts.benchmark.utils.api_client.APIError",
                    direction="both"
                ))
            # 5 dependency queries
            for _ in range(5):
                tasks.append(deps_handler(
                    target=f"{self.project_name}.scripts.benchmark.benchmark_models",
                    dependency_type="all"
                ))
            # 5 export queries
            for _ in range(5):
                tasks.append(exports_handler(
                    module_name=f"{self.project_name}.scripts.benchmark.utils.api_client",
                    include_private=False
                ))

            extreme_results = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = int((time.time() - start) * 1000)

            successful = sum(1 for r in extreme_results if not isinstance(r, Exception))

            results["CONC5"] = self.create_result(
                status="pass" if successful >= 16 else "partial",  # Allow some failures under extreme load
                successful_queries=successful,
                total_queries=len(tasks),
                response_time_ms=elapsed,
                avg_time_per_query=elapsed // len(tasks),
                notes=f"Extreme load: {successful}/{len(tasks)} succeeded in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("CONC5", e)
            results["CONC5"] = self.create_result(
                status="fail",
                error_message=str(e)[:100],
                notes="Extreme load test failed"
            )

        return results
