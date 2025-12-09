# CLAUDE.md

This file provides guidance to Claude Code when working with code-graph-rag and its infrastructure.

## Repository Overview

Code-graph-rag is a **specialized graph query engine** that analyzes codebases using Tree-sitter, builds knowledge graphs in Memgraph, and enables structural relationship queries for precise codebase understanding.

**Key capabilities**:
- Multi-language codebase analysis (Python, TypeScript, JavaScript, Go, Rust, etc.)
- Knowledge graph storage in Memgraph
- Natural language code querying via MCP server (translates to Cypher)
- Structural queries: function callers, class hierarchies, dependencies, call graphs
- **Focus**: Graph-based structural relationships (NOT semantic/keyword search)

**Tool Separation**:
- **code-graph-rag** (this tool): Structural relationships and graph queries
- **vector-search-mcp**: Semantic code search and fuzzy matching
- **mcp-ragdocs**: Documentation search

## Infrastructure

This repository includes infrastructure for deploying code-graph across multiple projects:

### Quick Setup

```bash
# Initialize code-graph for a project
./init-project-graph.sh /path/to/project

# With group graph (for related projects)
./init-project-graph.sh /path/to/project --group mcp-servers

# Skip git hook
./init-project-graph.sh /path/to/project --no-hook
```

### What Gets Installed

- `.codebase-intelligence/code-graph/` in the target project
- Auto-generated `update.sh` script with paths to this repo
- Post-commit hook for automatic graph updates
- Entry in `infrastructure/registry/projects.toon`

### Project Structure

```
code-graph-rag/
├── init-project-graph.sh       # Initialize projects (NEW)
├── infrastructure/             # Infrastructure files (NEW)
│   ├── registry/
│   │   └── projects.toon      # Initialized projects registry
│   └── logs/                  # Centralized group-level logs
├── codebase_rag/              # Main Python package
├── mcp_server/                # MCP server implementation
├── venv/                      # Python virtual environment
└── docs/
    ├── INFRASTRUCTURE.md      # Infrastructure documentation (NEW)
    └── claude-code-setup.md   # MCP server setup
```

### Project Isolation

Code-graph-rag uses **Project-based isolation** instead of separate databases:
- All projects share the default Memgraph database (localhost:7687, Lab UI at localhost:3000)
- Each project gets a `Project` node (e.g., `Project {name: "my-project"}`)
- All code nodes have `CONTAINS` relationships from their Project node
- Queries filter by Project using relationship patterns

This approach works with Memgraph Community Edition (no enterprise license required).

## Common Tasks

### Initialize a New Project

```bash
./init-project-graph.sh /path/to/project [--group <name>] [--no-hook]
```

### Update Documentation

When updating infrastructure or adding features:
1. Update `docs/INFRASTRUCTURE.md` - Infrastructure details
2. Update this `CLAUDE.md` - Claude Code guidance
3. Update `README.md` - User-facing documentation

### View Project Registry

```bash
cat infrastructure/registry/projects.toon
```

### Check Group Logs

```bash
tail -f infrastructure/logs/<group-name>.log
```

### Troubleshoot Updates

```bash
# Check project update logs
tail -f /path/to/project/.codebase-intelligence/code-graph/update.log

# Run manual update
/path/to/project/.codebase-intelligence/code-graph/update.sh

# Check Memgraph
docker ps | grep memgraph
```

## Development Workflow

### Running the MCP Server

```bash
# Start server (uv handles venv automatically)
uv run -m mcp_server.server
```

### Testing Code-Graph Functionality

```bash
# Run tests
make test

# Run specific test
uv run pytest tests/test_infrastructure.py

# Run stress tests
uv run stress_test.py

# Run project isolation test
uv run test_project_isolation.py
```

### Project-Based Isolation (Community Edition)

Code-graph-rag uses **Project-based isolation** via `CONTAINS` relationships. This approach works with Memgraph Community Edition (no enterprise license required).

**How it works:**
1. Each indexed project creates a `Project` node with `name = project_name`
2. All code nodes (Module, Class, Function, Method, etc.) automatically get a `CONTAINS` relationship from their Project
3. Queries can filter by Project using relationship patterns

```python
from codebase_rag.services.graph_service import MemgraphIngestor

# Index project A
with MemgraphIngestor(
    host='localhost',
    port=7687,
    project_name='my-project-a'  # Enables Project isolation
) as ingestor:
    # All nodes will automatically get: (Project {name: 'my-project-a'})-[:CONTAINS]->(node)
    ingestor.ensure_node_batch("Module", {"qualified_name": "my-project-a.module"})
    ingestor.flush_all()

# Query only project A's code
with MemgraphIngestor(host='localhost', port=7687) as ingestor:
    results = ingestor.fetch_all("""
        MATCH (p:Project {name: 'my-project-a'})-[:CONTAINS*]->(f:Function)
        RETURN f.qualified_name
    """)
```

**Benefits over database switching:**
- ✅ Works with Community Edition (free)
- ✅ Single database, simpler deployment
- ✅ Cross-project queries possible when needed
- ✅ No `USE DATABASE` enterprise requirement

See `test_project_isolation.py` for a complete example.

### Making Changes to Infrastructure

When modifying `init-project-graph.sh` or infrastructure:

1. **Test on a sample project first**
   ```bash
   mkdir -p /tmp/test-project && cd /tmp/test-project && git init
   /path/to/code-graph-rag/init-project-graph.sh /tmp/test-project
   ```

2. **Verify generated files**
   ```bash
   cat /tmp/test-project/.codebase-intelligence/code-graph/update.sh
   cat infrastructure/registry/projects.toon
   ```

