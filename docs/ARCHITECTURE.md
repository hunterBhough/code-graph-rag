# Architecture

## System Overview

code-graph-rag is a multi-layer system that parses code, builds knowledge graphs, and exposes query tools via multiple interfaces.

```
┌─────────────────────────────────────────────────────┐
│              Interface Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ MCP      │  │ HTTP     │  │ CLI      │          │
│  │ Server   │  │ Server   │  │ (Typer)  │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
└───────┼────────────┼─────────────┼─────────────────┘
        │            │             │
┌───────┴────────────┴─────────────┴─────────────────┐
│              Tool Registry                          │
│  Query Tools • File Tools • Structural Tools        │
│  (shared across all interfaces)                     │
└───────┬────────────────────────────────────┬────────┘
        │                                    │
┌───────┴──────────────┐          ┌─────────┴─────────┐
│   Service Layer      │          │   Parser Layer    │
│  ┌────────────────┐  │          │  ┌──────────────┐ │
│  │ MemgraphIngestor│ │          │  │ Tree-sitter  │ │
│  │ CypherGenerator │ │          │  │ Parsers      │ │
│  │ LLM Orchestrator│ │          │  │ (Multi-lang) │ │
│  └────────────────┘  │          │  └──────────────┘ │
└──────────┬───────────┘          └─────────┬─────────┘
           │                                │
┌──────────┴────────────────────────────────┴─────────┐
│              Data Layer                             │
│  ┌──────────────┐         ┌──────────────┐          │
│  │  Memgraph    │         │  File System │          │
│  │  (Graph DB)  │         │  (Source)    │          │
│  └──────────────┘         └──────────────┘          │
└─────────────────────────────────────────────────────┘
```

## Core Components

### 1. Interface Layer

**MCP Server** (`codebase_rag/mcp/`)
- Implements Model Context Protocol
- Exposes tools to Claude Desktop
- Async event-driven architecture
- Tool registry shared with other interfaces

**HTTP Server** (`codebase_rag/http/`)
- FastAPI-based REST API
- Health checks and monitoring
- Same tools as MCP, different transport
- CORS-enabled for web integrations

**CLI** (`codebase_rag/main.py`)
- Typer-based command interface
- Interactive chat mode
- Repository indexing commands
- Rich output formatting

### 2. Tool Registry

**MCPToolsRegistry** (`codebase_rag/mcp/tools.py`)
- Single source of truth for all tools
- Shared across MCP, HTTP, CLI
- Metadata includes schemas and handlers
- Lazy initialization of heavy dependencies

**Tool Categories:**

**Query Tools:**
- `query_code_graph` - Natural language queries → Cypher
- `query_callers` - Find function callers
- `query_hierarchy` - Class inheritance trees
- `query_dependencies` - Module dependency analysis
- `query_call_graph` - Full call stack analysis
- `query_expert_mode` - Direct Cypher queries

**File Tools:**
- `get_code_snippet` - Retrieve source by qualified name
- `surgical_replace_code` - Precise code edits
- `read_file` - Read file contents
- `write_file` - Write file contents
- `list_directory` - Directory structure

**Index Tools:**
- `index_repository` - Parse and ingest codebase

### 3. Parser Layer

**Tree-sitter Integration** (`codebase_rag/parsers/`)
- Language-agnostic AST parsing
- Factory pattern for parser creation
- Per-language processors handle language-specific patterns

**Supported Languages:**
- Python, JavaScript, TypeScript
- Go, Rust, Java, Scala
- C, C++, Lua

**Parser Components:**

**Definition Processor** (`definition_processor.py`)
- Extracts functions, classes, methods
- Builds qualified names (e.g., `app.services.UserService.create_user`)
- Captures docstrings, signatures, decorators

**Call Processor** (`call_processor.py`)
- Identifies function/method calls
- Resolves call targets (with type inference where possible)
- Builds CALLS relationships

**Import Processor** (`import_processor.py`)
- Tracks module imports
- Resolves import paths
- Builds IMPORTS relationships

**Type Inference** (`*_type_inference.py`)
- Language-specific type resolution
- Method call target identification
- Reduces ambiguity in dynamic languages

### 4. Service Layer

**MemgraphIngestor** (`codebase_rag/services/graph_service.py`)
- Manages Memgraph connection
- Batch inserts for performance
- Transaction management
- Query execution

**CypherGenerator** (`codebase_rag/services/llm.py`)
- Natural language → Cypher translation
- Uses pydantic-ai with configurable LLM
- Schema-aware query generation
- Validation and error handling

**LLM Orchestrator**
- Multi-tool agent coordination
- Context management
- Result aggregation
- Configurable providers (OpenAI, Anthropic, Vertex, Ollama)

### 5. Data Layer

**Memgraph Graph Schema:**

**Nodes:**
```cypher
// Core entities
(:File {path, language})
(:Module {name, qualified_name, file_path})
(:Function {name, qualified_name, signature, docstring, start_line, end_line})
(:Class {name, qualified_name, docstring, start_line, end_line})
(:Method {name, qualified_name, signature, docstring, start_line, end_line})
```

**Relationships:**
```cypher
// Structural relationships
(Module)-[:DEFINES]->(Function)
(Module)-[:DEFINES]->(Class)
(Class)-[:DEFINES]->(Method)

// Code relationships
(Function)-[:CALLS {line_number}]->(Function)
(Method)-[:CALLS {line_number}]->(Method|Function)
(Class)-[:INHERITS]->(Class)
(Module)-[:IMPORTS {alias}]->(Module)

// File relationships
(File)-[:CONTAINS]->(Module)
```

