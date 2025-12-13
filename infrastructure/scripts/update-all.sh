#!/bin/bash
# Update all code-graph configured projects

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
    echo ""
}

print_header "Update All Code-Graph Projects"

# Usage
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: $0 [--parallel]"
    echo ""
    echo "Options:"
    echo "  --parallel    Run updates in parallel (faster but more resource intensive)"
    echo ""
    echo "This script finds all projects with .codegraph-update.sh and runs them."
    echo ""
    exit 0
fi

PARALLEL=false
if [ "$1" == "--parallel" ]; then
    PARALLEL=true
    log "Running in parallel mode"
fi

# Search paths
SEARCH_PATHS=(
    "/Users/hunter/code/ai_agency/shared/mcp-servers"
    "/Users/hunter/code/ai_agency/shared/dashboard"
    "/Users/hunter/code/ai_agency/projects"
    "/Users/hunter/code/ai_agency/brain"
    "/Users/hunter/code/go/src/github.com/hunterBhough"
)

FOUND=0
SUCCESS=0
FAILED=0

# Find and update all projects
for search_path in "${SEARCH_PATHS[@]}"; do
    if [ ! -d "$search_path" ]; then
        continue
    fi

    while IFS= read -r update_script; do
        PROJECT_DIR="$(dirname "$update_script")"
        PROJECT_NAME="$(basename "$PROJECT_DIR")"

        FOUND=$((FOUND + 1))

        echo ""
        log "Updating: $PROJECT_NAME"
        log "Path: $PROJECT_DIR"

        if [ "$PARALLEL" = true ]; then
            # Run in background
            (
                cd "$PROJECT_DIR"
                if "$update_script"; then
                    log_success "$PROJECT_NAME updated"
                else
                    log_error "$PROJECT_NAME failed"
                fi
            ) &
        else
            # Run sequentially
            if (cd "$PROJECT_DIR" && "$update_script"); then
                log_success "$PROJECT_NAME updated"
                SUCCESS=$((SUCCESS + 1))
            else
                log_error "$PROJECT_NAME failed"
                FAILED=$((FAILED + 1))
            fi
        fi

    done < <(find "$search_path" -maxdepth 3 -path "*/.codebase-intelligence/code-graph/update.sh" 2>/dev/null)
done

# Wait for parallel jobs
if [ "$PARALLEL" = true ]; then
    log "Waiting for parallel updates to complete..."
    wait
    log_success "All parallel updates completed"
fi

# Summary
print_header "Update Summary"

echo "Projects found: $FOUND"

if [ "$PARALLEL" = false ]; then
    echo "Successful: $SUCCESS"
    echo "Failed: $FAILED"
fi

echo ""
echo "View detailed logs:"
echo "  tail -f /Users/hunter/code/ai_agency/vendor/weavr/logs/*-updates.log"
echo ""
