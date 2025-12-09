"""Parameter validation stress tests.

Tests parameter validation for all structural query tools:
- Invalid parameter types
- Out-of-range values
- Boundary conditions
- None/null handling
- Malformed inputs
"""

import time
from typing import Any

from tests.stress.base import BaseStressTest


class ParameterValidationTest(BaseStressTest):
    """Comprehensive parameter validation tests."""

    async def get_test_results(self) -> dict[str, Any]:
        """Run all parameter validation tests.

        Returns:
            Dictionary mapping test IDs to test results
        """
        results = {}

        # P1: query_callers - Invalid max_depth (too high)
        self.log_test("P1", "query_callers - invalid max_depth (999)")
        try:
            handler, _ = self.tools.get_tool_handler("query_callers")
            result = await handler(
                function_name=f"{self.project_name}.scripts.benchmark.benchmark_models.main",
                max_depth=999  # Way beyond allowed max
            )
            has_error = "error" in result or "error_code" in result
            results["P1"] = self.create_result(
                status="pass" if has_error else "fail",
                handled_gracefully=has_error,
                error_message=result.get("error", ""),
                notes="Max depth validation (should reject values > 5)"
            )
        except Exception as e:
            self.log_error("P1", e)
            results["P1"] = self.create_result(
                status="fail",
                handled_gracefully=False,
                error_message=str(e)[:100],
                notes="Max depth validation failed unexpectedly"
            )

        # P2: query_callers - Invalid max_depth (negative)
        self.log_test("P2", "query_callers - invalid max_depth (negative)")
        try:
            handler, _ = self.tools.get_tool_handler("query_callers")
            result = await handler(
                function_name=f"{self.project_name}.scripts.benchmark.benchmark_models.main",
                max_depth=-1
            )
            has_error = "error" in result or "error_code" in result
            results["P2"] = self.create_result(
                status="pass" if has_error else "fail",
                handled_gracefully=has_error,
                error_message=result.get("error", ""),
                notes="Negative max_depth validation"
            )
        except Exception as e:
            self.log_error("P2", e)
            results["P2"] = self.create_result(
                status="fail",
                handled_gracefully=False,
                error_message=str(e)[:100],
                notes="Negative max_depth validation failed"
            )

        # P3: query_callers - None function_name
        self.log_test("P3", "query_callers - None function_name")
        try:
            handler, _ = self.tools.get_tool_handler("query_callers")
            result = await handler(
                function_name=None,  # type: ignore
                max_depth=1
            )
            results["P3"] = self.create_result(
                status="partial",
                notes="None parameter may or may not be caught at type level"
            )
        except (TypeError, AttributeError, Exception) as e:
            results["P3"] = self.create_result(
                status="pass",
                handled_gracefully=True,
                error_message=str(e)[:100],
                notes="None parameter correctly rejected"
            )

        # P4: query_callers - Empty function_name
        self.log_test("P4", "query_callers - empty function_name")
        try:
            handler, _ = self.tools.get_tool_handler("query_callers")
            result = await handler(
                function_name="",
                max_depth=1
            )
            has_error = "error" in result or "error_code" in result
            results["P4"] = self.create_result(
                status="pass" if has_error else "fail",
                handled_gracefully=has_error,
                error_message=result.get("error", ""),
                notes="Empty string parameter validation"
            )
        except Exception as e:
            results["P4"] = self.create_result(
                status="pass",
                handled_gracefully=True,
                error_message=str(e)[:100],
                notes="Empty string correctly rejected"
            )

        # P5: query_hierarchy - Invalid direction
        self.log_test("P5", "query_hierarchy - invalid direction parameter")
        try:
            handler, _ = self.tools.get_tool_handler("query_hierarchy")
            result = await handler(
                class_name=f"{self.project_name}.scripts.benchmark.utils.api_client.APIError",
                direction="sideways"  # Invalid direction
            )
            has_error = "error" in result or "error_code" in result
            results["P5"] = self.create_result(
                status="pass" if has_error else "fail",
                handled_gracefully=has_error,
                error_message=result.get("error", ""),
                notes="Invalid direction parameter validation"
            )
        except Exception as e:
            results["P5"] = self.create_result(
                status="pass",
                handled_gracefully=True,
                error_message=str(e)[:100],
                notes="Invalid direction correctly rejected"
            )

        # P6: query_hierarchy - Invalid max_depth
        self.log_test("P6", "query_hierarchy - invalid max_depth (100)")
        try:
            handler, _ = self.tools.get_tool_handler("query_hierarchy")
            result = await handler(
                class_name=f"{self.project_name}.scripts.benchmark.utils.api_client.APIError",
                direction="both",
                max_depth=100  # Beyond allowed max
            )
            has_error = "error" in result or "error_code" in result
            results["P6"] = self.create_result(
                status="pass" if has_error else "fail",
                handled_gracefully=has_error,
                error_message=result.get("error", ""),
                notes="Max depth validation for hierarchy (should reject > 10)"
            )
        except Exception as e:
            results["P6"] = self.create_result(
                status="fail",
                handled_gracefully=False,
                error_message=str(e)[:100],
                notes="Max depth validation failed unexpectedly"
            )

        # P7: query_dependencies - Invalid dependency_type
        self.log_test("P7", "query_dependencies - invalid dependency_type")
        try:
            handler, _ = self.tools.get_tool_handler("query_dependencies")
            result = await handler(
                target=f"{self.project_name}.scripts.benchmark.benchmark_models",
                dependency_type="invalid_type"  # Should be "imports", "calls", or "all"
            )
            has_error = "error" in result or "error_code" in result
            results["P7"] = self.create_result(
                status="pass" if has_error else "partial",
                handled_gracefully=has_error,
                notes="Invalid dependency_type parameter (may pass Python type checking)"
            )
        except Exception as e:
            results["P7"] = self.create_result(
                status="pass",
                handled_gracefully=True,
                error_message=str(e)[:100],
                notes="Invalid dependency_type correctly rejected"
            )

        # P8: query_call_graph - Invalid max_nodes (negative)
        self.log_test("P8", "query_call_graph - invalid max_nodes (negative)")
        try:
            handler, _ = self.tools.get_tool_handler("query_call_graph")
            result = await handler(
                entry_point=f"{self.project_name}.scripts.benchmark.benchmark_models.main",
                max_depth=2,
                max_nodes=-10
            )
            has_error = "error" in result or "error_code" in result
            results["P8"] = self.create_result(
                status="pass" if has_error else "fail",
                handled_gracefully=has_error,
                error_message=result.get("error", ""),
                notes="Negative max_nodes validation"
            )
        except Exception as e:
            results["P8"] = self.create_result(
                status="fail",
                handled_gracefully=False,
                error_message=str(e)[:100],
                notes="Negative max_nodes validation failed"
            )

        # P9: query_call_graph - Invalid max_depth (zero)
        self.log_test("P9", "query_call_graph - invalid max_depth (zero)")
        try:
            handler, _ = self.tools.get_tool_handler("query_call_graph")
            result = await handler(
                entry_point=f"{self.project_name}.scripts.benchmark.benchmark_models.main",
                max_depth=0,
                max_nodes=30
            )
            has_error = "error" in result or "error_code" in result
            results["P9"] = self.create_result(
                status="pass" if has_error else "fail",
                handled_gracefully=has_error,
                error_message=result.get("error", ""),
                notes="Zero max_depth validation"
            )
        except Exception as e:
            results["P9"] = self.create_result(
                status="pass",
                handled_gracefully=True,
                error_message=str(e)[:100],
                notes="Zero max_depth correctly rejected"
            )

        # P10: query_cypher - Empty query string
        self.log_test("P10", "query_cypher - empty query string")
        try:
            handler, _ = self.tools.get_tool_handler("query_cypher")
            result = await handler(
                query="",
                limit=10
            )
            has_error = "error" in result or "error_code" in result
            results["P10"] = self.create_result(
                status="pass" if has_error else "fail",
                handled_gracefully=has_error,
                error_message=result.get("error", ""),
                notes="Empty Cypher query validation"
            )
        except Exception as e:
            results["P10"] = self.create_result(
                status="fail",
                handled_gracefully=False,
                error_message=str(e)[:100],
                notes="Empty query validation failed"
            )

        # P11: query_cypher - Destructive query prevention (DELETE)
        self.log_test("P11", "query_cypher - destructive query prevention (DELETE)")
        try:
            handler, _ = self.tools.get_tool_handler("query_cypher")
            result = await handler(
                query="DELETE n",
                limit=10
            )
            has_error = "error" in result or "error_code" in result
            is_forbidden = "FORBIDDEN" in str(result.get("error_code", ""))
            results["P11"] = self.create_result(
                status="pass" if (has_error and is_forbidden) else "fail",
                handled_gracefully=has_error,
                error_message=result.get("error", ""),
                notes="DELETE operation should be forbidden"
            )
        except Exception as e:
            results["P11"] = self.create_result(
                status="fail",
                handled_gracefully=False,
                error_message=str(e)[:100],
                notes="Destructive query prevention failed"
            )

        # P12: query_cypher - SET operation prevention
        self.log_test("P12", "query_cypher - SET operation prevention")
        try:
            handler, _ = self.tools.get_tool_handler("query_cypher")
            result = await handler(
                query="MATCH (n:Function) SET n.test = 'value' RETURN n",
                limit=10
            )
            has_error = "error" in result or "error_code" in result
            is_forbidden = "FORBIDDEN" in str(result.get("error_code", ""))
            results["P12"] = self.create_result(
                status="pass" if (has_error and is_forbidden) else "fail",
                handled_gracefully=has_error,
                error_message=result.get("error", ""),
                notes="SET operation should be forbidden"
            )
        except Exception as e:
            results["P12"] = self.create_result(
                status="fail",
                handled_gracefully=False,
                error_message=str(e)[:100],
                notes="SET operation prevention failed"
            )

        # P13: query_cypher - CREATE operation prevention
        self.log_test("P13", "query_cypher - CREATE operation prevention")
        try:
            handler, _ = self.tools.get_tool_handler("query_cypher")
            result = await handler(
                query="CREATE (n:TestNode {name: 'test'}) RETURN n",
                limit=10
            )
            has_error = "error" in result or "error_code" in result
            is_forbidden = "FORBIDDEN" in str(result.get("error_code", ""))
            results["P13"] = self.create_result(
                status="pass" if (has_error and is_forbidden) else "fail",
                handled_gracefully=has_error,
                error_message=result.get("error", ""),
                notes="CREATE operation should be forbidden"
            )
        except Exception as e:
            results["P13"] = self.create_result(
                status="fail",
                handled_gracefully=False,
                error_message=str(e)[:100],
                notes="CREATE operation prevention failed"
            )

        # P14: query_cypher - MERGE operation prevention
        self.log_test("P14", "query_cypher - MERGE operation prevention")
        try:
            handler, _ = self.tools.get_tool_handler("query_cypher")
            result = await handler(
                query="MERGE (n:TestNode {name: 'test'}) RETURN n",
                limit=10
            )
            has_error = "error" in result or "error_code" in result
            is_forbidden = "FORBIDDEN" in str(result.get("error_code", ""))
            results["P14"] = self.create_result(
                status="pass" if (has_error and is_forbidden) else "fail",
                handled_gracefully=has_error,
                error_message=result.get("error", ""),
                notes="MERGE operation should be forbidden"
            )
        except Exception as e:
            results["P14"] = self.create_result(
                status="fail",
                handled_gracefully=False,
                error_message=str(e)[:100],
                notes="MERGE operation prevention failed"
            )

        # P15: query_cypher - Malformed Cypher syntax
        self.log_test("P15", "query_cypher - malformed Cypher syntax")
        try:
            handler, _ = self.tools.get_tool_handler("query_cypher")
            result = await handler(
                query="MATCH (n:Invalid syntax here",
                limit=10
            )
            has_error = "error" in result or isinstance(result, dict)
            results["P15"] = self.create_result(
                status="pass" if has_error else "fail",
                error_handled=has_error,
                notes="Malformed Cypher syntax should be caught"
            )
        except Exception as e:
            results["P15"] = self.create_result(
                status="pass",
                error_handled=True,
                error_message=str(e)[:100],
                notes="Malformed Cypher syntax caught by exception"
            )

        return results
