# Code-Graph Infrastructure

This document describes the infrastructure setup for deploying code-graph-rag across multiple projects with automated updates.

## Overview

The code-graph infrastructure provides:
- **Project-level graphs**: Individual knowledge graphs for each codebase
- **Group-level graphs**: Shared graphs across related projects (e.g., all MCP servers)
- **Automated updates**: Git post-commit hooks trigger background graph updates
- **Centralized logging**: Group-level logs stored centrally, project logs stored locally

## Architecture

```
code-graph-rag/
├── init-project-graph.sh          # Initialize code-graph for a project
├── infrastructure/
│   ├── registry/
│   │   └── projects.toon          # Registry of initialized projects
│   └── logs/
│       ├── mcp-servers.log        # Group-level log (centralized)
│       └── brain.log              # Another group log
└── venv/                          # Python virtual environment

project/
├── .codebase-intelligence/
│   └── code-graph/
│       ├── update.sh              # Project-specific update script
│       ├── update.log             # Local update log
│       ├── ignore                 # Project-specific exclusions
│       └── logs/
│           ├── project-name.log   # Project-level log
│           └── group-name.log     # Symlink to centralized log
└── .git/hooks/
    └── post-commit                # Triggers update.sh after commits
```

## Database Naming Convention

All Memgraph databases follow the pattern `codegraph_<name>`:

- **Project-level**: `codegraph_<project-name>` (e.g., `codegraph_ai-gateway-mcp`)
- **Group-level**: `codegraph_<group-name>` (e.g., `codegraph_mcp-servers`)

## Quick Start

### Initialize a New Project

```bash
# Basic initialization (project-level graph only)
./init-project-graph.sh /path/to/project

# With group graph (shares graph with related projects)
./init-project-graph.sh /path/to/project --group mcp-servers

# Skip git hook installation
./init-project-graph.sh /path/to/project --no-hook
```

### What Gets Installed

1. **Project directory structure**:
   ```
   .codebase-intelligence/code-graph/
   ├── update.sh       # Auto-generated update script
   ├── update.log      # Local log file
   ├── ignore          # Project-specific exclusions
   └── logs/
       └── *.log       # Per-database logs
   ```

2. **Git hook** (unless `--no-hook`):
   ```bash
   .git/hooks/post-commit  # Runs update.sh in background after commits
   ```

3. **Registry entry**: Project added to `infrastructure/registry/projects.toon`

4. **Initial graph**: Code graph built and stored in Memgraph

## Project Groups

Groups allow related projects to share a common knowledge graph. Useful for:
- Understanding cross-project dependencies
- Analyzing architectural patterns across related codebases
- Querying multiple related projects simultaneously

### Defining Groups

Groups are logical collections defined when initializing projects:

```bash
# All MCP servers share the "mcp-servers" group
./init-project-graph.sh ~/code/ai-gateway-mcp --group mcp-servers
./init-project-graph.sh ~/code/vector-search-mcp --group mcp-servers
./init-project-graph.sh ~/code/conversational-memory-mcp --group mcp-servers

# Brain projects share the "brain" group
./init-project-graph.sh ~/code/mastermind --group brain
```

