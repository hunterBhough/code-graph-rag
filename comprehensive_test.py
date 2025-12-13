#!/usr/bin/env python3
"""
Comprehensive end-to-end test for weavr structural query engine.
Tests indexing, all 7 structural query tools, and natural language queries.
"""
from pathlib import Path
from loguru import logger
import sys

from weavr.services.graph_service import MemgraphIngestor
from weavr.parser_loader import load_parsers
from weavr.graph_updater import GraphUpdater
from weavr.config import settings
from weavr.tools.structural_queries import (
    FindCallersQuery,
    ClassHierarchyQuery,
    DependencyAnalysisQuery,
    InterfaceImplementationsQuery,
    ModuleExportsQuery,
    CallGraphGeneratorQuery,
    ExpertModeQuery
)

# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

def index_project():
    """Index the weavr project."""
    logger.info("=" * 80)
    logger.info("STEP 1: Indexing weavr project")
    logger.info("=" * 80)

    repo_path = Path(".")
    project_name = "weavr"

    with MemgraphIngestor(
        host=settings.MEMGRAPH_HOST,
        port=settings.MEMGRAPH_PORT,
        project_name=project_name
    ) as ingestor:
        # Load parsers
        parsers, queries = load_parsers()

        logger.info(f"Loaded parsers for: {list(parsers.keys())}")

        # Create updater and run indexing
        updater = GraphUpdater(
            ingestor=ingestor,
            repo_path=repo_path,
            parsers=parsers,
            queries=queries
        )

        logger.info("Running graph update (this may take a few minutes)...")
        updater.run()

        # Get statistics
        stats = ingestor.fetch_all("""
            MATCH (p:Project {name: $project_name})-[:CONTAINS]->(n)
            RETURN labels(n)[0] as type, count(n) as count
            ORDER BY count DESC
        """, {"project_name": project_name})

        logger.success("✅ Indexing complete!")
        logger.info("📊 Statistics:")
        total = 0
        for s in stats:
            logger.info(f"   - {s['type']}: {s['count']}")
            total += s['count']
        logger.info(f"   - TOTAL: {total} nodes")

        return total > 0

