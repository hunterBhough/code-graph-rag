# CLAUDE.md

This file provides guidance to Claude Code when working with code-graph-rag and its infrastructure.

## Repository Overview

Code-graph-rag is a graph-based RAG system that analyzes codebases using Tree-sitter, builds knowledge graphs in Memgraph, and enables natural language querying of code structure and relationships.

**Key capabilities**:
- Multi-language codebase analysis (Python, TypeScript, JavaScript, Go, Rust, etc.)
- Knowledge graph storage in Memgraph
- Natural language code querying via MCP server
- Semantic code search using UniXcoder embeddings

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

### Database Naming

- Project-level: `codegraph_<project-name>`
- Group-level: `codegraph_<group-name>`

All databases are stored in Memgraph (accessible at localhost:7687, Lab UI at localhost:3000).

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
# Activate virtual environment
source venv/bin/activate

# Start server
python -m mcp_server.server
```

### Testing Code-Graph Functionality

```bash
# Run tests
make test

# Run specific test
pytest tests/test_infrastructure.py
```

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

4. **Check Memgraph**
   ```
   USE DATABASE codegraph_test-project;
   MATCH (n) RETURN count(n);
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
