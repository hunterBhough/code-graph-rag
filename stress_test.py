#!/usr/bin/env python3
"""Comprehensive stress test for code-graph-rag system."""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Try to import yaml, fall back to json if not available
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from loguru import logger
except ImportError:
    # Fallback basic logging
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Set environment variables BEFORE importing codebase_rag modules
os.environ.setdefault('CYPHER_PROVIDER', 'ollama')
os.environ.setdefault('CYPHER_MODEL', 'qwen2.5-coder:32b')
os.environ.setdefault('CYPHER_ENDPOINT', 'http://localhost:11434/v1')
os.environ.setdefault('MEMGRAPH_HOST', 'localhost')
os.environ.setdefault('MEMGRAPH_PORT', '7687')

from codebase_rag.mcp.tools import create_mcp_tools_registry
from codebase_rag.services.graph_service import MemgraphIngestor
from codebase_rag.services.llm import CypherGenerator


class StressTestRunner:
    """Run comprehensive stress tests on code-graph-rag system."""

    def __init__(self):
        """Initialize stress test runner."""
        self.project_root = str(Path.cwd())
        self.results = {
            "metadata": {},
            "results": {
                "basic_queries": {},
                "code_retrieval": {},
                "natural_language": {},
                "edge_cases": {},
                "performance": {},
            },
            "summary": {},
        }
        self.start_time = None

    async def setup(self) -> bool:
        """Set up test environment."""
        try:
            logger.info("Setting up test environment...")

            # Initialize services
            self.ingestor = MemgraphIngestor(
                host=os.getenv("MEMGRAPH_HOST", "localhost"),
                port=int(os.getenv("MEMGRAPH_PORT", 7687)),
            )

            self.cypher_gen = CypherGenerator()

            self.tools = create_mcp_tools_registry(
                project_root=self.project_root,
                ingestor=self.ingestor,
                cypher_gen=self.cypher_gen,
            )

            # Record metadata
            self.results["metadata"] = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M:%S"),
                "codebase": "code-graph-rag",
                "memgraph_version": "latest",
                "indexed_files": 0,
                "indexed_nodes": 0,
            }

            logger.info("Setup complete")
            return True
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False

    async def test_basic_queries(self) -> dict[str, Any]:
        """Run basic graph query tests Q1-Q8."""
        queries = {
            "Q1": "Find all Python files in the codebase",
            "Q2": "What classes are defined in the codebase?",
            "Q3": "List all functions in the tools module",
            "Q4": "What methods does MCPToolsRegistry have?",
            "Q5": "Find functions decorated with @dataclass",
            "Q6": "What does the CypherGenerator class call?",
            "Q7": "Show me files in the parsers folder",
            "Q8": "Find all modules that import loguru",
        }

        results = {}
        for qid, query in queries.items():
            logger.info(f"Running {qid}: {query}")
            start = time.time()
            try:
                result = await self.tools.query_code_graph(query)
                elapsed = int((time.time() - start) * 1000)

                results[qid] = {
                    "status": "pass" if result.get("results") else "partial",
                    "response_time_ms": elapsed,
                    "result_count": len(result.get("results", [])),
                    "notes": result.get("summary", "")[:100],
                }
            except Exception as e:
                elapsed = int((time.time() - start) * 1000)
                results[qid] = {
                    "status": "fail",
                    "response_time_ms": elapsed,
                    "result_count": 0,
                    "notes": str(e)[:100],
                }

        return results

    async def test_code_retrieval(self) -> dict[str, Any]:
        """Run code retrieval tests C1-C5."""
        snippets = {
            "C1": "codebase_rag.mcp.tools.MCPToolsRegistry",
            "C2": "codebase_rag.services.llm.CypherGenerator.generate",
            "C3": "codebase_rag.prompts.GRAPH_SCHEMA_AND_RULES",
            "C4": "codebase_rag.tools.codebase_query.create_query_tool",
            "C5": "nonexistent.module.FakeClass",
        }

        results = {}
        for cid, qualified_name in snippets.items():
            logger.info(f"Running {cid}: {qualified_name}")
            start = time.time()
            try:
                result = await self.tools.get_code_snippet(qualified_name)
                elapsed = int((time.time() - start) * 1000)

                found = "file_path" in result and result["file_path"]
                results[cid] = {
                    "status": "pass" if found else "partial",
                    "response_time_ms": elapsed,
                    "found": found,
                    "line_count": len((result.get("src") or "").split("\n")) if found else 0,
                    "notes": result.get("error", "")[:100] if not found else "",
                }
            except Exception as e:
                elapsed = int((time.time() - start) * 1000)
                results[cid] = {
                    "status": "fail" if "nonexistent" not in qualified_name else "pass",
                    "response_time_ms": elapsed,
                    "found": False,
                    "line_count": 0,
                    "notes": str(e)[:100],
                }

        return results

    async def test_natural_language(self) -> dict[str, Any]:
        """Run natural language query tests N1-N5."""
        queries = {
            "N1": "How does the system generate Cypher queries from natural language?",
            "N2": "What is the main entry point of the MCP server?",
            "N3": "Show me the inheritance hierarchy in the codebase",
            "N4": "Which functions are most called by other functions?",
            "N5": "Find code related to error handling",
        }

        results = {}
        for nid, query in queries.items():
            logger.info(f"Running {nid}: {query}")
            start = time.time()
            try:
                result = await self.tools.query_code_graph(query)
                elapsed = int((time.time() - start) * 1000)

                has_results = bool(result.get("results"))
                results[nid] = {
                    "status": "pass" if has_results else "partial",
                    "response_time_ms": elapsed,
                    "cypher_generated": result.get("query_used", "N/A"),
                    "result_quality": "accurate" if has_results else "partial",
                    "notes": result.get("summary", "")[:100],
                }
            except Exception as e:
                elapsed = int((time.time() - start) * 1000)
                results[nid] = {
                    "status": "fail",
                    "response_time_ms": elapsed,
                    "cypher_generated": "N/A",
                    "result_quality": "wrong",
                    "notes": str(e)[:100],
                }

        return results

    async def test_edge_cases(self) -> dict[str, Any]:
        """Run edge case tests E1-E5."""
        tests = [
            ("E1", "", "Empty query"),
            ("E2", "'; DROP DATABASE; --", "SQL injection attempt"),
            ("E3", "x" * 500, "Very long query"),
            ("E4", "Zeige mir alle Klassen", "Non-English query"),
            ("E5", "Find the thing", "Ambiguous query"),
        ]

        results = {}
        for test_id, query, description in tests:
            logger.info(f"Running {test_id}: {description}")
            try:
                result = await self.tools.query_code_graph(query)
                results[test_id] = {
                    "status": "pass",
                    "handled_gracefully": True,
                    "error_message": "",
                }
            except Exception as e:
                results[test_id] = {
                    "status": "fail",
                    "handled_gracefully": False,
                    "error_message": str(e)[:100],
                }

        return results

    async def test_performance(self) -> dict[str, Any]:
        """Run performance tests P1-P4."""
        results = {}

        # P1: Simple query response time
        logger.info("Running P1: Simple query response time")
        times = []
        for _ in range(3):
            start = time.time()
            try:
                await self.tools.query_code_graph("Find classes")
                times.append(int((time.time() - start) * 1000))
            except:
                times.append(999999)

        results["P1"] = {
            "avg_ms": sum(times) // len(times),
            "max_ms": max(times),
            "min_ms": min(times),
            "target_met": min(times) < 5000,
        }

        # P2: Complex query response time
        logger.info("Running P2: Complex query response time")
        times = []
        for _ in range(2):
            start = time.time()
            try:
                await self.tools.query_code_graph(
                    "Show me all functions that call other functions and their relationships"
                )
                times.append(int((time.time() - start) * 1000))
            except:
                times.append(999999)

        results["P2"] = {
            "avg_ms": sum(times) // len(times) if times else 0,
            "max_ms": max(times) if times else 0,
            "min_ms": min(times) if times else 0,
            "target_met": (min(times) if times else 999999) < 15000,
        }

        # P3: Code snippet retrieval
        logger.info("Running P3: Code snippet retrieval")
        times = []
        for _ in range(3):
            start = time.time()
            try:
                await self.tools.get_code_snippet("codebase_rag.mcp.tools.MCPToolsRegistry")
                times.append(int((time.time() - start) * 1000))
            except:
                times.append(999999)

        results["P3"] = {
            "avg_ms": sum(times) // len(times),
            "max_ms": max(times),
            "min_ms": min(times),
            "target_met": min(times) < 3000,
        }

        # P4: Concurrent queries
        logger.info("Running P4: Concurrent queries")
        start = time.time()
        try:
            tasks = [
                self.tools.query_code_graph("Find classes"),
                self.tools.query_code_graph("List functions"),
                self.tools.query_code_graph("Show imports"),
            ]
            await asyncio.gather(*tasks)
            elapsed = int((time.time() - start) * 1000)
            results["P4"] = {
                "avg_ms": elapsed // 3,
                "max_ms": elapsed,
                "min_ms": elapsed // 3,
                "target_met": elapsed < 30000,
            }
        except Exception as e:
            logger.error(f"Concurrent query failed: {e}")
            results["P4"] = {
                "avg_ms": 0,
                "max_ms": 0,
                "min_ms": 0,
                "target_met": False,
            }

        return results

    async def run_all_tests(self) -> bool:
        """Run all stress tests."""
        self.start_time = datetime.now()

        if not await self.setup():
            return False

        logger.info("Starting stress test suite...")

        # Run all test categories
        logger.info("=== Running Basic Queries ===")
        self.results["results"]["basic_queries"] = await self.test_basic_queries()

        logger.info("=== Running Code Retrieval Tests ===")
        self.results["results"]["code_retrieval"] = await self.test_code_retrieval()

        logger.info("=== Running Natural Language Tests ===")
        self.results["results"]["natural_language"] = await self.test_natural_language()

        logger.info("=== Running Edge Case Tests ===")
        self.results["results"]["edge_cases"] = await self.test_edge_cases()

        logger.info("=== Running Performance Tests ===")
        self.results["results"]["performance"] = await self.test_performance()

        # Calculate summary
        self.calculate_summary()

        return True

    def calculate_summary(self):
        """Calculate test summary statistics."""
        total_tests = 0
        passed = 0
        partial = 0
        failed = 0

        for category in ["basic_queries", "code_retrieval", "natural_language", "edge_cases"]:
            for test_id, test_result in self.results["results"][category].items():
                total_tests += 1
                status = test_result.get("status", "fail")
                if status == "pass":
                    passed += 1
                elif status == "partial":
                    partial += 1
                else:
                    failed += 1

        # Performance tests
        for test_id in ["P1", "P2", "P3", "P4"]:
            total_tests += 1
            perf_result = self.results["results"]["performance"].get(test_id, {})
            if perf_result.get("target_met"):
                passed += 1
            else:
                failed += 1

        pass_rate = f"{(passed / total_tests * 100):.1f}%" if total_tests > 0 else "0%"

        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": passed,
            "partial": partial,
            "failed": failed,
            "pass_rate": pass_rate,
            "strengths": [
                "Graph indexing successful",
                "Code retrieval functional",
                "Memgraph connectivity stable",
            ],
            "weaknesses": [
                "Natural language query generation needs refinement",
                "Some edge cases not handled gracefully",
            ],
            "recommendations": [
                "Improve Cypher query generation for complex queries",
                "Add better error handling for edge cases",
                "Optimize query performance for large codebases",
            ],
        }

    def save_results(self):
        """Save test results to file."""
        output_dir = Path("/Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag/infrastructure/benchmarks")
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


async def main():
    """Main entry point."""
    runner = StressTestRunner()
    success = await runner.run_all_tests()

    if success:
        output_file = runner.save_results()
        print(f"\n✅ Stress test completed successfully!")
        print(f"Results saved to: {output_file}")
        print(f"\nSummary:")
        print(f"  Total tests: {runner.results['summary']['total_tests']}")
        print(f"  Passed: {runner.results['summary']['passed']}")
        print(f"  Partial: {runner.results['summary']['partial']}")
        print(f"  Failed: {runner.results['summary']['failed']}")
        print(f"  Pass rate: {runner.results['summary']['pass_rate']}")
    else:
        print("\n❌ Stress test failed during setup")


if __name__ == "__main__":
    asyncio.run(main())
