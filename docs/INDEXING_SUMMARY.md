# Project Indexing Summary
**Date**: 2025-12-02
**Systems**: code-graph-rag & vector-search-mcp

## Overview
Successfully indexed **16 projects** with both code-graph-rag (graph-based analysis) and vector-search-mcp (semantic search).

## Exclusions Added
Added the following directories to ignore patterns:
- `/vendor` - Dependency vendors
- `/dist` - Build outputs
- `/research_papers` - Research documents

### Files Modified
- `code-graph-rag/codebase_rag/config.py` (lines 168-185)
- `vector-search-mcp/src/embeddings/provider-manager.ts` (lines 477, 491)

## Projects Indexed

### MCP Servers (Group: mcp-servers)
1. ✅ code-graph-rag
2. ✅ ai-gateway-mcp
3. ✅ conversational-memory-mcp
4. ✅ mcp-service-wrappers
5. ✅ vector-search-mcp

### Dashboard (Group: dashboard)
6. ✅ claude-topology-designer
7. ✅ remote-ai-control

### Brain (Group: brain)
8. ✅ mastermind

### Projects (Group: projects)
9. ✅ etsy-scripts
10. ✅ bastion

### Bible Vault (Group: bible-vault)
11. ✅ obsidian-study-bible-cli
12. ✅ obsidian-study-bible-infrastructure
13. ✅ obsidian-study-bible-infrastructure-serverless
14. ✅ obsidian-study-bible-marketing
15. ✅ obsidian-study-bible-scraper
16. ✅ obsidian-study-bible-website

## Projects Skipped
- ⚠️ schoolscraper - Not a git repository
- ⚠️ scripts - Not a git repository

## Registry Status
- **code-graph-rag registry**: 18 entries
- **vector-search-mcp registry**: 17 entries
- **shared/scripts registry**: Not updated (different format)

All registries are located at:
- `/Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag/infrastructure/registry/projects.toon`
- `/Users/hunter/code/ai_agency/shared/mcp-servers/vector-search-mcp/infrastructure/registry/projects.toon`
- `/Users/hunter/code/ai_agency/shared/scripts/registry/projects.toon`

## Graph Databases Created
Each project has its own graph database in Memgraph:
- **Project databases**: `codegraph_<project-name>` (16 databases)
- **Group databases**:
  - `codegraph_mcp-servers`
  - `codegraph_dashboard`
  - `codegraph_brain`
  - `codegraph_projects`
  - `codegraph_bible-vault`

Access via Memgraph Lab: http://localhost:3000

## Vector Search Indexes
Each project has vector embeddings stored in SQLite databases located at:
`<project>/.codebase-intelligence/vector-search/`

## Scripts Created
Scripts located in `infrastructure/scripts/`:
1. **index-all-projects.sh** - Comprehensive indexing with full output
2. **index-all-fast.sh** - Fast batch indexing with minimal output
3. **cleanup-registries.sh** - Removes duplicate registry entries

## Update Scripts
Each indexed project now has automated update scripts:
- `.codebase-intelligence/code-graph/update.sh` - Updates code graph
- `.codebase-intelligence/vector-search/update.sh` - Updates vector embeddings

Note: Git hooks were NOT installed (--no-hook flag used). To enable automatic updates on commit, run the init scripts again without --no-hook.

## Manual Update Commands
To manually update a specific project:
```bash
# Update code graph
cd /path/to/project
./.codebase-intelligence/code-graph/update.sh

# Update vector search
./.codebase-intelligence/vector-search/update.sh
```

To re-index all projects:
```bash
cd /Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag
./infrastructure/scripts/index-all-fast.sh
```

## Total Processing Time
Approximately 18 minutes for all 16 projects

## Next Steps
1. Consider initializing git repositories for `schoolscraper` and `scripts` if they need indexing
2. Optionally install git hooks for automatic updates (re-run init scripts without --no-hook)
3. Verify graph databases in Memgraph Lab: http://localhost:3000
4. Test semantic search queries via vector-search-mcp MCP server
