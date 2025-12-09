#!/bin/bash
# Run stress test with Claude via AI Gateway

# Configuration - AI Gateway routes to Claude
export CYPHER_PROVIDER=openai
export CYPHER_MODEL=claude-3-5-haiku-20241022  # AI Gateway will route this
export CYPHER_ENDPOINT=http://localhost:8000/v1  # Your AI Gateway endpoint
export CYPHER_API_KEY=dummy  # AI Gateway handles auth

# Run stress test
PROJECT_NAME=${1:-ai-gateway-mcp}

echo "Running stress test with:"
echo "  Provider: $CYPHER_PROVIDER (via AI Gateway)"
echo "  Model: $CYPHER_MODEL"
echo "  Endpoint: $CYPHER_ENDPOINT"
echo "  Project: $PROJECT_NAME"
echo ""

uv run python stress_test.py "$PROJECT_NAME"
