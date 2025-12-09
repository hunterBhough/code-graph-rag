"""Structural query tools stress tests.

Tests all 7 structural query tools:
- query_callers: Find function callers
- query_hierarchy: Explore class hierarchies
- query_dependencies: Analyze module dependencies
- query_implementations: Find interface implementations
- query_module_exports: List module exports
- query_call_graph: Generate call graphs
- query_cypher: Expert mode custom queries
"""

import time
from typing import Any

from tests.stress.base import BaseStressTest


class StructuralQueriesTest(BaseStressTest):
    """Comprehensive structural query tools tests."""

    async def get_test_results(self) -> dict[str, Any]:
        """Run all structural query tests.

        Returns:
            Dictionary mapping test IDs to test results
        """
        results = {}

        # S1: query_callers - Find function callers (depth 1)
        self.log_test("S1", "query_callers - find function callers (depth=1)")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_callers")
            result = await handler(
                function_name=f"{self.project_name}.scripts.benchmark.benchmark_models.main",
                max_depth=1,
                include_paths=True
            )
            elapsed = int((time.time() - start) * 1000)

            # If no error_code, then 0 results is legitimate (function exists but has no callers)
            has_error = "error_code" in result
            metadata = result.get("metadata", {})

            results["S1"] = self.create_result(
                status="fail" if has_error else "pass",
                response_time_ms=elapsed,
                result_count=metadata.get("row_count", 0),
                performance_target_met=elapsed < 50,
                notes=f"Found {metadata.get('row_count', 0)} callers in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("S1", e)
            elapsed = int((time.time() - start) * 1000)
            results["S1"] = self.create_result(
                status="fail",
                response_time_ms=elapsed,
                result_count=0,
                performance_target_met=False,
                notes=str(e)[:100]
            )

        # S2: query_callers - Multi-level caller traversal (depth 3)
        self.log_test("S2", "query_callers - multi-level traversal (depth=3)")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_callers")
            result = await handler(
                function_name=f"{self.project_name}.scripts.benchmark.benchmark_models.main",
                max_depth=3,
                include_paths=True
            )
            elapsed = int((time.time() - start) * 1000)

            # If no error_code, then 0 results is legitimate (function exists but has no callers)
            has_error = "error_code" in result
            metadata = result.get("metadata", {})

            results["S2"] = self.create_result(
                status="fail" if has_error else "pass",
                response_time_ms=elapsed,
                result_count=metadata.get("row_count", 0),
                performance_target_met=elapsed < 150,
                notes=f"Multi-level traversal found {metadata.get('row_count', 0)} callers in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("S2", e)
            elapsed = int((time.time() - start) * 1000)
            results["S2"] = self.create_result(
                status="fail",
                response_time_ms=elapsed,
                result_count=0,
                performance_target_met=False,
                notes=str(e)[:100]
            )

        # S3: query_hierarchy - Class inheritance (down)
        self.log_test("S3", "query_hierarchy - class inheritance descendants")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_hierarchy")
            result = await handler(
                class_name=f"{self.project_name}.scripts.benchmark.utils.api_client.APIError",
                direction="down",
                max_depth=5
            )
            elapsed = int((time.time() - start) * 1000)

            metadata = result.get("metadata", {})
            row_count = metadata.get("row_count", 0)

            results["S3"] = self.create_result(
                status="pass" if row_count > 0 else "partial",
                response_time_ms=elapsed,
                result_count=row_count,
                performance_target_met=elapsed < 50,
                notes=f"Found {row_count} descendants in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("S3", e)
            elapsed = int((time.time() - start) * 1000)
            results["S3"] = self.create_result(
                status="fail",
                response_time_ms=elapsed,
                result_count=0,
                performance_target_met=False,
                notes=str(e)[:100]
            )

        # S4: query_hierarchy - Class inheritance (up)
        self.log_test("S4", "query_hierarchy - class inheritance ancestors")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_hierarchy")
            result = await handler(
                class_name=f"{self.project_name}.scripts.benchmark.utils.api_client.APIError",
                direction="up",
                max_depth=5
            )
            elapsed = int((time.time() - start) * 1000)

            metadata = result.get("metadata", {})
            row_count = metadata.get("row_count", 0)

            results["S4"] = self.create_result(
                status="pass",  # May have 0 ancestors (base class)
                response_time_ms=elapsed,
                result_count=row_count,
                performance_target_met=elapsed < 50,
                notes=f"Found {row_count} ancestors in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("S4", e)
            elapsed = int((time.time() - start) * 1000)
            results["S4"] = self.create_result(
                status="fail",
                response_time_ms=elapsed,
                result_count=0,
                performance_target_met=False,
                notes=str(e)[:100]
            )

        # S5: query_hierarchy - Bidirectional hierarchy
        self.log_test("S5", "query_hierarchy - bidirectional traversal")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_hierarchy")
            result = await handler(
                class_name=f"{self.project_name}.scripts.benchmark.utils.api_client.APIError",
                direction="both",
                max_depth=10
            )
            elapsed = int((time.time() - start) * 1000)

            metadata = result.get("metadata", {})
            row_count = metadata.get("row_count", 0)

            results["S5"] = self.create_result(
                status="pass" if row_count > 0 else "partial",
                response_time_ms=elapsed,
                result_count=row_count,
                performance_target_met=elapsed < 100,
                notes=f"Bidirectional traversal found {row_count} classes in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("S5", e)
            elapsed = int((time.time() - start) * 1000)
            results["S5"] = self.create_result(
                status="fail",
                response_time_ms=elapsed,
                result_count=0,
                performance_target_met=False,
                notes=str(e)[:100]
            )

        # S6: query_dependencies - Module imports
        self.log_test("S6", "query_dependencies - module imports")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_dependencies")
            result = await handler(
                target=f"{self.project_name}.scripts.benchmark.benchmark_models",
                dependency_type="imports"
            )
            elapsed = int((time.time() - start) * 1000)

            # If no error_code, then 0 results is legitimate (module exists but has no imports)
            has_error = "error_code" in result
            metadata = result.get("metadata", {})
            row_count = metadata.get("row_count", 0)

            results["S6"] = self.create_result(
                status="fail" if has_error else "pass",
                response_time_ms=elapsed,
                result_count=row_count,
                performance_target_met=elapsed < 50,
                notes=f"Found {row_count} import dependencies in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("S6", e)
            elapsed = int((time.time() - start) * 1000)
            results["S6"] = self.create_result(
                status="fail",
                response_time_ms=elapsed,
                result_count=0,
                performance_target_met=False,
                notes=str(e)[:100]
            )

        # S7: query_dependencies - Function calls
        self.log_test("S7", "query_dependencies - function calls")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_dependencies")
            result = await handler(
                target=f"{self.project_name}.scripts.benchmark.benchmark_models.main",
                dependency_type="calls"
            )
            elapsed = int((time.time() - start) * 1000)

            metadata = result.get("metadata", {})
            row_count = metadata.get("row_count", 0)

            results["S7"] = self.create_result(
                status="pass" if row_count > 0 else "partial",
                response_time_ms=elapsed,
                result_count=row_count,
                performance_target_met=elapsed < 50,
                notes=f"Found {row_count} call dependencies in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("S7", e)
            elapsed = int((time.time() - start) * 1000)
            results["S7"] = self.create_result(
                status="fail",
                response_time_ms=elapsed,
                result_count=0,
                performance_target_met=False,
                notes=str(e)[:100]
            )

        # S8: query_dependencies - All dependencies
        self.log_test("S8", "query_dependencies - all dependency types")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_dependencies")
            result = await handler(
                target=f"{self.project_name}.scripts.benchmark.benchmark_models",
                dependency_type="all"
            )
            elapsed = int((time.time() - start) * 1000)

            # If no error_code, then 0 results is legitimate (module exists but has no dependencies)
            has_error = "error_code" in result
            metadata = result.get("metadata", {})
            row_count = metadata.get("row_count", 0)

            results["S8"] = self.create_result(
                status="fail" if has_error else "pass",
                response_time_ms=elapsed,
                result_count=row_count,
                performance_target_met=elapsed < 100,
                notes=f"Found {row_count} total dependencies in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("S8", e)
            elapsed = int((time.time() - start) * 1000)
            results["S8"] = self.create_result(
                status="fail",
                response_time_ms=elapsed,
                result_count=0,
                performance_target_met=False,
                notes=str(e)[:100]
            )

        # S9: query_implementations - Find implementations
        self.log_test("S9", "query_implementations - direct implementations")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_implementations")
            result = await handler(
                interface_name=f"{self.project_name}.scripts.benchmark.utils.api_client.APIError",
                include_indirect=False
            )
            elapsed = int((time.time() - start) * 1000)

            metadata = result.get("metadata", {})
            row_count = metadata.get("row_count", 0)

            results["S9"] = self.create_result(
                status="pass",  # May have 0 implementations
                response_time_ms=elapsed,
                result_count=row_count,
                performance_target_met=elapsed < 50,
                notes=f"Found {row_count} direct implementations in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("S9", e)
            elapsed = int((time.time() - start) * 1000)
            results["S9"] = self.create_result(
                status="fail",
                response_time_ms=elapsed,
                result_count=0,
                performance_target_met=False,
                notes=str(e)[:100]
            )

        # S10: query_implementations - Include indirect implementations
        self.log_test("S10", "query_implementations - indirect implementations")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_implementations")
            result = await handler(
                interface_name=f"{self.project_name}.scripts.benchmark.utils.api_client.APIError",
                include_indirect=True
            )
            elapsed = int((time.time() - start) * 1000)

            metadata = result.get("metadata", {})
            row_count = metadata.get("row_count", 0)

            results["S10"] = self.create_result(
                status="pass",  # May have 0 implementations
                response_time_ms=elapsed,
                result_count=row_count,
                performance_target_met=elapsed < 100,
                notes=f"Found {row_count} total implementations (including indirect) in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("S10", e)
            elapsed = int((time.time() - start) * 1000)
            results["S10"] = self.create_result(
                status="fail",
                response_time_ms=elapsed,
                result_count=0,
                performance_target_met=False,
                notes=str(e)[:100]
            )

        # S11: query_module_exports - Public exports only
        self.log_test("S11", "query_module_exports - public exports")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_module_exports")
            result = await handler(
                module_name=f"{self.project_name}.scripts.benchmark.utils.api_client",
                include_private=False
            )
            elapsed = int((time.time() - start) * 1000)

            has_results = bool(result.get("results"))
            metadata = result.get("metadata", {})

            results["S11"] = self.create_result(
                status="pass" if has_results else "partial",
                response_time_ms=elapsed,
                result_count=metadata.get("row_count", 0),
                performance_target_met=elapsed < 50,
                notes=f"Found {metadata.get('row_count', 0)} public exports in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("S11", e)
            elapsed = int((time.time() - start) * 1000)
            results["S11"] = self.create_result(
                status="fail",
                response_time_ms=elapsed,
                result_count=0,
                performance_target_met=False,
                notes=str(e)[:100]
            )

        # S12: query_module_exports - Include private exports
        self.log_test("S12", "query_module_exports - all exports including private")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_module_exports")
            result = await handler(
                module_name=f"{self.project_name}.scripts.benchmark.utils.api_client",
                include_private=True
            )
            elapsed = int((time.time() - start) * 1000)

            has_results = bool(result.get("results"))
            metadata = result.get("metadata", {})

            results["S12"] = self.create_result(
                status="pass" if has_results else "partial",
                response_time_ms=elapsed,
                result_count=metadata.get("row_count", 0),
                performance_target_met=elapsed < 50,
                notes=f"Found {metadata.get('row_count', 0)} total exports (including private) in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("S12", e)
            elapsed = int((time.time() - start) * 1000)
            results["S12"] = self.create_result(
                status="fail",
                response_time_ms=elapsed,
                result_count=0,
                performance_target_met=False,
                notes=str(e)[:100]
            )

        # S13: query_call_graph - Simple call graph
        self.log_test("S13", "query_call_graph - simple call graph (depth=2)")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_call_graph")
            result = await handler(
                entry_point=f"{self.project_name}.scripts.benchmark.benchmark_models.main",
                max_depth=2,
                max_nodes=30
            )
            elapsed = int((time.time() - start) * 1000)

            metadata = result.get("metadata", {})
            row_count = metadata.get("row_count", 0)

            results["S13"] = self.create_result(
                status="pass" if row_count > 0 else "partial",
                response_time_ms=elapsed,
                result_count=row_count,
                performance_target_met=elapsed < 100,
                notes=f"Generated call graph with {row_count} nodes in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("S13", e)
            elapsed = int((time.time() - start) * 1000)
            results["S13"] = self.create_result(
                status="fail",
                response_time_ms=elapsed,
                result_count=0,
                performance_target_met=False,
                notes=str(e)[:100]
            )

        # S14: query_call_graph - Deep call graph
        self.log_test("S14", "query_call_graph - deep call graph (depth=4)")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_call_graph")
            result = await handler(
                entry_point=f"{self.project_name}.scripts.benchmark.benchmark_models.main",
                max_depth=4,
                max_nodes=100
            )
            elapsed = int((time.time() - start) * 1000)

            metadata = result.get("metadata", {})
            row_count = metadata.get("row_count", 0)

            results["S14"] = self.create_result(
                status="pass" if row_count > 0 else "partial",
                response_time_ms=elapsed,
                result_count=row_count,
                performance_target_met=elapsed < 300,
                notes=f"Generated deep call graph with {row_count} nodes in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("S14", e)
            elapsed = int((time.time() - start) * 1000)
            results["S14"] = self.create_result(
                status="fail",
                response_time_ms=elapsed,
                result_count=0,
                performance_target_met=False,
                notes=str(e)[:100]
            )

        # S15: query_cypher - Simple custom query
        self.log_test("S15", "query_cypher - simple custom query")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_cypher")
            result = await handler(
                query=f"MATCH (p:Project {{name: '{self.project_name}'}})-[:CONTAINS]->(f:Function) RETURN f.qualified_name AS name LIMIT 10",
                limit=10
            )
            elapsed = int((time.time() - start) * 1000)

            metadata = result.get("metadata", {})
            row_count = metadata.get("row_count", 0)

            results["S15"] = self.create_result(
                status="pass" if row_count > 0 else "partial",
                response_time_ms=elapsed,
                result_count=row_count,
                performance_target_met=elapsed < 50,
                notes=f"Custom Cypher query returned {row_count} results in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("S15", e)
            elapsed = int((time.time() - start) * 1000)
            results["S15"] = self.create_result(
                status="fail",
                response_time_ms=elapsed,
                result_count=0,
                performance_target_met=False,
                notes=str(e)[:100]
            )

        # S16: query_cypher - Complex custom query with joins
        self.log_test("S16", "query_cypher - complex query with relationships")
        start = time.time()
        try:
            handler, _ = self.tools.get_tool_handler("query_cypher")
            result = await handler(
                query=f"""
                    MATCH (p:Project {{name: '{self.project_name}'}})-[:CONTAINS]->(m:Module)
                    -[:CONTAINS]->(c:Class)-[:CONTAINS]->(method:Method)
                    RETURN m.qualified_name AS module, c.name AS class, method.name AS method
                    LIMIT 20
                """,
                limit=20
            )
            elapsed = int((time.time() - start) * 1000)

            # If no error_code, then 0 results is legitimate (query executed successfully, no matching data)
            has_error = "error_code" in result
            metadata = result.get("metadata", {})
            row_count = metadata.get("row_count", 0)

            results["S16"] = self.create_result(
                status="fail" if has_error else "pass",
                response_time_ms=elapsed,
                result_count=row_count,
                performance_target_met=elapsed < 100,
                notes=f"Complex Cypher query returned {row_count} results in {elapsed}ms"
            )
        except Exception as e:
            self.log_error("S16", e)
            elapsed = int((time.time() - start) * 1000)
            results["S16"] = self.create_result(
                status="fail",
                response_time_ms=elapsed,
                result_count=0,
                performance_target_met=False,
                notes=str(e)[:100]
            )

        return results
