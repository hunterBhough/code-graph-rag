#!/opt/homebrew/bin/bash
# Master script to index all projects with code-graph-rag and vector-search-mcp
# Created: 2025-12-02
# Requires bash 4+ for associative arrays

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_header() { echo -e "${CYAN}═══════════════════════════════════════════${NC}"; echo -e "${CYAN}$1${NC}"; echo -e "${CYAN}═══════════════════════════════════════════${NC}"; }

# Get script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CODE_GRAPH_INIT="$REPO_ROOT/init-project-graph.sh"
VECTOR_SEARCH_INIT="/Users/hunter/code/ai_agency/shared/mcp-servers/seekr/init-project-search.sh"

# Define all projects with their paths and groups
declare -A PROJECTS=(
    # MCP Servers group
    ["code-graph-rag"]="/Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag:mcp-servers"
    ["ai-gateway-mcp"]="/Users/hunter/code/ai_agency/shared/mcp-servers/ai-gateway-mcp:mcp-servers"
    ["conversational-memory-mcp"]="/Users/hunter/code/ai_agency/shared/mcp-servers/conversational-memory-mcp:mcp-servers"
    ["mcp-service-wrappers"]="/Users/hunter/code/ai_agency/shared/mcp-servers/mcp-service-wrappers:mcp-servers"
    ["seekr"]="/Users/hunter/code/ai_agency/shared/mcp-servers/seekr:mcp-servers"

    # Dashboard group
    ["claude-topology-designer"]="/Users/hunter/code/ai_agency/shared/dashboard/claude-topology-designer:dashboard"
    ["remote-ai-control"]="/Users/hunter/code/ai_agency/shared/dashboard/remote-ai-control:dashboard"

    # Brain projects
    ["mastermind"]="/Users/hunter/code/ai_agency/brain/mastermind:brain"

    # General projects
    ["etsy-scripts"]="/Users/hunter/code/ai_agency/projects/etsy-scripts:projects"
    ["bastion"]="/Users/hunter/code/ai_agency/projects/bastion:projects"
    ["schoolscraper"]="/Users/hunter/code/ai_agency/projects/schoolscraper:projects"

    # Bible vault projects
    ["obsidian-study-bible-cli"]="/Users/hunter/code/ai_agency/projects/bible-vault/obsidian-study-bible-cli:bible-vault"
    ["obsidian-study-bible-infrastructure"]="/Users/hunter/code/ai_agency/projects/bible-vault/obsidian-study-bible-infrastructure:bible-vault"
    ["obsidian-study-bible-infrastructure-serverless"]="/Users/hunter/code/ai_agency/projects/bible-vault/obsidian-study-bible-infrastructure-serverless:bible-vault"
    ["obsidian-study-bible-marketing"]="/Users/hunter/code/ai_agency/projects/bible-vault/obsidian-study-bible-marketing:bible-vault"
    ["obsidian-study-bible-scraper"]="/Users/hunter/code/ai_agency/projects/bible-vault/obsidian-study-bible-scraper:bible-vault"
    ["obsidian-study-bible-website"]="/Users/hunter/code/ai_agency/projects/bible-vault/obsidian-study-bible-website:bible-vault"

    # Shared scripts
    ["scripts"]="/Users/hunter/code/ai_agency/shared/scripts:shared"
)

# Check dependencies
check_dependencies() {
    log_header "Checking Dependencies"

    if [ ! -f "$CODE_GRAPH_INIT" ]; then
        log_error "code-graph-rag init script not found: $CODE_GRAPH_INIT"
        exit 1
    fi
    log_success "Found code-graph-rag init script"

    if [ ! -f "$VECTOR_SEARCH_INIT" ]; then
        log_error "vector-search-mcp init script not found: $VECTOR_SEARCH_INIT"
        exit 1
    fi
    log_success "Found vector-search-mcp init script"

    echo ""
}

# Index a single project
index_project() {
    local name="$1"
    local path_and_group="$2"
    local path="${path_and_group%:*}"
    local group="${path_and_group#*:}"

    log_header "Indexing: $name"

    # Check if project exists
    if [ ! -d "$path" ]; then
        log_warning "Project directory not found: $path (skipping)"
        return 1
    fi

    # Check if it's a git repo
    if [ ! -d "$path/.git" ]; then
        log_warning "Not a git repository: $path (skipping)"
        return 1
    fi

    log "Path: $path"
    log "Group: $group"
    echo ""

    # Index with code-graph-rag
    log "📊 Initializing code-graph-rag..."
    if "$CODE_GRAPH_INIT" "$path" --group "$group" --no-hook; then
        log_success "Code-graph initialized"
    else
        log_error "Code-graph initialization failed"
        return 1
    fi

    echo ""

    # Index with vector-search-mcp
    log "🔍 Initializing vector-search-mcp..."
    if "$VECTOR_SEARCH_INIT" "$path" --group "$group" --no-hook; then
        log_success "Vector-search initialized"
    else
        log_error "Vector-search initialization failed"
        return 1
    fi

    echo ""
    log_success "Project '$name' indexed successfully!"
    echo ""
    echo ""

    return 0
}

# Main execution
main() {
    local start_time=$(date +%s)
    local total=${#PROJECTS[@]}
    local success=0
    local failed=0
    local skipped=0

    log_header "🚀 Mass Project Indexing"
    log "Projects to index: $total"
    echo ""

    check_dependencies

    # Index all projects
    for name in "${!PROJECTS[@]}"; do
        if index_project "$name" "${PROJECTS[$name]}"; then
            ((success++))
        else
            if [ ! -d "${PROJECTS[$name]%:*}" ] || [ ! -d "${PROJECTS[$name]%:*}/.git" ]; then
                ((skipped++))
            else
                ((failed++))
            fi
        fi
    done

    # Summary
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))

    echo ""
    log_header "📊 Indexing Summary"
    echo ""
    log "Total projects: $total"
    log_success "Successfully indexed: $success"
    if [ $failed -gt 0 ]; then
        log_error "Failed: $failed"
    fi
    if [ $skipped -gt 0 ]; then
        log_warning "Skipped: $skipped"
    fi
    log "Duration: ${minutes}m ${seconds}s"
    echo ""

    if [ $failed -eq 0 ]; then
        log_success "🎉 All projects indexed successfully!"
    else
        log_warning "⚠️ Some projects had errors. Check the output above."
    fi
    echo ""
}

# Parse arguments
REINDEX_ALL=false
if [ "$1" == "--reindex" ]; then
    REINDEX_ALL=true
    log_warning "Re-indexing all projects (this will reinitialize existing projects)"
fi

main
