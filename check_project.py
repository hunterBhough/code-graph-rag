#!/usr/bin/env python3
"""Quick script to verify test project is indexed in Memgraph."""
import pymgclient

try:
    conn = pymgclient.connect(host='localhost', port=7687)
    conn.autocommit = True
    cursor = conn.cursor()

    # Check if ai-gateway-mcp project is indexed
    cursor.execute(
        "MATCH (p:Project {name: $project_name})-[:CONTAINS]->(n) RETURN count(n) AS node_count",
        {"project_name": "ai-gateway-mcp"}
    )
    result = cursor.fetchone()

    if result and result[0] > 0:
        print(f"✓ Test project 'ai-gateway-mcp' is indexed with {result[0]} nodes")
    else:
        print("✗ Test project 'ai-gateway-mcp' is NOT indexed (node_count = 0)")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"✗ Error connecting to Memgraph: {e}")
