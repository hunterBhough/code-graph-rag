#!/usr/bin/env python3
"""Manual test script to verify code-graph indexing and semantic search."""

import sys
from pathlib import Path

# Add the project to the path
sys.path.insert(0, str(Path(__file__).parent))

from weavr.config import settings
from weavr.embedder import embed_code
from weavr.services.graph_service import MemgraphIngestor
from weavr.tools.semantic_search import semantic_code_search, get_function_source_code


def test_basic_graph_query():
    """Test 1: Basic graph query to verify data is indexed."""
    print("=" * 80)
    print("TEST 1: Basic Graph Query")
    print("=" * 80)

    with MemgraphIngestor(
        host=settings.MEMGRAPH_HOST,
        port=settings.MEMGRAPH_PORT,
        batch_size=100,
        project_name="weavr"
    ) as ingestor:
        # Count total nodes
        count_query = "MATCH (n) RETURN count(n) AS total"
        result = ingestor._execute_query(count_query, {})
        total_nodes = result[0]["total"] if result else 0
        print(f"✓ Total nodes in graph: {total_nodes}")

        # Count functions
        func_query = "MATCH (n:Function) RETURN count(n) AS total"
        result = ingestor._execute_query(func_query, {})
        total_functions = result[0]["total"] if result else 0
        print(f"✓ Total functions: {total_functions}")

        # Count classes
        class_query = "MATCH (n:Class) RETURN count(n) AS total"
        result = ingestor._execute_query(class_query, {})
        total_classes = result[0]["total"] if result else 0
        print(f"✓ Total classes: {total_classes}")

        # Get sample function
        sample_query = """
        MATCH (f:Function)
        RETURN f.qualified_name AS name, id(f) AS node_id
        LIMIT 3
        """
        results = ingestor._execute_query(sample_query, {})
        print(f"\n✓ Sample functions:")
        for r in results:
            print(f"  - {r['name']} (node_id: {r['node_id']})")

        return total_nodes > 0, results[0]["node_id"] if results else None


def test_embedding_generation():
    """Test 2: Verify embeddings can be generated."""
    print("\n" + "=" * 80)
    print("TEST 2: Embedding Generation")
    print("=" * 80)

    test_code = "def parse_python_code(source): return ast.parse(source)"

    try:
        embedding = embed_code(test_code)
        print(f"✓ Embedding generated successfully")
        print(f"✓ Embedding dimensions: {len(embedding)}")
        print(f"✓ Embedding type: {type(embedding)}")
        print(f"✓ Sample values: {embedding[:5]}")

        # Verify it's the right size
        assert len(embedding) == 1024, f"Expected 1024 dimensions, got {len(embedding)}"
        print(f"✓ Embedding dimensions match expected (1024)")

        return True
    except Exception as e:
        print(f"✗ Embedding generation failed: {e}")
        return False


def test_semantic_search():
    """Test 3: Semantic search with natural language query."""
    print("\n" + "=" * 80)
    print("TEST 3: Semantic Search")
    print("=" * 80)

    # Test query: find code related to embedding
    test_queries = [
        ("code that generates embeddings", "Should find embed_code function"),
        ("graph database operations", "Should find Memgraph-related code"),
        ("parse source code", "Should find parsing functions"),
    ]

    all_passed = True
    for query, description in test_queries:
        print(f"\nQuery: '{query}'")
        print(f"Expected: {description}")

        try:
            results = semantic_code_search(query, top_k=3)

            if results:
                print(f"✓ Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result['qualified_name']}")
                    print(f"     Type: {result['type']}, Score: {result['score']}")
            else:
                print(f"✗ No results found for '{query}'")
                all_passed = False
        except Exception as e:
            print(f"✗ Semantic search failed: {e}")
            all_passed = False

    return all_passed


def test_code_retrieval(node_id: int):
    """Test 4: Retrieve actual source code."""
    print("\n" + "=" * 80)
    print("TEST 4: Code Retrieval")
    print("=" * 80)

    try:
        source_code = get_function_source_code(node_id)

        if source_code:
            print(f"✓ Successfully retrieved source code for node {node_id}")
            print(f"✓ Source code length: {len(source_code)} characters")
            print(f"\nSource preview (first 200 chars):")
            print("-" * 80)
            print(source_code[:200] + ("..." if len(source_code) > 200 else ""))
            print("-" * 80)
            return True
        else:
            print(f"✗ Could not retrieve source code for node {node_id}")
            return False
    except Exception as e:
        print(f"✗ Code retrieval failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("CODE-GRAPH-RAG MANUAL TESTING")
    print("=" * 80)
    print(f"Embedding Model: {settings.EMBEDDING_MODEL}")
    print(f"Embedding Endpoint: {settings.EMBEDDING_ENDPOINT}")
    print(f"Memgraph: {settings.MEMGRAPH_HOST}:{settings.MEMGRAPH_PORT}")
    print("=" * 80 + "\n")

    # Run tests
    results = {}

    # Test 1: Basic graph query
    graph_ok, sample_node_id = test_basic_graph_query()
    results["Basic Graph Query"] = graph_ok

    # Test 2: Embedding generation
    embedding_ok = test_embedding_generation()
    results["Embedding Generation"] = embedding_ok

    # Test 3: Semantic search
    search_ok = test_semantic_search()
    results["Semantic Search"] = search_ok

    # Test 4: Code retrieval (if we have a node ID)
    if sample_node_id:
        retrieval_ok = test_code_retrieval(sample_node_id)
        results["Code Retrieval"] = retrieval_ok

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 80)

    if all_passed:
        print("\n🎉 All tests passed! Code-graph indexing is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