**Indexes:**
```cypher
CREATE INDEX ON :Function(qualified_name);
CREATE INDEX ON :Class(qualified_name);
CREATE INDEX ON :Module(qualified_name);
CREATE INDEX ON :File(path);
```

## Key Patterns

### 1. Parsing Flow

```
1. GraphUpdater.update()
   ↓
2. Walk file tree, filter by language
   ↓
3. For each file:
   - Load Tree-sitter parser
   - Parse file → AST
   - Extract definitions (functions, classes)
   - Extract calls
   - Extract imports
   ↓
4. Batch results
   ↓
5. MemgraphIngestor.ingest_batch()
   - Begin transaction
   - Create nodes (Functions, Classes, Modules)
   - Create relationships (CALLS, IMPORTS, DEFINES)
   - Commit transaction
```

### 2. Query Flow

```
Natural Language Query
   ↓
CypherGenerator.generate()
   - LLM converts NL → Cypher
   - Validates against schema
   - Returns Cypher query
   ↓
MemgraphIngestor.execute_query()
   - Execute Cypher
   - Fetch results
   ↓
Format results (JSON/Table/Markdown)
   ↓
Return to interface (MCP/HTTP/CLI)
```

### 3. Tool Invocation Flow

```
Interface (MCP/HTTP/CLI)
   ↓
MCPToolsRegistry.get_tool(name)
   - Lookup tool metadata
   - Extract handler function
   ↓
handler(**params)
   - Validate inputs
   - Execute tool logic
   - Return structured result
   ↓
Interface-specific formatting
   - MCP: JSON response
   - HTTP: JSON API response
   - CLI: Rich formatted output
```

## Configuration

**Environment Variables** (`.env`):

```bash
# Memgraph connection
MEMGRAPH_HOST=localhost
MEMGRAPH_PORT=7687
MEMGRAPH_HTTP_PORT=7444

# LLM for orchestrator (multi-tool agent)
ORCHESTRATOR_PROVIDER=anthropic
ORCHESTRATOR_MODEL=claude-sonnet-4-5-20250929
ORCHESTRATOR_API_KEY=sk-...

# LLM for Cypher generation
CYPHER_PROVIDER=anthropic
CYPHER_MODEL=claude-sonnet-4-5-20250929
CYPHER_API_KEY=sk-...

# Project settings
TARGET_REPO_PATH=.
SHELL_COMMAND_TIMEOUT=30
```

**Provider Support:**
- `anthropic` - Claude models
- `openai` - GPT models
- `google` - Gemini via Vertex AI
- `ollama` - Local models

## Performance Considerations

**Parsing Performance:**
- Parallel file processing (asyncio)
- Batch inserts (1000 nodes/relationships per transaction)
- Incremental updates (planned, not yet implemented)

**Query Performance:**
- Indexed node properties (qualified_name)
- Cypher query optimization
- Result limiting for large graphs

**Memory Management:**
- Streaming file processing
- Batch size tuning via MEMGRAPH_BATCH_SIZE
- Parser cleanup after each file

## Extension Points

### Adding a New Language

1. Add Tree-sitter grammar to `grammars/`
2. Create language-specific processor in `parsers/`
3. Implement definition extraction
4. Implement call extraction
5. Implement import extraction
6. Add to `language_config.py`
7. Register in parser factory

### Adding a New Tool

1. Create tool function with pydantic-ai signature
2. Add to `MCPToolsRegistry._tools` dict
3. Define input schema
4. Implement handler logic
5. Tool automatically available in MCP, HTTP, CLI

### Adding a New Query Pattern

1. Create pre-built Cypher query in `tools/structural_queries.py`
2. Wrap in tool function
3. Add to tool registry
4. Document in tool description

## Dependencies

**Core:**
- `tree-sitter` - AST parsing
- `pymgclient` - Memgraph driver
- `pydantic-ai` - LLM orchestration

**Interface:**
- `mcp` - Model Context Protocol
- `fastapi` - HTTP server
- `typer` - CLI framework

**Utilities:**
- `loguru` - Logging
- `rich` - Terminal formatting
- `watchdog` - File watching (future)

## API Contracts

### MCP Tool Schema

All tools follow this pattern:

```json
{
  "name": "tool_name",
  "description": "What the tool does",
  "inputSchema": {
    "type": "object",
    "properties": {
      "param_name": {
        "type": "string",
        "description": "What this parameter does"
      }
    },
    "required": ["param_name"]
  }
}
```

### HTTP Endpoints

```
POST /api/tools/{tool_name}
Body: {"params": {...}}
Response: {"result": {...}, "status": "success"}
```

### CLI Commands

```bash
graph-code index [--repo URL]     # Index repository
graph-code chat [query]           # Interactive or direct query
graph-code mcp                    # Start MCP server
graph-code http                   # Start HTTP server
```

## Testing Strategy

**Unit Tests** (`codebase_rag/tests/`)
- Parser tests (per language)
- Tool tests (mocked graph)
- Service tests (integration)

**Integration Tests** (`tests/integration/`)
- End-to-end indexing
- Query accuracy
- MCP protocol compliance

**Stress Tests** (`tests/stress/`)
- Large codebase indexing
- Concurrent query load
- Memory profiling

## Deployment

**Development:**
```bash
docker compose up -d              # Start Memgraph
uv run graph-code index           # Index project
uv run graph-code mcp             # Run MCP server
```

**Production:**
- Deploy Memgraph (Docker/Kubernetes)
- Configure environment variables
- Run MCP server as systemd service or launchd agent
- HTTP server behind reverse proxy (optional)

**MCP Integration:**
Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "code-graph-rag": {
      "command": "uv",
      "args": ["run", "graph-code", "mcp"],
      "cwd": "/path/to/code-graph-rag"
    }
  }
}
```