3. **Test update script**
   ```bash
   /tmp/test-project/.codebase-intelligence/code-graph/update.sh
   tail -f /tmp/test-project/.codebase-intelligence/code-graph/update.log
   ```

4. **Check Memgraph** (via Lab UI at http://localhost:3000)
   ```cypher
   // Count nodes for test project
   MATCH (p:Project {name: 'test-project'})-[:CONTAINS]->(n)
   RETURN count(n);
   ```

## Important Paths

- **This repo**: `/Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag`
- **Project registry**: `infrastructure/registry/projects.toon`
- **Group logs**: `infrastructure/logs/`
- **Memgraph**: `localhost:7687` (Lab: `http://localhost:3000`)

## Dependencies

- **Memgraph** - Graph database (via Docker Compose)
- **Python 3.12+** - Runtime
- **Tree-sitter** - Code parsing
- **Docker** - For Memgraph

### Start Dependencies

```bash
# Start Memgraph
docker compose up -d

# Verify
docker ps | grep memgraph
curl -s http://localhost:3000 | grep -q "Memgraph"
```

## Architecture Notes

### Two-Level Graph Hierarchy

1. **Project-level** (`codegraph_<project>`): Single project's code
2. **Group-level** (`codegraph_<group>`): Related projects' code (parent directory)

### Update Flow

```
git commit
  → post-commit hook
    → .codebase-intelligence/code-graph/update.sh
      → Activates venv in this repo
      → Runs codebase_rag.main with --update-graph
      → Updates project graph (codegraph_<project>)
      → Updates group graph (codegraph_<group>) if configured
      → Logs to .codebase-intelligence/code-graph/update.log
```

### Registry Format (TOON)

```yaml
projects:
  - name: project-name
    path: /absolute/path/to/project
    group: "group-name"  # or "" for no group
    databases: [codegraph_project-name, codegraph_group-name]
    initialized_at: 2025-12-01T20:16:10
```

## Edge Case Handling

### Query Tool Edge Cases

**Non-Existent Nodes**: All structural query tools handle missing nodes gracefully:
- Returns clear error message: `"Node not found: <qualified_name>"`
- Suggests checking qualified name spelling or re-indexing the repository
- No crashes or unclear errors

**Large Result Sets**: Automatic truncation prevents overwhelming output:
- Pre-built tools: Truncate at >100 rows, include metadata showing total count
- Expert mode (Cypher): Truncate at >50 rows, include metadata showing total count
- Metadata shows: `row_count`, `total_count`, `truncated` (boolean)

**Empty Results**: When query returns no results:
- Verifies target node exists in graph (provides specific error if not)
- Returns empty results array with clear message if node exists but has no relationships
- Example: "Function exists but has no callers"

**Deep Traversals**: Performance safeguards for graph traversals:
- Max depth limits enforced (e.g., `max_depth=5` for callers, `max_depth=10` for hierarchies)
- Validation errors for out-of-range depths
- Query timeouts prevent runaway queries

**Circular Dependencies**: Class hierarchy tool detects circular inheritance:
- Returns `circular_dependencies` array in metadata
- Continues query execution, doesn't crash
- Includes paths showing circular chains

### Database Edge Cases

**Connection Failures**: Graceful handling of database unavailability:
- Clear error messages indicating Memgraph connection issues
- Suggests checking `docker ps | grep memgraph` and restarting containers
- No data corruption on connection loss

**Missing Projects**: Project isolation queries handle missing projects:
- Validates project exists before executing queries
- Returns clear error if project not found
- Suggests running index_repository if project not indexed

### Performance Edge Cases

**Large Codebases**: Handles codebases with >10K nodes:
- Query performance degrades gracefully (50ms → 100ms for 10K-100K nodes)
- Result truncation ensures response times stay predictable
- Graph traversal depth limits prevent exponential explosion

**Concurrent Queries**: Thread-safe query execution:
- Multiple MCP tools can query simultaneously
- Connection pooling handled by Memgraph client
- No race conditions or data corruption

## Related Documentation

- **Infrastructure Guide**: `docs/INFRASTRUCTURE.md` - Comprehensive infrastructure documentation
- **MCP Setup**: `docs/claude-code-setup.md` - Setting up as MCP server for Claude Code
- **Main README**: `README.md` - User-facing documentation and features

## Migration Context

This infrastructure was recently migrated from a centralized `codebase-intelligence` system to be co-located with code-graph-rag. Key changes:

- Moved from `/shared/scripts/codebase-intelligence/` to `/shared/mcp-servers/code-graph-rag/`
- New location for registry: `infrastructure/registry/projects.toon`
- New location for group logs: `infrastructure/logs/`
- All project `update.sh` scripts updated with new paths
- Initialization script renamed: `init-code-graph.sh` → `init-project-graph.sh`

## Active Technologies
- Python 3.14.2 (requires-python >= 3.12) + pymgclient 1.4.0, loguru 0.7.3, pydantic-settings 2.0.0 (001-fix-db-connection)
- Memgraph graph database (via mgclient connection, host:port 7687) (001-fix-db-connection)
- Python 3.12+ (requires-python >= 3.12) + pymgclient 1.4.0 (Memgraph client), tree-sitter 0.25.0 (AST parsing), mcp 1.21.1+ (MCP protocol), pydantic-ai-slim 0.2.18+ (LLM integration for NL→Cypher), loguru 0.7.3 (logging) (002-graph-query-engine)
- Memgraph Community Edition (graph database at localhost:7687), project-based isolation via CONTAINS relationships (002-graph-query-engine)

## Recent Changes
- 001-fix-db-connection: Added Python 3.14.2 (requires-python >= 3.12) + pymgclient 1.4.0, loguru 0.7.3, pydantic-settings 2.0.0
