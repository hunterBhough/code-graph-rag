#!/usr/bin/env python3
"""Test that Project-based isolation works correctly in Community Edition."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from codebase_rag.config import settings
from codebase_rag.services.graph_service import MemgraphIngestor


def test_project_isolation():
    """Test that nodes from different projects are isolated via Project CONTAINS relationships."""
    print("=" * 80)
    print("TESTING PROJECT-BASED ISOLATION")
    print("=" * 80)

    with MemgraphIngestor(
        host=settings.MEMGRAPH_HOST,
        port=settings.MEMGRAPH_PORT,
        batch_size=10,
        project_name="test-project-a"
    ) as ingestor_a:
        # Clean database
        print("\n1. Cleaning database...")
        ingestor_a.clean_database()
        ingestor_a.ensure_constraints()

        # Create Project A
        print("2. Creating Project A...")
        ingestor_a.ensure_node_batch("Project", {"name": "test-project-a"})

        # Create some nodes for Project A
        print("3. Creating nodes for Project A...")
        ingestor_a.ensure_node_batch("Module", {
            "qualified_name": "test-project-a.module_a",
            "name": "module_a",
            "path": "/path/to/module_a.py"
        })
        ingestor_a.ensure_node_batch("Function", {
            "qualified_name": "test-project-a.module_a.func_a",
            "name": "func_a",
            "start_line": 1,
            "end_line": 5
        })
        ingestor_a.flush_all()

    # Now use a different project
    with MemgraphIngestor(
        host=settings.MEMGRAPH_HOST,
        port=settings.MEMGRAPH_PORT,
        batch_size=10,
        project_name="test-project-b"
    ) as ingestor_b:
        # Create Project B
        print("4. Creating Project B...")
        ingestor_b.ensure_node_batch("Project", {"name": "test-project-b"})

        # Create some nodes for Project B
        print("5. Creating nodes for Project B...")
        ingestor_b.ensure_node_batch("Module", {
            "qualified_name": "test-project-b.module_b",
            "name": "module_b",
            "path": "/path/to/module_b.py"
        })
        ingestor_b.ensure_node_batch("Function", {
            "qualified_name": "test-project-b.module_b.func_b",
            "name": "func_b",
            "start_line": 1,
            "end_line": 5
        })
        ingestor_b.flush_all()

    # Verify isolation
    print("\n6. Verifying isolation...")
    with MemgraphIngestor(
        host=settings.MEMGRAPH_HOST,
        port=settings.MEMGRAPH_PORT,
        project_name="__all__"  # Query across all projects for verification
    ) as ingestor:
        # Count total Projects
        result = ingestor.fetch_all("MATCH (p:Project) RETURN count(p) AS count")
        project_count = result[0]["count"]
        print(f"   ✓ Total Projects: {project_count}")
        assert project_count == 2, f"Expected 2 projects, got {project_count}"

        # Count Project A's nodes
        result = ingestor.fetch_all("""
            MATCH (p:Project {name: 'test-project-a'})-[:CONTAINS]->(n)
            RETURN count(n) AS count
        """)
        project_a_nodes = result[0]["count"]
        print(f"   ✓ Project A nodes: {project_a_nodes}")
        assert project_a_nodes == 2, f"Expected 2 nodes for Project A, got {project_a_nodes}"

        # Count Project B's nodes
        result = ingestor.fetch_all("""
            MATCH (p:Project {name: 'test-project-b'})-[:CONTAINS]->(n)
            RETURN count(n) AS count
        """)
        project_b_nodes = result[0]["count"]
        print(f"   ✓ Project B nodes: {project_b_nodes}")
        assert project_b_nodes == 2, f"Expected 2 nodes for Project B, got {project_b_nodes}"

        # Query only Project A's functions
        result = ingestor.fetch_all("""
            MATCH (p:Project {name: 'test-project-a'})-[:CONTAINS*]->(f:Function)
            RETURN f.qualified_name AS qn
        """)
        print(f"   ✓ Project A functions: {[r['qn'] for r in result]}")
        assert len(result) == 1, f"Expected 1 function for Project A, got {len(result)}"
        assert result[0]["qn"] == "test-project-a.module_a.func_a"

        # Query only Project B's functions
        result = ingestor.fetch_all("""
            MATCH (p:Project {name: 'test-project-b'})-[:CONTAINS*]->(f:Function)
            RETURN f.qualified_name AS qn
        """)
        print(f"   ✓ Project B functions: {[r['qn'] for r in result]}")
        assert len(result) == 1, f"Expected 1 function for Project B, got {len(result)}"
        assert result[0]["qn"] == "test-project-b.module_b.func_b"

        # Verify cross-project queries don't mix data
        result = ingestor.fetch_all("""
            MATCH (p:Project {name: 'test-project-a'})-[:CONTAINS*]->(f:Function)
            WHERE f.qualified_name CONTAINS 'project-b'
            RETURN count(f) AS count
        """)
        cross_contamination = result[0]["count"]
        print(f"   ✓ Cross-project contamination: {cross_contamination}")
        assert cross_contamination == 0, "Projects should not share nodes!"

    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED - Project isolation is working correctly!")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(test_project_isolation())
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
