#!/usr/bin/env python3
"""Entry point for code-graph-rag structural query stress tests.

This is a comprehensive stress test suite that focuses exclusively on:
- Structural graph queries (no NL to Cypher, no semantic search, no vector search)
- All 7 structural query tools (callers, hierarchy, dependencies, etc.)
- Parameter validation and error handling
- Edge cases and boundary conditions
- Performance benchmarks
- Concurrent operations

Test modules are organized in tests/stress/:
- test_structural_queries.py: Tests all 7 structural query tools
- test_parameter_validation.py: Parameter validation and input handling
- test_edge_cases.py: Edge cases like non-existent nodes, empty results, etc.
- test_performance.py: Performance benchmarks and timing tests
- test_concurrent_operations.py: Concurrent query execution tests
- runner.py: Orchestrates all test modules

Usage:
    python stress_test.py [project_name] [project_root]

Examples:
    python stress_test.py ai-gateway-mcp
    python stress_test.py my-project /path/to/project
"""

import asyncio
import sys
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tests.stress.runner import StressTestRunner


async def main():
    """Main entry point for stress tests."""
    # Parse command line arguments
    project_name = sys.argv[1] if len(sys.argv) > 1 else "ai-gateway-mcp"
    project_root = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"\n{'='*80}")
    print(f"{'STRUCTURAL QUERY STRESS TEST':^80}")
    print(f"{'='*80}")
    print(f"  Project: {project_name}")
    print(f"  Root: {project_root or 'current directory'}")
    print(f"  Focus: Structural graph queries only")
    print(f"  Tools: 7 structural query tools + expert mode")
    print(f"{'='*80}\n")

    # Run stress tests
    runner = StressTestRunner(project_name=project_name, project_root=project_root)
    success = await runner.run_all_tests()

    if success:
        output_file = runner.save_results()
        runner.print_summary(output_file)
        return 0
    else:
        print("\n❌ Stress test failed during setup")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
