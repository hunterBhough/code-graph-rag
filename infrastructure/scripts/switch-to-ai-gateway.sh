#!/bin/bash
# Switch code-graph-rag to use AI Gateway for intelligent routing

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
    echo ""
}

CODE_GRAPH_DIR="/Users/hunter/code/ai_agency/vendor/code-graph-rag"
ENV_FILE="$CODE_GRAPH_DIR/.env"

print_header "Switch to AI Gateway"

# Check if AI Gateway HTTP server is running
echo -e "${BLUE}Checking AI Gateway status...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ AI Gateway is running${NC}"
else
    echo -e "${RED}❌ AI Gateway is not running${NC}"
    echo ""
    echo "Start it with:"
    echo "  cd /Users/hunter/code/ai_agency/shared/mcp-servers/ai-gateway-mcp"
    echo "  ./scripts/manage-service.sh start"
    exit 1
fi

# Backup current .env
echo ""
echo -e "${BLUE}Backing up current .env...${NC}"
cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
echo -e "${GREEN}✅ Backup created${NC}"

# Update .env file
echo ""
echo -e "${BLUE}Updating configuration...${NC}"

# Use sed to update the configuration
sed -i '' 's/^ORCHESTRATOR_PROVIDER=.*/ORCHESTRATOR_PROVIDER=openai/' "$ENV_FILE"
sed -i '' 's/^ORCHESTRATOR_MODEL=.*/ORCHESTRATOR_MODEL=code-graph-orchestrator/' "$ENV_FILE"
sed -i '' 's|^ORCHESTRATOR_ENDPOINT=.*|ORCHESTRATOR_ENDPOINT=http://localhost:8000/v1|' "$ENV_FILE"

# Add API key if not present
if ! grep -q "^ORCHESTRATOR_API_KEY=" "$ENV_FILE"; then
    sed -i '' '/^ORCHESTRATOR_ENDPOINT=/a\
ORCHESTRATOR_API_KEY=dummy
' "$ENV_FILE"
fi

sed -i '' 's/^CYPHER_PROVIDER=.*/CYPHER_PROVIDER=openai/' "$ENV_FILE"
sed -i '' 's/^CYPHER_MODEL=.*/CYPHER_MODEL=code-graph-cypher/' "$ENV_FILE"
sed -i '' 's|^CYPHER_ENDPOINT=.*|CYPHER_ENDPOINT=http://localhost:8000/v1|' "$ENV_FILE"

# Add API key if not present
if ! grep -q "^CYPHER_API_KEY=" "$ENV_FILE"; then
    sed -i '' '/^CYPHER_ENDPOINT=/a\
CYPHER_API_KEY=dummy
' "$ENV_FILE"
fi

echo -e "${GREEN}✅ Configuration updated${NC}"

# Show current config
print_header "Current Configuration"
echo "Provider: openai (AI Gateway wrapper)"
echo "Orchestrator Model: code-graph-orchestrator"
echo "Cypher Model: code-graph-cypher"
echo "Endpoint: http://localhost:8000/v1"
echo ""
echo -e "${YELLOW}Benefits:${NC}"
echo "  • Intelligent routing to optimal models"
echo "  • Load balancing across Mac and Server"
echo "  • Usage tracking and analytics"
echo "  • 100% free (local models only)"

print_header "Next Steps"
echo "Test the integration:"
echo "  cd $CODE_GRAPH_DIR"
echo "  source venv/bin/activate"
echo '  echo "Show me all classes" | python -m codebase_rag.main'
echo ""
echo "Monitor AI Gateway:"
echo "  curl http://localhost:8000/usage | python3 -m json.tool"
echo ""
echo -e "${GREEN}✅ Ready to use AI Gateway!${NC}"
