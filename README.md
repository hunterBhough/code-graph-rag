# weavr

MCP server for structured code graph queries using Tree-sitter and Memgraph.

Answer structural questions about codebases: who calls this function, what inherits from that class, what are the circular dependencies. Complements semantic search (seekr) and document search (docwell) with precise relationship analysis.

**Note**: Weavr is the renamed successor to the code-graph-rag project, now with a more descriptive name reflecting its core purpose of weaving connections between code structures.

## Quick Start

### 1. Install

```bash
uv sync
```

### 2. Start Memgraph

```bash
docker compose up -d
```

### 3. Index Your Project

```bash
uv run weavr index
```

### 4. Query Interactively

```bash
uv run weavr chat "Who calls UserService.create_user?"
```

## Key Capabilities

**Structural Queries:**
- Find function callers: "Who calls this function?"
- Map class hierarchies: "Show inheritance tree for BaseModel"
- Trace dependencies: "What modules does auth.py depend on?"
- Analyze call graphs: "Show call stack for authenticate()"
- Detect patterns: "Find functions with >5 callers"

**Multi-Language Support:**
- Python, JavaScript, TypeScript
- Go, Rust, Java, Scala
- C, C++, Lua

**Multiple Interfaces:**
- MCP server for Claude Desktop
- HTTP API for web integrations
- CLI for interactive exploration

## Usage Examples

### CLI Queries

```bash
# Find callers
uv run weavr chat "Who calls verify_token?"

# Class hierarchy
uv run weavr chat "Show inheritance for BaseModel"

# Dependencies
uv run weavr chat "What does auth.py import?"

# Call graph
uv run weavr chat "Show call stack for login()"
```

### MCP Server

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "weavr": {
      "command": "uv",
      "args": ["run", "weavr", "mcp"],
      "cwd": "/path/to/weavr"
    }
  }
}
```

Available tools:
- `index_repository` - Parse and ingest codebase
- `query_code_graph` - Natural language structural queries
- `query_callers` - Find function callers
- `query_hierarchy` - Class inheritance trees
- `query_dependencies` - Module dependencies
- `query_call_graph` - Full call stacks
- `get_code_snippet` - Retrieve source by qualified name

### HTTP API

```bash
# Start server
uv run weavr http

# Query via POST
curl -X POST http://localhost:8000/api/tools/query_callers \
  -H "Content-Type: application/json" \
  -d '{"params": {"qualified_name": "app.services.UserService.create_user"}}'
```

## Project Structure

```
weavr/
├── main.py              # CLI entry point
├── mcp/                 # MCP server & tools
├── http/                # HTTP server
├── parsers/             # Language-specific parsers
├── services/            # Core services (graph, LLM)
├── tools/               # Query tools
└── tests/               # Test suite
```

## Requirements

- Python 3.12+
- Docker (for Memgraph)
- UV package manager

## Configuration

Create `.env` file:

```bash
# Memgraph
MEMGRAPH_HOST=localhost
MEMGRAPH_PORT=7687

# LLM for queries (optional)
ORCHESTRATOR_PROVIDER=anthropic
ORCHESTRATOR_MODEL=claude-sonnet-4-5-20250929
ORCHESTRATOR_API_KEY=sk-...

CYPHER_PROVIDER=anthropic
CYPHER_MODEL=claude-sonnet-4-5-20250929
CYPHER_API_KEY=sk-...
```

Supported providers: `anthropic`, `openai`, `google` (Vertex AI), `ollama`

## Documentation

- `docs/VISION.md` - Purpose, philosophy, relationships
- `docs/ARCHITECTURE.md` - System design, graph schema, tools
- `CLAUDE.md` - AI assistant guidance

## Relationship to Other Tools

**seekr** - Semantic code search via vector embeddings
**docwell** - Documentation search via vector embeddings
**weavr** - Structural relationship queries via knowledge graph

Use together for comprehensive codebase understanding.

## Attribution

Weavr is the renamed successor to the original [code-graph-rag](https://github.com/vitali87/code-graph-rag) project. The new name "weavr" better reflects the project's core purpose of weaving connections between code structures through structural analysis.

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check

# Type check
uv run mypy weavr

# Format
uv run ruff format
```

## License

MIT