When a project is in a group:
- **Project graph**: `codegraph_<project-name>` (only this project's code)
- **Group graph**: `codegraph_<group-name>` (all projects in the group)

### Group Path Resolution

For group graphs, the parent directory is used:
```
/path/to/mcp-servers/
├── ai-gateway-mcp/        # codegraph_ai-gateway-mcp (project)
├── vector-search-mcp/     #  + codegraph_mcp-servers (group)
└── conversational-memory-mcp/
```

The group graph indexes `/path/to/mcp-servers/` (the parent directory).

## Update Workflow

### Automatic Updates (Post-Commit Hook)

```bash
git add .
git commit -m "Your changes"
# Post-commit hook runs automatically:
# 1. Spawns background process: .codebase-intelligence/code-graph/update.sh
# 2. Updates project graph: codegraph_<project-name>
# 3. Updates group graph: codegraph_<group-name> (if configured)
# 4. Logs to .codebase-intelligence/code-graph/update.log
```

### Manual Updates

```bash
# Update specific project
/path/to/project/.codebase-intelligence/code-graph/update.sh

# View logs
tail -f /path/to/project/.codebase-intelligence/code-graph/update.log
```

## Logging

### Log Locations

1. **Project logs** (local): `<project>/.codebase-intelligence/code-graph/logs/`
   - `<project-name>.log` - Project-level graph updates
   - `<group-name>.log` - Symlink to centralized group log

2. **Centralized logs**: `code-graph-rag/infrastructure/logs/`
   - `<group-name>.log` - Group-level graph updates
   - Shared across all projects in the group

### Log Format

Each update logs:
```
🔄 Code-Graph Update Started: Mon Dec 2 00:15:30 UTC 2025
📊 Updating codegraph_project-name...
✅ codegraph_project-name updated successfully
📊 Updating codegraph_group-name...
✅ codegraph_group-name updated successfully
✅ Code-Graph Update Complete: Mon Dec 2 00:15:45 UTC 2025
```

## Project Registry

The registry tracks all initialized projects at `infrastructure/registry/projects.toon`:

```yaml
projects:
  - name: ai-gateway-mcp
    path: /Users/hunter/code/ai_agency/shared/mcp-servers/ai-gateway-mcp
    group: "mcp-servers"
    databases: [codegraph_ai-gateway-mcp, codegraph_mcp-servers]
    initialized_at: 2025-12-01T20:16:10
```

### Registry Management

- **Automatically updated** by `init-project-graph.sh`
- **Deduplicated** - Old entries for the same path are removed
- **TOON format** - Tab-Organized Object Notation (human-readable, git-friendly)

## Exclusions

### Global Exclusions

Configured in code-graph-rag's internal settings:
- `node_modules/`, `.venv/`, `venv/`, `build/`, `dist/`
- `.git/`, `.next/`, `.cache/`
- Binary files, generated files

### Project-Specific Exclusions

Each project has `.codebase-intelligence/code-graph/ignore`:

```bash
# Exclude codebase intelligence artifacts
.codebase-intelligence/

# Exclude project-specific generated files
generated/
scripts/temp/
```

## Dependencies

### Required

1. **Memgraph** (running via Docker)
   ```bash
   cd code-graph-rag && docker compose up -d
   ```

2. **Python virtual environment** (in code-graph-rag)
   ```bash
   cd code-graph-rag
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Git** (for hooks and repo detection)

### Verify Dependencies

```bash
# Check Memgraph is running
docker ps | grep memgraph

# Check Python environment
code-graph-rag/venv/bin/python --version

# Check code-graph-rag is installed
code-graph-rag/venv/bin/python -m codebase_rag.main --help
```

## Troubleshooting

### Graph not updating

```bash
# Check logs
tail -f <project>/.codebase-intelligence/code-graph/update.log

# Run update manually
<project>/.codebase-intelligence/code-graph/update.sh

# Check Memgraph is running
docker ps | grep memgraph
```

### Missing databases

```bash
# Rebuild from scratch
<project>/.codebase-intelligence/code-graph/update.sh
```

### Hook not running

```bash
# Check hook exists and is executable
ls -la <project>/.git/hooks/post-commit

# Make executable if needed
chmod +x <project>/.git/hooks/post-commit

# Test manually
cd <project>
.git/hooks/post-commit
```

## Advanced Usage

### Viewing Graphs in Memgraph Lab

1. Open http://localhost:3000
2. Connect to Memgraph
3. Select database: `codegraph_<name>`
4. Run Cypher queries:

```cypher
// Find all functions
MATCH (f:Function) RETURN f LIMIT 10;

// Find all classes and their methods
MATCH (c:Class)-[:HAS_METHOD]->(m:Function)
RETURN c.name, collect(m.name);

// Find dependencies
MATCH (f1:Function)-[:CALLS]->(f2:Function)
RETURN f1.name, f2.name;
```

### Switching Between Databases

```bash
# In Memgraph Lab or via CLI
USE DATABASE codegraph_project-name;
USE DATABASE codegraph_group-name;
```

### Cleaning Up Old Projects

```bash
# Remove project entry from registry
# Edit: code-graph-rag/infrastructure/registry/projects.toon

# Drop database in Memgraph
DROP DATABASE codegraph_project-name;
```

## Best Practices

1. **Use groups for related projects** - Easier cross-project analysis
2. **Monitor logs** - Check update logs after commits
3. **Exclude generated code** - Update `.codebase-intelligence/code-graph/ignore`
4. **Keep Memgraph running** - Use Docker Compose for automatic startup
5. **Commit often** - Graphs stay up-to-date automatically

## Migration Notes

This infrastructure setup was migrated from a centralized `codebase-intelligence` system to be co-located with code-graph-rag. Key changes:

- Registry moved: `codebase-intelligence/projects.toon` → `code-graph-rag/infrastructure/registry/projects.toon`
- Logs moved: `codebase-intelligence/code-graph/logs/` → `code-graph-rag/infrastructure/logs/`
- Script paths updated in all project `update.sh` files
- Initialization script: `init-code-graph.sh` → `init-project-graph.sh`
