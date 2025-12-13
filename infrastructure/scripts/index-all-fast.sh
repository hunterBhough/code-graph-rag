#!/opt/homebrew/bin/bash
# Fast batch indexing script - runs all projects in parallel where possible
# Created: 2025-12-02

# Don't exit on error - we want to try all projects
set +e

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
log_header() { echo -e "${CYAN}$1${NC}"; }

# Get script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CODE_GRAPH_INIT="$REPO_ROOT/init-project-graph.sh"
VECTOR_SEARCH_INIT="/Users/hunter/code/ai_agency/shared/mcp-servers/seekr/init-project-search.sh"

# All project paths
PROJECTS=(
    "/Users/hunter/code/ai_agency/shared/mcp-servers/weavr:mcp-servers"
    "/Users/hunter/code/ai_agency/shared/mcp-servers/ai-gateway-mcp:mcp-servers"
    "/Users/hunter/code/ai_agency/shared/mcp-servers/conversational-memory-mcp:mcp-servers"
    "/Users/hunter/code/ai_agency/shared/mcp-servers/mcp-service-wrappers:mcp-servers"
    "/Users/hunter/code/ai_agency/shared/mcp-servers/seekr:mcp-servers"
    "/Users/hunter/code/ai_agency/shared/dashboard/claude-topology-designer:dashboard"
    "/Users/hunter/code/ai_agency/shared/dashboard/remote-ai-control:dashboard"
    "/Users/hunter/code/ai_agency/brain/mastermind:brain"
    "/Users/hunter/code/ai_agency/projects/etsy-scripts:projects"
    "/Users/hunter/code/ai_agency/projects/bastion:projects"
    "/Users/hunter/code/ai_agency/projects/schoolscraper:projects"
    "/Users/hunter/code/ai_agency/projects/bible-vault/obsidian-study-bible-cli:bible-vault"
    "/Users/hunter/code/ai_agency/projects/bible-vault/obsidian-study-bible-infrastructure:bible-vault"
    "/Users/hunter/code/ai_agency/projects/bible-vault/obsidian-study-bible-infrastructure-serverless:bible-vault"
    "/Users/hunter/code/ai_agency/projects/bible-vault/obsidian-study-bible-marketing:bible-vault"
    "/Users/hunter/code/ai_agency/projects/bible-vault/obsidian-study-bible-scraper:bible-vault"
    "/Users/hunter/code/ai_agency/projects/bible-vault/obsidian-study-bible-website:bible-vault"
    "/Users/hunter/code/ai_agency/shared/scripts:shared"
)

log_header "═══════════════════════════════════════════"
log_header "🚀 Fast Batch Indexing - ${#PROJECTS[@]} projects"
log_header "═══════════════════════════════════════════"
echo ""

success=0
failed=0
skipped=0

for project_info in "${PROJECTS[@]}"; do
    path="${project_info%:*}"
    group="${project_info#*:}"
    name="$(basename "$path")"

    log "📦 Indexing: $name"

    # Check if project exists and is a git repo
    if [ ! -d "$path" ]; then
        log_warning "Directory not found: $path (skipping)"
        ((skipped++))
        continue
    fi

    if [ ! -d "$path/.git" ]; then
        log_warning "Not a git repo: $path (skipping)"
        ((skipped++))
        continue
    fi

    # Initialize with weavr
    code_graph_success=false
    if "$CODE_GRAPH_INIT" "$path" --group "$group" --no-hook >/dev/null 2>&1; then
        log_success "Code-graph: $name"
        code_graph_success=true
    else
        log_error "Code-graph failed: $name"
    fi

    # Initialize with vector-search-mcp
    vector_search_success=false
    if "$VECTOR_SEARCH_INIT" "$path" --group "$group" --no-hook >/dev/null 2>&1; then
        log_success "Vector-search: $name"
        vector_search_success=true
    else
        log_error "Vector-search failed: $name"
    fi

    # Count successes and failures
    if $code_graph_success && $vector_search_success; then
        ((success++))
    else
        ((failed++))
    fi
done

echo ""
log_header "═══════════════════════════════════════════"
log_header "📊 Summary"
log_header "═══════════════════════════════════════════"
echo ""
log "Total: ${#PROJECTS[@]}"
log_success "Success: $success"
[ $failed -gt 0 ] && log_error "Failed: $failed"
[ $skipped -gt 0 ] && log_warning "Skipped: $skipped"
echo ""

if [ $failed -eq 0 ]; then
    log_success "🎉 All projects indexed!"
else
    log_warning "⚠️  Some projects had errors"
    exit 1
fi
