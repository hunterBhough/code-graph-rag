# Codebase Intelligence - Shared Memgraph Infrastructure

This docker-compose stack provides a shared Memgraph instance for all codebase intelligence tools.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Memgraph Instance (codebase-intelligence-memgraph)         │
│                                                              │
│  Multiple isolated databases (one per project):             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │  DB: "project-a"    │  │  DB: "project-b"    │  ...     │
│  │                     │  │                     │          │
│  │  • Code graph nodes │  │  • Code graph nodes │          │
│  │  • qualified_name   │  │  • qualified_name   │          │
│  │  • Relationships    │  │  • Relationships    │          │
│  └─────────────────────┘  └─────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
         ↑                            ↑
         │                            │
    code-graph-rag              vector-search-mcp
    Creates graph               Queries for node IDs
```

## Services

### memgraph
- **Image**: memgraph/memgraph-mage (includes MAGE algorithms)
- **Container**: `codebase-intelligence-memgraph`
- **Ports**:
  - `7687`: Bolt protocol (for direct queries)
  - `7444`: HTTP API (for REST queries)
- **Data**: Persisted in named volume `codebase-intelligence-memgraph-data`

### lab
- **Image**: memgraph/lab (web UI for queries and visualization)
- **Container**: `codebase-intelligence-lab`
- **Port**: `3000`
- **Access**: http://localhost:3000

## Tools Using This Instance

### 1. code-graph-rag
**Purpose**: Structural code analysis with graph relationships

**What it does**:
- Indexes codebases and creates graph nodes for functions, classes, methods
- Sets `qualified_name` property on each node (e.g., `project.module.Class.method`)
- Creates relationships: calls, imports, inheritance, etc.
- Stores in database named after the project

**Database creation**: Automatic (creates DB on first index)

### 2. vector-search-mcp
**Purpose**: Semantic code search with graph node linkage

**What it does**:
- Performs semantic search on indexed codebases
- During indexing, queries Memgraph to find node IDs by qualified name
- Stores node IDs alongside vector embeddings
- Returns node IDs in search results for downstream graph queries

**Database usage**: Queries existing databases created by code-graph-rag

### 3. docwell (future)
**Purpose**: Document search with knowledge graph integration

## Usage

### Start Services

```bash
cd ~/code/ai_agency/shared/mcp-servers/code-graph-rag
docker compose up -d
```

### Stop Services

```bash
docker compose down
```

### View Logs

```bash
docker compose logs -f memgraph
docker compose logs -f lab
```

### Check Status

```bash
docker ps | grep codebase-intelligence
```

### Access Memgraph Lab

Open http://localhost:3000 in your browser to:
- Run Cypher queries
- Visualize the graph
- Explore databases and relationships

## Data Persistence

Memgraph data is persisted in a Docker volume:
- **Volume name**: `codebase-intelligence-memgraph-data`
- **Location**: Managed by Docker

### Backup Data

```bash
docker run --rm -v codebase-intelligence-memgraph-data:/data -v $(pwd):/backup alpine tar czf /backup/memgraph-backup.tar.gz /data
```

### Restore Data

```bash
docker run --rm -v codebase-intelligence-memgraph-data:/data -v $(pwd):/backup alpine tar xzf /backup/memgraph-backup.tar.gz -C /
```

### Clear All Data

⚠️ **Warning**: This deletes all databases and relationships!

```bash
docker compose down -v
```

## Project Database Naming

Each indexed project gets its own isolated database in Memgraph:

| Tool | Config | Database Name |
|------|--------|--------------|
| code-graph-rag | Project name from config | e.g., `vector-search-mcp` |
| vector-search-mcp | `config/integrations.json` → `projectName` | Must match code-graph-rag |

**Important**: Both tools must use the **same project name** to share data!

## Example Workflow

### 1. Index a project with code-graph-rag

```bash
# code-graph-rag creates database "my-project" with graph nodes
code-graph-rag index /path/to/my-project --name my-project
```

### 2. Configure vector-search-mcp

```json
// config/integrations.json
{
  "memgraph": {
    "enabled": true,
    "projectName": "my-project"  // Match code-graph-rag!
  }
}
```

### 3. Index with vector-search-mcp

```bash
# vector-search queries "my-project" database for node IDs
./init-project-search.sh /path/to/my-project
```

### 4. Search and get node IDs

```javascript
// Search returns results with node IDs
{
  "filePath": "src/auth.ts",
  "content": "function login() { ... }",
  "memgraph_node_id": 12345,
  "graph_query_available": true
}
```

### 5. Query relationships with code-graph-rag

```bash
# Use node ID 12345 to explore call graph
code-graph-rag query --node-id 12345 --relationship calls
```

## Troubleshooting

### Memgraph not responding

```bash
# Check if containers are running
docker ps | grep codebase-intelligence

# Restart services
docker compose restart
```

### Cannot connect to HTTP API (port 7444)

```bash
# Check port mapping
docker port codebase-intelligence-memgraph

# Should show: 7444/tcp -> 0.0.0.0:7444
```

### Database not found

```bash
# Connect to Memgraph and list databases
docker exec -it codebase-intelligence-memgraph mgconsole

# In mgconsole:
SHOW DATABASES;
```

### Clear specific database

```cypher
// In Memgraph Lab (http://localhost:3000)
USE DATABASE "my-project";
MATCH (n) DETACH DELETE n;
```

## Environment Variables

Create `.env` file in the same directory as docker-compose.yaml:

```bash
# Memgraph ports
MEMGRAPH_PORT=7687
MEMGRAPH_HTTP_PORT=7444

# Lab port
LAB_PORT=3000

# Memgraph logging
MEMGRAPH_LOG_LEVEL=WARNING
```

## Migrations

If you have existing containers from the old "code-graph-rag" naming:

### Option 1: Recreate (loses data)

```bash
cd ~/code/ai_agency/shared/mcp-servers/code-graph-rag
docker compose down
docker compose up -d
```

### Option 2: Rename (preserves data)

```bash
# Stop old containers
docker stop code-graph-rag-memgraph-1 code-graph-rag-lab-1

# Rename containers
docker rename code-graph-rag-memgraph-1 codebase-intelligence-memgraph
docker rename code-graph-rag-lab-1 codebase-intelligence-lab

# Start with new compose
docker compose up -d
```

## References

- [Memgraph Documentation](https://memgraph.com/docs)
- [Memgraph Lab Guide](https://memgraph.com/docs/memgraph-lab)
- [Cypher Query Language](https://memgraph.com/docs/cypher-manual)
