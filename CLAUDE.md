# code-graph-rag

MCP server for structured code graph queries using Tree-sitter and Memgraph.

## AI Guidance

**CRITICAL:**
- NEVER create files unless absolutely necessary
- NEVER proactively create documentation (*.md, *.txt)
- DO NOT add comments unless code is genuinely unclear
- ALWAYS use fd/rg/eza (NOT find/grep/ls)

**This Project:**
Indexes codebases into Memgraph knowledge graph for structural queries (class hierarchies, call graphs, dependencies, callers). Complements seekr (semantic search) and docwell (document search). Can index working project or external GitHub repos for comparison research.

**For details, search:**
- Architecture → `docs/ARCHITECTURE.md`
- Vision → `docs/VISION.md`

## Commands

### Development
```bash
uv run graph-code index          # Index current project
uv run graph-code chat           # Interactive query CLI
uv run graph-code mcp            # Start MCP server
uv run graph-code http           # Start HTTP server
```

### Database
```bash
docker compose up -d             # Start Memgraph
docker compose down              # Stop Memgraph
```

### Quality
```bash
uv run pytest                    # Run tests
uv run ruff check                # Lint code
uv run mypy codebase_rag         # Type check
```

## Common Workflows

### Indexing a Project
1. Start Memgraph: `docker compose up -d`
2. Index codebase: `uv run graph-code index`
3. Query interactively: `uv run graph-code chat`

### Using as MCP Server
1. Start server: `uv run graph-code mcp`
2. Configure in Claude Desktop MCP settings
3. Use tools: `index_repository`, `query_code_graph`, `query_callers`, etc.

### Querying Code Structure
```bash
# Find who calls a function
uv run graph-code chat "Who calls UserService.create_user?"

# Get class hierarchy
uv run graph-code chat "Show inheritance tree for BaseModel"

# Find dependencies
uv run graph-code chat "What modules does auth.py depend on?"
```

## Code Conventions

- Python 3.12+ with strict type hints
- Tree-sitter for all language parsing
- Pydantic for data validation
- Async/await for I/O operations
- Tests colocated in `codebase_rag/tests/`

## File Organization

```
codebase_rag/
├── main.py              # CLI entry point
├── mcp/                 # MCP server & tools
├── http/                # HTTP server
├── parsers/             # Language-specific parsers
├── services/            # Core services (graph, LLM)
├── tools/               # Query tools
└── tests/               # Test suite
```

## Tool Usage

**ALWAYS use:**
- `fd` for file search
- `rg` for content search
- `eza` for directory listing
- `bat` for file viewing

**NEVER use:**
- `find`, `grep`, `ls`, `cat`

## Documentation Map

**Core docs:**
- `docs/VISION.md` - Purpose, philosophy, relationships
- `docs/ARCHITECTURE.md` - System design, graph schema, tools

**Project registry reference:**
`~/code/ai_agency/shared/scripts/registry/projects.json`

## Active Technologies
- Memgraph graph database (Docker container) (005-rename-to-weavr)

## Recent Changes
- 005-rename-to-weavr: Added Python 3.12+
