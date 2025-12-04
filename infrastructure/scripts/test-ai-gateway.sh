#!/bin/bash
# Test AI Gateway integration with code-graph-rag

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

print_header "AI Gateway Integration Test"

# 1. Check AI Gateway is running
echo -e "${BLUE}1. Checking AI Gateway status...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ AI Gateway is running${NC}"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || true
else
    echo -e "${RED}❌ AI Gateway is not running${NC}"
    exit 1
fi

# 2. Test OpenAI endpoint directly
echo ""
echo -e "${BLUE}2. Testing OpenAI endpoint...${NC}"
RESPONSE=$(curl -s -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"code-graph-orchestrator","messages":[{"role":"user","content":"test"}]}')

if echo "$RESPONSE" | grep -q "choices"; then
    echo -e "${GREEN}✅ OpenAI endpoint working${NC}"
    echo "$RESPONSE" | python3 -m json.tool | head -15
else
    echo -e "${RED}❌ OpenAI endpoint failed${NC}"
    echo "$RESPONSE"
    exit 1
fi

# 3. Check code-graph-rag configuration
echo ""
echo -e "${BLUE}3. Checking code-graph-rag configuration...${NC}"
if grep -q "ORCHESTRATOR_ENDPOINT=http://localhost:8000/v1" "$CODE_GRAPH_DIR/.env"; then
    echo -e "${GREEN}✅ Configured to use AI Gateway${NC}"
else
    echo -e "${YELLOW}⚠️  Not configured for AI Gateway${NC}"
    echo "Run: ./utils/switch-to-ai-gateway.sh"
    exit 1
fi

# 4. Test with sample query
echo ""
echo -e "${BLUE}4. Testing code-graph-rag query...${NC}"
echo ""
cd "$CODE_GRAPH_DIR"
source venv/bin/activate

echo -e "${YELLOW}Running: 'What is this codebase about?'${NC}"
echo ""

if echo "What is this codebase about?" | python -m codebase_rag.main 2>&1 | tee /tmp/cgr-test.log; then
    echo ""
    echo -e "${GREEN}✅ Query completed${NC}"
else
    echo ""
    echo -e "${RED}❌ Query failed${NC}"
    exit 1
fi

# 5. Check AI Gateway usage stats
echo ""
echo -e "${BLUE}5. Checking AI Gateway usage stats...${NC}"
curl -s http://localhost:8000/usage | python3 -m json.tool

print_header "Test Complete"
echo -e "${GREEN}✅ All tests passed!${NC}"
echo ""
echo "The AI Gateway integration is working correctly."
echo ""
echo "View logs:"
echo "  tail -f ~/Library/Logs/ai-gateway-http.log"
