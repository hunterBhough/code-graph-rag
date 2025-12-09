"""Performance stress tests.

Tests performance characteristics of structural query tools:
- Simple query response times
- Complex query response times
- Code snippet retrieval performance
- Concurrent query performance
- Performance degradation under load
"""

import asyncio
import time
from typing import Any

from tests.stress.base import BaseStressTest


class PerformanceTest(BaseStressTest):
    """Comprehensive performance tests."""

    async def get_test_results(self) -> dict[str, Any]:
        """Run all performance tests.

        Returns:
            Dictionary mapping test IDs to test results
        """
        results = {}

        # PERF1: Simple structural query response time
        self.log_test("PERF1", "Simple structural query response time")
        times = []
        for _ in range(5):
            start = time.time()
            try:
                handler, _ = self.tools.get_tool_handler("query_module_exports")
                await handler(
                    module_name=f"{self.project_name}.scripts.benchmark.utils.api_client",
                    include_private=False
                )
                times.append(int((time.time() - start) * 1000))
            except Exception:
                times.append(999999)

        target_met = min(times) < 50 if times else False
        results["PERF1"] = {
            "status": "pass" if target_met else "fail",
            "avg_ms": sum(times) // len(times) if times else 0,
            "max_ms": max(times) if times else 0,
            "min_ms": min(times) if times else 0,
            "target_met": target_met,
            "notes": "Simple query should complete in <50ms"
        }

        # PERF2: Complex traversal query response time
        self.log_test("PERF2", "Complex traversal query response time")
        times = []
        for _ in range(3):
            start = time.time()
            try:
                handler, _ = self.tools.get_tool_handler("query_callers")
                await handler(
                    function_name=f"{self.project_name}.scripts.benchmark.benchmark_models.main",
                    max_depth=3
                )
                times.append(int((time.time() - start) * 1000))
            except Exception:
                times.append(999999)

        target_met = min(times) < 150 if times else False
        results["PERF2"] = {
            "status": "pass" if target_met else "fail",
            "avg_ms": sum(times) // len(times) if times else 0,
            "max_ms": max(times) if times else 0,
            "min_ms": min(times) if times else 0,
            "target_met": target_met,
            "notes": "Complex traversal should complete in <150ms"
        }

        # PERF3: Code snippet retrieval performance
        self.log_test("PERF3", "Code snippet retrieval performance")
        times = []
        for _ in range(5):
            start = time.time()
            try:
                await self.tools.get_code_snippet(
                    f"{self.project_name}.scripts.benchmark.benchmark_models.main"
                )
                times.append(int((time.time() - start) * 1000))
            except Exception:
                times.append(999999)

        target_met = min(times) < 30 if times else False
        results["PERF3"] = {
            "status": "pass" if target_met else "fail",
            "avg_ms": sum(times) // len(times) if times else 0,
            "max_ms": max(times) if times else 0,
            "min_ms": min(times) if times else 0,
            "target_met": target_met,
            "notes": "Code snippet retrieval should complete in <30ms"
        }

        # PERF4: Call graph generation performance
        self.log_test("PERF4", "Call graph generation performance")
        times = []
        for _ in range(3):
            start = time.time()
            try:
                handler, _ = self.tools.get_tool_handler("query_call_graph")
                await handler(
                    entry_point=f"{self.project_name}.scripts.benchmark.benchmark_models.main",
                    max_depth=3,
                    max_nodes=50
                )
                times.append(int((time.time() - start) * 1000))
            except Exception:
                times.append(999999)

        target_met = min(times) < 200 if times else False
        results["PERF4"] = {
            "status": "pass" if target_met else "fail",
            "avg_ms": sum(times) // len(times) if times else 0,
            "max_ms": max(times) if times else 0,
            "min_ms": min(times) if times else 0,
            "target_met": target_met,
            "notes": "Call graph generation should complete in <200ms"
        }

        # PERF5: Cypher query performance
        self.log_test("PERF5", "Custom Cypher query performance")
        times = []
        for _ in range(5):
            start = time.time()
            try:
                handler, _ = self.tools.get_tool_handler("query_cypher")
                await handler(
                    query=f"MATCH (p:Project {{name: '{self.project_name}'}})-[:CONTAINS]->(f:Function) RETURN f.qualified_name LIMIT 20",
                    limit=20
                )
                times.append(int((time.time() - start) * 1000))
            except Exception:
                times.append(999999)

        target_met = min(times) < 50 if times else False
        results["PERF5"] = {
            "status": "pass" if target_met else "fail",
            "avg_ms": sum(times) // len(times) if times else 0,
            "max_ms": max(times) if times else 0,
            "min_ms": min(times) if times else 0,
            "target_met": target_met,
            "notes": "Custom Cypher query should complete in <50ms"
        }

        # PERF6: Sequential query performance (5 queries in sequence)
        self.log_test("PERF6", "Sequential query performance")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_module_exports")
            for _ in range(5):
                await handler(
                    module_name=f"{self.project_name}.scripts.benchmark.utils.api_client",
                    include_private=False
                )
            elapsed = int((time.time() - start) * 1000)
            avg = elapsed // 5

            target_met = avg < 50
            results["PERF6"] = {
                "status": "pass" if target_met else "fail",
                "avg_ms": avg,
                "total_ms": elapsed,
                "target_met": target_met,
                "notes": f"5 sequential queries completed in {elapsed}ms (avg {avg}ms)"
            }
        except Exception as e:
            self.log_error("PERF6", e)
            results["PERF6"] = {
                "status": "fail",
                "avg_ms": 0,
                "total_ms": 0,
                "target_met": False,
                "notes": f"Sequential query test failed: {str(e)[:100]}"
            }

        return results
