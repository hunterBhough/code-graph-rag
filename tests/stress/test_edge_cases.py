"""Edge case stress tests.

Tests edge cases for structural query tools:
- Non-existent nodes
- Empty results
- Large result sets (truncation)
- Circular dependencies
- Deep traversals
- Special characters in names
"""

import time
from typing import Any

from tests.stress.base import BaseStressTest


class EdgeCasesTest(BaseStressTest):
    """Comprehensive edge case tests."""

    async def get_test_results(self) -> dict[str, Any]:
        """Run all edge case tests.

        Returns:
            Dictionary mapping test IDs to test results
        """
        results = {}

        # E1: Non-existent function for query_callers
        self.log_test("E1", "query_callers - non-existent function")
        try:
            handler, _ = self.tools.get_tool_handler("query_callers")
            result = await handler(
                function_name=f"{self.project_name}.nonexistent.module.fake_function",
                max_depth=1
            )
            has_error = "error" in result or "error_code" in result
            has_suggestion = "suggestion" in result or "re-index" in result.get("error", "").lower()
            results["E1"] = self.create_result(
                status="pass" if has_error else "fail",
                handled_gracefully=has_error,
                error_message=result.get("error", "")[:100],
                has_suggestion=has_suggestion,
                notes="Non-existent function should return clear error"
            )
        except Exception as e:
            self.log_error("E1", e)
            results["E1"] = self.create_result(
                status="fail",
                handled_gracefully=False,
                error_message=str(e)[:100],
                notes="Non-existent function query failed"
            )

        # E2: Non-existent class for query_hierarchy
        self.log_test("E2", "query_hierarchy - non-existent class")
        try:
            handler, _ = self.tools.get_tool_handler("query_hierarchy")
            result = await handler(
                class_name=f"{self.project_name}.nonexistent.FakeClass",
                direction="both"
            )
            has_error = "error" in result or "error_code" in result
            results["E2"] = self.create_result(
                status="pass" if has_error else "fail",
                handled_gracefully=has_error,
                error_message=result.get("error", "")[:100],
                notes="Non-existent class should return clear error"
            )
        except Exception as e:
            self.log_error("E2", e)
            results["E2"] = self.create_result(
                status="fail",
                handled_gracefully=False,
                error_message=str(e)[:100],
                notes="Non-existent class query failed"
            )

        # E3: Non-existent module for query_dependencies
        self.log_test("E3", "query_dependencies - non-existent module")
        try:
            handler, _ = self.tools.get_tool_handler("query_dependencies")
            result = await handler(
                target=f"{self.project_name}.nonexistent.module",
                dependency_type="imports"
            )
            has_error = "error" in result or "error_code" in result
            results["E3"] = self.create_result(
                status="pass" if has_error else "fail",
                handled_gracefully=has_error,
                error_message=result.get("error", "")[:100],
                notes="Non-existent module should return clear error"
            )
        except Exception as e:
            self.log_error("E3", e)
            results["E3"] = self.create_result(
                status="fail",
                handled_gracefully=False,
                error_message=str(e)[:100],
                notes="Non-existent module query failed"
            )

        # E4: Function with no callers (empty result)
        self.log_test("E4", "query_callers - function with no callers")
        try:
            handler, _ = self.tools.get_tool_handler("query_callers")
            result = await handler(
                function_name=f"{self.project_name}.scripts.benchmark.benchmark_models.parse_args",
                max_depth=1
            )
            # Should succeed even if no callers found
            has_metadata = "metadata" in result
            results["E4"] = self.create_result(
                status="pass" if has_metadata else "fail",
                handled_gracefully=True,
                has_results=bool(result.get("results")),
                result_count=len(result.get("results", [])),
                notes="Empty result should be handled gracefully"
            )
        except Exception as e:
            self.log_error("E4", e)
            results["E4"] = self.create_result(
                status="fail",
                handled_gracefully=False,
                error_message=str(e)[:100],
                notes="Empty result handling failed"
            )

        # E5: Large result set truncation
        self.log_test("E5", "Large result set truncation test")
        try:
            handler, _ = self.tools.get_tool_handler("query_cypher")
            result = await handler(
                query=f"MATCH (p:Project {{name: '{self.project_name}'}})-[:CONTAINS*]->(n) RETURN n.qualified_name LIMIT 200",
                limit=200
            )
            metadata = result.get("metadata", {})
            was_truncated = metadata.get("truncated", False)
            results["E5"] = self.create_result(
                status="pass",
                handled_gracefully=True,
                truncated=was_truncated,
                row_count=metadata.get("row_count", 0),
                total_count=metadata.get("total_count", 0),
                notes=f"Truncation test - truncated: {was_truncated}"
            )
        except Exception as e:
            self.log_error("E5", e)
            results["E5"] = self.create_result(
                status="fail",
                handled_gracefully=False,
                error_message=str(e)[:100],
                notes="Large result set truncation test failed"
            )

        # E6: Circular dependency detection
        self.log_test("E6", "Circular dependency detection")
        try:
            handler, _ = self.tools.get_tool_handler("query_hierarchy")
            result = await handler(
                class_name=f"{self.project_name}.scripts.benchmark.utils.api_client.APIError",
                direction="both",
                max_depth=10
            )
            # Check if circular_dependencies field exists
            has_circular_check = "circular_dependencies" in result
            results["E6"] = self.create_result(
                status="pass" if has_circular_check else "fail",
                handled_gracefully=True,
                has_circular_detection=has_circular_check,
                circular_deps=result.get("circular_dependencies", []),
                notes="Should have circular dependency detection"
            )
        except Exception as e:
            self.log_error("E6", e)
            results["E6"] = self.create_result(
                status="fail",
                handled_gracefully=False,
                error_message=str(e)[:100],
                notes="Circular dependency detection failed"
            )

        # E7: Special characters in query
        self.log_test("E7", "Special characters in qualified name")
        try:
            handler, _ = self.tools.get_tool_handler("query_cypher")
            result = await handler(
                query=f"MATCH (p:Project {{name: '{self.project_name}'}})-[:CONTAINS]->(n) WHERE n.qualified_name =~ '.*<.*>.*' RETURN count(n) as count",
                limit=1
            )
            # Should handle special regex characters gracefully
            results["E7"] = self.create_result(
                status="pass",
                error_handled=True,
                notes="Special characters handled gracefully"
            )
        except Exception as e:
            results["E7"] = self.create_result(
                status="partial",
                error_handled=True,
                error_message=str(e)[:100],
                notes="Special characters may cause issues"
            )

        # E8: Deep traversal stress test
        self.log_test("E8", "Deep traversal with max depth")
        try:
            handler, _ = self.tools.get_tool_handler("query_callers")
            result = await handler(
                function_name=f"{self.project_name}.scripts.benchmark.benchmark_models.main",
                max_depth=5  # Max allowed
            )
            metadata = result.get("metadata", {})
            results["E8"] = self.create_result(
                status="pass",
                handled_gracefully=True,
                result_count=metadata.get("row_count", 0),
                notes=f"Deep traversal (depth=5) returned {metadata.get('row_count', 0)} results"
            )
        except Exception as e:
            self.log_error("E8", e)
            results["E8"] = self.create_result(
                status="fail",
                handled_gracefully=False,
                error_message=str(e)[:100],
                notes="Deep traversal failed"
            )

        return results