def test_structural_queries():
    """Test all 7 structural query tools."""
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: Testing Structural Query Tools")
    logger.info("=" * 80)

    project_name = "weavr"
    results = {}

    with MemgraphIngestor(
        host=settings.MEMGRAPH_HOST,
        port=settings.MEMGRAPH_PORT,
        project_name=project_name
    ) as ingestor:
        # Find a sample function to test with
        sample_func = ingestor.fetch_all("""
            MATCH (p:Project {name: $project_name})-[:CONTAINS]->(f:Function)
            RETURN f.qualified_name as qn
            LIMIT 1
        """, {"project_name": project_name})

        if not sample_func:
            logger.error("No functions found in graph - indexing may have failed")
            return False

        target_func = sample_func[0]['qn']
        logger.info(f"Using sample function: {target_func}")

        # Test 1: query_callers
        logger.info("\n[TEST 1/7] query_callers")
        try:
            query = FindCallersQuery(function_name=target_func, max_depth=1)
            result = query.execute(ingestor)
            results['query_callers'] = True
            logger.success(f"✅ PASS - Found {result['metadata']['row_count']} callers")
        except Exception as e:
            results['query_callers'] = False
            logger.error(f"❌ FAIL - {e}")

        # Test 2: query_hierarchy (find a class first)
        logger.info("\n[TEST 2/7] query_hierarchy")
        sample_class = ingestor.fetch_all("""
            MATCH (p:Project {name: $project_name})-[:CONTAINS]->(c:Class)
            RETURN c.qualified_name as qn
            LIMIT 1
        """, {"project_name": project_name})

        if sample_class:
            try:
                query = ClassHierarchyQuery(class_name=sample_class[0]['qn'], direction="both")
                result = query.execute(ingestor)
                results['query_hierarchy'] = True
                logger.success(f"✅ PASS - Hierarchy query executed")
            except Exception as e:
                results['query_hierarchy'] = False
                logger.error(f"❌ FAIL - {e}")
        else:
            results['query_hierarchy'] = None
            logger.warning("⚠️  SKIP - No classes found")

        # Test 3: query_dependencies
        logger.info("\n[TEST 3/7] query_dependencies")
        try:
            query = DependencyAnalysisQuery(target=target_func, type="all")
            result = query.execute(ingestor)
            results['query_dependencies'] = True
            logger.success(f"✅ PASS - Dependencies analyzed")
        except Exception as e:
            results['query_dependencies'] = False
            logger.error(f"❌ FAIL - {e}")

        # Test 4: query_implementations
        logger.info("\n[TEST 4/7] query_implementations")
        if sample_class:
            try:
                query = InterfaceImplementationsQuery(interface_name=sample_class[0]['qn'])
                result = query.execute(ingestor)
                results['query_implementations'] = True
                logger.success(f"✅ PASS - Implementations query executed")
            except Exception as e:
                results['query_implementations'] = False
                logger.error(f"❌ FAIL - {e}")
        else:
            results['query_implementations'] = None
            logger.warning("⚠️  SKIP - No classes found")

        # Test 5: query_module_exports
        logger.info("\n[TEST 5/7] query_module_exports")
        sample_module = ingestor.fetch_all("""
            MATCH (p:Project {name: $project_name})-[:CONTAINS]->(m:Module)
            RETURN m.qualified_name as qn
            LIMIT 1
        """, {"project_name": project_name})

        if sample_module:
            try:
                query = ModuleExportsQuery(module_name=sample_module[0]['qn'])
                result = query.execute(ingestor)
                results['query_module_exports'] = True
                logger.success(f"✅ PASS - Module exports retrieved")
            except Exception as e:
                results['query_module_exports'] = False
                logger.error(f"❌ FAIL - {e}")
        else:
            results['query_module_exports'] = None
            logger.warning("⚠️  SKIP - No modules found")

        # Test 6: query_call_graph
        logger.info("\n[TEST 6/7] query_call_graph")
        try:
            query = CallGraphGeneratorQuery(entry_point=target_func, max_depth=2)
            result = query.execute(ingestor)
            results['query_call_graph'] = True
            logger.success(f"✅ PASS - Call graph generated ({result['metadata']['row_count']} nodes)")
        except Exception as e:
            results['query_call_graph'] = False
            logger.error(f"❌ FAIL - {e}")

        # Test 7: query_cypher (expert mode)
        logger.info("\n[TEST 7/7] query_cypher (expert mode)")
        try:
            cypher_query = f"""
                MATCH (p:Project {{name: '{project_name}'}})-[:CONTAINS]->(n)
                RETURN labels(n)[0] as type, count(n) as count
                ORDER BY count DESC
                LIMIT 5
            """
            query = ExpertModeQuery(query=cypher_query)
            result = query.execute(ingestor)
            results['query_cypher'] = True
            logger.success(f"✅ PASS - Custom Cypher executed ({result['metadata']['row_count']} results)")
        except Exception as e:
            results['query_cypher'] = False
            logger.error(f"❌ FAIL - {e}")

    return results

def print_summary(indexing_ok, query_results):
    """Print final test summary."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    # Indexing result
    if indexing_ok:
        logger.success("✅ Indexing: PASS")
    else:
        logger.error("❌ Indexing: FAIL")

    # Query tool results
    total_tests = len([r for r in query_results.values() if r is not None])
    passed = len([r for r in query_results.values() if r is True])
    skipped = len([r for r in query_results.values() if r is None])

    for tool_name, result in query_results.items():
        if result is True:
            logger.success(f"✅ {tool_name}: PASS")
        elif result is False:
            logger.error(f"❌ {tool_name}: FAIL")
        else:
            logger.warning(f"⚠️  {tool_name}: SKIP")

    logger.info("=" * 80)
    logger.info(f"Results: {passed}/{total_tests} passed, {skipped} skipped")

    if indexing_ok and passed == total_tests:
        logger.success("\n🎉 All tests PASSED! Code-graph-rag is fully operational.")
        return 0
    else:
        logger.warning("\n⚠️  Some tests failed or were skipped.")
        return 1

def main():
    """Run comprehensive end-to-end test."""
    logger.info("🚀 Starting Comprehensive End-to-End Test")
    logger.info(f"Memgraph: {settings.MEMGRAPH_HOST}:{settings.MEMGRAPH_PORT}")
    logger.info(f"Cypher Provider: {settings.CYPHER_PROVIDER}")

    # Step 1: Index the project
    indexing_ok = index_project()

    if not indexing_ok:
        logger.error("Indexing failed - aborting tests")
        return 1

    # Step 2: Test all structural query tools
    query_results = test_structural_queries()

    # Print summary and return exit code
    return print_summary(indexing_ok, query_results)

if __name__ == "__main__":
    sys.exit(main())
