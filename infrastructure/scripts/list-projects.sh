#!/bin/bash
# List all code-graph configured projects

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

print_header "Code-Graph Configured Projects"

echo "Searching for configured projects..."
echo ""

FOUND=0

# Search common locations
SEARCH_PATHS=(
    "/Users/hunter/code/ai_agency/shared/mcp-servers"
    "/Users/hunter/code/ai_agency/shared/dashboard"
    "/Users/hunter/code/ai_agency/projects"
    "/Users/hunter/code/ai_agency/brain"
    "/Users/hunter/code/go/src/github.com/hunterBhough"
)

for search_path in "${SEARCH_PATHS[@]}"; do
    if [ ! -d "$search_path" ]; then
        continue
    fi

    while IFS= read -r update_script; do
        PROJECT_DIR="$(dirname "$(dirname "$(dirname "$update_script")")")"
        PROJECT_NAME="$(basename "$PROJECT_DIR")"

        # Extract database info from script
        DB_INFO=$(grep "^DB_PROJECT=" "$update_script" 2>/dev/null | head -1 | cut -d'"' -f2 || echo "Unknown")
        GROUP=$(grep "^GROUP=" "$update_script" 2>/dev/null | head -1 | cut -d'"' -f2 || echo "")

        echo -e "${GREEN}📦 $PROJECT_NAME${NC}"
        echo "   Path: $PROJECT_DIR"
        echo "   DB:   $DB_INFO"
        [ -n "$GROUP" ] && echo "   Group: $GROUP"

        # Check if git hook is installed
        if [ -f "$PROJECT_DIR/.git/hooks/post-commit" ]; then
            echo -e "   Hook: ${GREEN}✅ Installed${NC}"
        else
            echo -e "   Hook: ${YELLOW}⚠️  Missing${NC}"
        fi

        echo ""
        FOUND=$((FOUND + 1))
    done < <(find "$search_path" -maxdepth 3 -path "*/.codebase-intelligence/code-graph/update.sh" 2>/dev/null)
done

if [ "$FOUND" -eq 0 ]; then
    echo "No configured projects found."
    echo ""
    echo "To initialize a project:"
    echo "  ./init-project.sh <path> [group]"
else
    echo "Found $FOUND configured project(s)"
fi

echo ""
