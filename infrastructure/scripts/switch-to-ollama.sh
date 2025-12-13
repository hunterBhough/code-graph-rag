#!/bin/bash
# Switch weavr back to direct Ollama connection

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
    echo ""
}

CODE_GRAPH_DIR="/Users/hunter/code/ai_agency/vendor/weavr"
ENV_FILE="$CODE_GRAPH_DIR/.env"

print_header "Switch to Direct Ollama"

# Backup current .env
echo -e "${BLUE}Backing up current .env...${NC}"
cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
echo -e "${GREEN}✅ Backup created${NC}"

# Update .env file
echo ""
echo -e "${BLUE}Updating configuration...${NC}"

sed -i '' 's/^ORCHESTRATOR_PROVIDER=.*/ORCHESTRATOR_PROVIDER=ollama/' "$ENV_FILE"
sed -i '' 's/^ORCHESTRATOR_MODEL=.*/ORCHESTRATOR_MODEL=llama3.2/' "$ENV_FILE"
sed -i '' 's|^ORCHESTRATOR_ENDPOINT=.*|ORCHESTRATOR_ENDPOINT=http://localhost:11434/v1|' "$ENV_FILE"

# Remove API key line if present
sed -i '' '/^ORCHESTRATOR_API_KEY=/d' "$ENV_FILE"

sed -i '' 's/^CYPHER_PROVIDER=.*/CYPHER_PROVIDER=ollama/' "$ENV_FILE"
sed -i '' 's/^CYPHER_MODEL=.*/CYPHER_MODEL=qwen2.5-coder:7b/' "$ENV_FILE"
sed -i '' 's|^CYPHER_ENDPOINT=.*|CYPHER_ENDPOINT=http://localhost:11434/v1|' "$ENV_FILE"

# Remove API key line if present
sed -i '' '/^CYPHER_API_KEY=/d' "$ENV_FILE"

echo -e "${GREEN}✅ Configuration updated${NC}"

# Show current config
print_header "Current Configuration"
echo "Provider: ollama (direct connection)"
echo "Orchestrator Model: llama3.2"
echo "Cypher Model: qwen2.5-coder:7b"
echo "Endpoint: http://localhost:11434/v1"
echo ""
echo -e "${YELLOW}Note:${NC} This bypasses AI Gateway routing"

print_header "Next Steps"
echo "Test direct Ollama:"
echo "  cd $CODE_GRAPH_DIR"
echo "  source venv/bin/activate"
echo '  echo "Show me all classes" | python -m weavr.main'
echo ""
echo -e "${GREEN}✅ Switched to direct Ollama${NC}"
