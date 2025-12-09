#!/usr/bin/env python3
"""Check if test data qualified names exist in graph."""
import pymgclient

project_name = "ai-gateway-mcp"

# Test qualified names from the test suite
test_names = [
    f"{project_name}.scripts.benchmark.benchmark_models.main",
    f"{project_name}.scripts.benchmark.utils.api_client.APIError",
    f"{project_name}.scripts.benchmark.utils.api_client",
]

try:
    conn = pymgclient.connect(host='localhost', port=7687)
    conn.autocommit = True
    cursor = conn.cursor()

    print("Checking test data qualified names in graph...\n")

    for name in test_names:
        cursor.execute(
            "MATCH (n) WHERE n.qualified_name = $name RETURN n.qualified_name, labels(n)",
            {"name": name}
        )
        result = cursor.fetchone()

        if result:
            print(f"✓ Found: {result[0]} (Type: {result[1]})")
        else:
            print(f"✗ NOT FOUND: {name}")

            # Try to find similar names
            partial = name.split('.')[-1]
            cursor.execute(
                "MATCH (n) WHERE n.name = $partial RETURN n.qualified_name LIMIT 5",
                {"partial": partial}
            )
            similar = cursor.fetchall()
            if similar:
                print(f"  Similar names found:")
                for s in similar:
                    print(f"    - {s[0]}")

    # Check for functions with "main" in name
    print("\n\nFunctions containing 'main':")
    cursor.execute(
        """
        MATCH (p:Project {name: $project})-[:CONTAINS]->(f:Function)
        WHERE f.name CONTAINS 'main'
        RETURN f.qualified_name, f.name
        LIMIT 10
        """,
        {"project": project_name}
    )
    results = cursor.fetchall()
    for r in results:
        print(f"  {r[0]}")

    # Check for classes with "Error" in name
    print("\n\nClasses containing 'Error':")
    cursor.execute(
        """
        MATCH (p:Project {name: $project})-[:CONTAINS]->(c:Class)
        WHERE c.name CONTAINS 'Error'
        RETURN c.qualified_name, c.name
        LIMIT 10
        """,
        {"project": project_name}
    )
    results = cursor.fetchall()
    for r in results:
        print(f"  {r[0]}")

    # Check for functions that have CALLS relationships (potential callers)
    print("\n\nFunctions with CALLS relationships (potential test candidates):")
    cursor.execute(
        """
        MATCH (p:Project {name: $project})-[:CONTAINS]->(f:Function)
        WHERE EXISTS((f)-[:CALLS]->())
        RETURN f.qualified_name, count{(f)-[:CALLS]->()} as call_count
        ORDER BY call_count DESC
        LIMIT 5
        """,
        {"project": project_name}
    )
    results = cursor.fetchall()
    for r in results:
        print(f"  {r[0]} (calls {r[1]} functions)")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
