"""Stress test runner that orchestrates all test modules."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from loguru import logger
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from weavr.mcp.tools import create_mcp_tools_registry
from weavr.services.graph_service import MemgraphIngestor
from tests.stress.test_structural_queries import StructuralQueriesTest
from tests.stress.test_parameter_validation import ParameterValidationTest
from tests.stress.test_edge_cases import EdgeCasesTest
from tests.stress.test_performance import PerformanceTest
from tests.stress.test_concurrent_operations import ConcurrentOperationsTest


class StressTestRunner:
    """Orchestrates all stress test modules."""

    def __init__(self, project_name: str = "ai-gateway-mcp", project_root: str | None = None):
        """Initialize stress test runner.

        Args:
            project_name: Name of the project to test (must be indexed in Memgraph)
            project_root: Root directory of the project (defaults to cwd)
        """
        self.project_name = project_name
        self.project_root = project_root or str(Path.cwd())
        self.results = {
            "metadata": {},
            "results": {},
            "summary": {},
        }
        self.start_time = None
        self.ingestor = None
        self.tools = None

    async def setup(self) -> bool:
        """Set up test environment."""
        try:
            logger.info("Setting up stress test environment...")

            # Initialize services
            self.ingestor = MemgraphIngestor(
                host=os.getenv("MEMGRAPH_HOST", "localhost"),
                port=int(os.getenv("MEMGRAPH_PORT", 7687)),
                project_name=self.project_name,
            )

            # Open database connection
            self.ingestor.__enter__()

            # Create tools registry
            self.tools = create_mcp_tools_registry(
                project_root=self.project_root,
                ingestor=self.ingestor,
                cypher_gen=None,  # Not testing NL to Cypher
            )

            # Get graph statistics
            node_count_result = self.ingestor.fetch_all(
                f"MATCH (p:Project {{name: '{self.project_name}'}})-[:CONTAINS]->(n) RETURN count(n) as count"
            )
            node_count = node_count_result[0].get("count", 0) if node_count_result else 0

            # Get tool count
            tool_count = len(self.tools.list_tool_names())

            # Record metadata
            self.results["metadata"] = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M:%S"),
                "project_name": self.project_name,
                "indexed_nodes": node_count,
                "available_tools": tool_count,
                "test_focus": "Structural graph queries only (no NL/semantic/vector search)",
                "memgraph_host": os.getenv("MEMGRAPH_HOST", "localhost"),
                "memgraph_port": int(os.getenv("MEMGRAPH_PORT", 7687)),
            }

            logger.info(f"Setup complete - Testing project '{self.project_name}' with {node_count} nodes, {tool_count} tools")
            return True
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False

    async def run_all_tests(self) -> bool:
        """Run all stress tests."""
        self.start_time = datetime.now()

        if not await self.setup():
            return False

        logger.info("\n" + "="*80)
        logger.info("Starting Comprehensive Stress Test Suite")
        logger.info("="*80 + "\n")

        # Initialize test modules
        structural_test = StructuralQueriesTest(self.project_name, self.tools, self.ingestor)
        param_test = ParameterValidationTest(self.project_name, self.tools, self.ingestor)
        edge_test = EdgeCasesTest(self.project_name, self.tools, self.ingestor)
        perf_test = PerformanceTest(self.project_name, self.tools, self.ingestor)
        conc_test = ConcurrentOperationsTest(self.project_name, self.tools, self.ingestor)

        # Run all test categories
        logger.info("=== Running Structural Query Tests ===")
        self.results["results"]["structural_queries"] = await structural_test.get_test_results()

        logger.info("\n=== Running Parameter Validation Tests ===")
        self.results["results"]["parameter_validation"] = await param_test.get_test_results()

        logger.info("\n=== Running Edge Case Tests ===")
        self.results["results"]["edge_cases"] = await edge_test.get_test_results()

        logger.info("\n=== Running Performance Tests ===")
        self.results["results"]["performance"] = await perf_test.get_test_results()

        logger.info("\n=== Running Concurrent Operations Tests ===")
        self.results["results"]["concurrent_operations"] = await conc_test.get_test_results()

        # Calculate summary
        self.calculate_summary()

        return True

    def calculate_summary(self):
        """Calculate test summary statistics."""
        total_tests = 0
        passed = 0
        partial = 0
        failed = 0

        # Count tests in all categories
        for category, tests in self.results["results"].items():
            for test_id, test_result in tests.items():
                total_tests += 1
                status = test_result.get("status", "fail")
                if status == "pass":
                    passed += 1
                elif status == "partial":
                    partial += 1
                else:
                    failed += 1

        pass_rate = f"{(passed / total_tests * 100):.1f}%" if total_tests > 0 else "0%"

        # Calculate category-specific stats
        structural_tests = self.results["results"].get("structural_queries", {})
        structural_passed = sum(1 for t in structural_tests.values() if t.get("status") == "pass")
        structural_perf_met = sum(1 for t in structural_tests.values() if t.get("performance_target_met", False))

        param_tests = self.results["results"].get("parameter_validation", {})
        param_passed = sum(1 for t in param_tests.values() if t.get("status") == "pass")

        edge_tests = self.results["results"].get("edge_cases", {})
        edge_passed = sum(1 for t in edge_tests.values() if t.get("status") == "pass")

        perf_tests = self.results["results"].get("performance", {})
        perf_targets_met = sum(1 for t in perf_tests.values() if t.get("target_met", False))

        conc_tests = self.results["results"].get("concurrent_operations", {})
        conc_passed = sum(1 for t in conc_tests.values() if t.get("status") == "pass")

        # Determine strengths
        strengths = []
        if structural_passed >= len(structural_tests) * 0.9:
            strengths.append(f"Excellent structural query reliability: {structural_passed}/{len(structural_tests)} passed")
        if structural_perf_met >= len(structural_tests) * 0.8:
            strengths.append(f"Strong performance: {structural_perf_met}/{len(structural_tests)} met timing targets")
        if param_passed >= len(param_tests) * 0.9:
            strengths.append(f"Robust parameter validation: {param_passed}/{len(param_tests)} passed")
        if edge_passed >= len(edge_tests) * 0.85:
            strengths.append(f"Excellent edge case handling: {edge_passed}/{len(edge_tests)} passed")
        if conc_passed >= len(conc_tests) * 0.9:
            strengths.append(f"Strong concurrent operation support: {conc_passed}/{len(conc_tests)} passed")

        if not strengths:
            strengths.append("System is functional but has room for improvement")

        # Determine weaknesses
        weaknesses = []
        if structural_passed < len(structural_tests) * 0.8:
            weaknesses.append(f"Structural query reliability needs improvement: {structural_passed}/{len(structural_tests)}")
        if structural_perf_met < len(structural_tests) * 0.7:
            weaknesses.append(f"Performance targets not consistently met: {structural_perf_met}/{len(structural_tests)}")
        if param_passed < len(param_tests) * 0.8:
            weaknesses.append(f"Parameter validation gaps: {param_passed}/{len(param_tests)}")
        if edge_passed < len(edge_tests) * 0.75:
            weaknesses.append(f"Edge case handling needs work: {edge_passed}/{len(edge_tests)}")
        if conc_passed < len(conc_tests) * 0.8:
            weaknesses.append(f"Concurrent operation reliability issues: {conc_passed}/{len(conc_tests)}")
        if failed > total_tests * 0.1:
            weaknesses.append(f"High failure rate: {failed}/{total_tests} tests failed")

        if not weaknesses:
            weaknesses.append("No significant weaknesses detected - system is production-ready")

        # Generate recommendations
        recommendations = []
        if structural_perf_met < len(structural_tests) * 0.8:
            recommendations.append("Optimize slow queries - add indexes or cache frequently accessed paths")
        if param_passed < len(param_tests) * 0.9:
            recommendations.append("Strengthen input validation - add more parameter checks")
        if edge_passed < len(edge_tests) * 0.85:
            recommendations.append("Improve edge case handling - add more defensive checks")
        if conc_passed < len(conc_tests) * 0.9:
            recommendations.append("Review concurrent operation handling - check for race conditions")
        if failed > 0:
            recommendations.append(f"Investigate {failed} failed tests - review logs for root causes")

        if not recommendations:
            recommendations.append("System is performing well - continue monitoring and maintain test coverage")

        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": passed,
            "partial": partial,
            "failed": failed,
            "pass_rate": pass_rate,
            "execution_time_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "test_categories": {
                "structural_queries": {
                    "total": len(structural_tests),
                    "passed": structural_passed,
                    "performance_targets_met": structural_perf_met,
                },
                "parameter_validation": {
                    "total": len(param_tests),
                    "passed": param_passed,
                },
                "edge_cases": {
                    "total": len(edge_tests),
                    "passed": edge_passed,
                },
                "performance": {
                    "total": len(perf_tests),
                    "targets_met": perf_targets_met,
                },
                "concurrent_operations": {
                    "total": len(conc_tests),
                    "passed": conc_passed,
                },
            },
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
        }

    def save_results(self) -> Path:
        """Save test results to file.

        Returns:
            Path to the saved results file
        """
        output_dir = Path(__file__).parent.parent.parent / "infrastructure" / "benchmarks"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d")

        if HAS_YAML:
            output_file = output_dir / f"stress-test-{timestamp}.yaml"
            with open(output_file, "w") as f:
                yaml.dump(self.results, f, default_flow_style=False, sort_keys=False)
        else:
            output_file = output_dir / f"stress-test-{timestamp}.json"
            with open(output_file, "w") as f:
                json.dump(self.results, f, indent=2)

        logger.info(f"Results saved to {output_file}")
        return output_file

    def print_summary(self, output_file: Path):
        """Print test summary to console.

        Args:
            output_file: Path to the saved results file
        """
        summary = self.results['summary']

        print(f"\n{'='*80}")
        print(f"{'STRUCTURAL QUERY STRESS TEST RESULTS':^80}")
        print(f"{'='*80}\n")

        print(f"✅ Stress test completed successfully!")
        print(f"📊 Results saved to: {output_file}\n")

        print(f"{'OVERALL STATISTICS':^80}")
        print(f"{'-'*80}")
        print(f"  Total tests run:    {summary['total_tests']}")
        print(f"  ✅ Passed:          {summary['passed']}")
        print(f"  ⚠️  Partial:         {summary['partial']}")
        print(f"  ❌ Failed:          {summary['failed']}")
        print(f"  📈 Pass rate:       {summary['pass_rate']}")
        print(f"  ⏱️  Execution time:  {summary['execution_time_seconds']:.2f}s\n")

        print(f"{'TEST CATEGORIES':^80}")
        print(f"{'-'*80}")
        for category, stats in summary['test_categories'].items():
            category_name = category.replace('_', ' ').title()
            if isinstance(stats, dict):
                if "passed" in stats:
                    print(f"  {category_name:.<45} {stats['passed']}/{stats['total']} passed")
                elif "targets_met" in stats:
                    print(f"  {category_name:.<45} {stats['targets_met']}/{stats['total']} targets met")
        print()

        print(f"{'STRENGTHS':^80}")
        print(f"{'-'*80}")
        for i, strength in enumerate(summary['strengths'], 1):
            print(f"  {i}. {strength}")
        print()

        print(f"{'WEAKNESSES':^80}")
        print(f"{'-'*80}")
        for i, weakness in enumerate(summary['weaknesses'], 1):
            print(f"  {i}. {weakness}")
        print()

        print(f"{'RECOMMENDATIONS':^80}")
        print(f"{'-'*80}")
        for i, rec in enumerate(summary['recommendations'], 1):
            print(f"  {i}. {rec}")
        print()

        print(f"{'='*80}")
        print(f"For detailed results, see: {output_file}")
        print(f"{'='*80}\n")
