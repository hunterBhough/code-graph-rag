#!/bin/bash
# Monitor AI Gateway usage and performance for code-graph-rag

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

# Check if AI Gateway is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}❌ AI Gateway is not running${NC}"
    exit 1
fi

print_header "AI Gateway Monitor"

# Health status
echo -e "${BLUE}Health Status:${NC}"
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""

# Usage statistics
echo -e "${BLUE}Usage Statistics:${NC}"
curl -s http://localhost:8000/usage | python3 -m json.tool
echo ""

# Available models
echo -e "${BLUE}Available Models:${NC}"
curl -s http://localhost:8000/models | python3 -m json.tool
echo ""

# Recent logs
print_header "Recent Activity (last 20 lines)"
echo -e "${BLUE}AI Gateway HTTP Logs:${NC}"
tail -20 ~/Library/Logs/ai-gateway-http.log
echo ""

# Check for errors
ERROR_COUNT=$(tail -100 ~/Library/Logs/ai-gateway-http-error.log 2>/dev/null | wc -l | tr -d ' ')
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}Recent Errors (last 10):${NC}"
    tail -10 ~/Library/Logs/ai-gateway-http-error.log
    echo ""
fi

print_header "Quick Commands"
echo "View live logs:    tail -f ~/Library/Logs/ai-gateway-http.log"
echo "Service status:    cd /Users/hunter/code/ai_agency/shared/mcp-servers/ai-gateway-mcp && ./scripts/manage-service.sh status"
echo "Restart service:   cd /Users/hunter/code/ai_agency/shared/mcp-servers/ai-gateway-mcp && ./scripts/manage-service.sh restart"
echo "Test integration:  ./utils/test-ai-gateway.sh"
