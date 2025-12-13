# Project Constitution

## Core Principles

### 1. Precision Over Approximation
- Tree-sitter provides exact AST parsing, not heuristics
- Memgraph stores precise relationships, not fuzzy matches
- Query results must be 100% accurate based on actual code structure
- Type inference improves precision but never sacrifices correctness

### 2. Language Agnostic Foundation
- Unified graph schema works across all languages
- Tree-sitter grammars enable consistent parsing patterns
- Same query tools work for Python, TypeScript, Rust, etc.
- Language-specific processors handle unique features without breaking abstraction

### 3. Structural Focus, Not Semantic Search
- We answer "who calls this" not "find similar code"
- We map "what inherits from X" not "discover related patterns"
- We trace "what depends on Y" not "search for imports"
- Complementary to seekr (semantic) and docwell (docs), not competitive

### 4. Multiple Indexing Targets
- Index working project for active development queries
- Index external GitHub repos for research and comparison
- Support cross-project graph queries
- Enable architectural pattern analysis across codebases

### 5. MCP-First Integration
- Native MCP server is primary interface
- HTTP API for external integrations (secondary)
- CLI for interactive exploration and debugging
- All interfaces share same tool registry

## Quality Standards

### Code Quality

**Type Safety:**
- All Python code must include type hints
- Use strict mypy configuration
- Pydantic models for all data structures
- No `Any` types without justification

**Testing:**
- Unit tests for parsers (per language)
- Integration tests for end-to-end indexing
- Stress tests for large codebases (>100k LOC)
- Query accuracy validation against known codebases

**Performance:**
- Index 100k LOC projects in <60 seconds
- Batch insertions (1000 nodes/tx minimum)
- Parallel file processing via asyncio
- Query response time <2 seconds for common patterns

### CLI Quality

**Output Formatting:**
- Rich formatting for interactive CLI
- JSON for programmatic consumption
- Markdown for documentation
- Tables for relationship queries

**Error Handling:**
- Clear error messages with actionable guidance
- Graceful degradation when parser fails
- Connection retry logic for Memgraph
- Timeout handling for LLM queries

**User Experience:**
- Natural language queries feel intuitive
- Progress indicators for long operations
- Confirmation prompts for destructive actions
- Session logging for debugging

### Documentation Quality

**CLAUDE.md:**
- Under 200 lines (progressive discovery)
- Critical behavioral rules only
- Pointers to VISION.md and ARCHITECTURE.md
- No duplication with other docs

**VISION.md:**
- Clear problem statement
- Design philosophy with rationale
- Relationship to broader infrastructure
- Success criteria and non-goals

**ARCHITECTURE.md:**
- System overview with diagrams
- Component descriptions
- Graph schema documentation
- Extension points clearly marked

**README.md:**
- Quick start in <5 steps
- Key capabilities with examples
- Multiple interface usage patterns
- Clear relationship to complementary tools

## Development Workflow

### Adding Features

1. **Define the problem:** What structural question does this answer?
2. **Design the query:** What Cypher pattern captures this?
3. **Create the tool:** Implement with pydantic-ai signature
4. **Add to registry:** Register in MCPToolsRegistry
5. **Test thoroughly:** Unit, integration, accuracy validation
6. **Document in ARCHITECTURE.md:** Add to tool catalog

### Adding Language Support

1. **Add Tree-sitter grammar:** Place in `grammars/`
2. **Create language processor:** Implement in `parsers/`
3. **Extract definitions:** Functions, classes, methods
4. **Extract calls:** Function/method invocations
5. **Extract imports:** Module dependencies
6. **Add type inference:** Language-specific resolution (if applicable)
7. **Test with real codebases:** Validate accuracy
8. **Register in language_config.py:** Enable in factory

### Testing Requirements

**Before Merging:**
- All tests pass (`uv run pytest`)
- Type checks pass (`uv run mypy codebase_rag`)
- Linter passes (`uv run ruff check`)
- No performance regressions (stress tests)

**For New Languages:**
- Parse sample codebases (1k+ LOC)
- Validate definition extraction accuracy
- Validate call graph accuracy
- Validate import resolution accuracy

**For New Tools:**
- Unit tests with mocked graph
- Integration tests with real graph
- Accuracy validation against known queries
- Documentation with usage examples

## Integration Contracts

### MCP Server Contract

**Tools must:**
- Follow pydantic-ai Tool signature
- Return structured results (dict/list)
- Include clear descriptions
- Define JSON schemas for inputs

**Server must:**
- Expose all registered tools
- Handle async tool execution
- Provide error context in responses
- Log tool invocations

### HTTP Server Contract

**Endpoints must:**
- Accept `POST /api/tools/{tool_name}`
- Expect `{"params": {...}}` body
- Return `{"result": {...}, "status": "success|error"}`
- Include appropriate HTTP status codes

**Server must:**
- CORS-enabled for web integrations
- Health check endpoint (`/health`)
- Request/response logging
- Error responses with details

### CLI Contract

**Commands must:**
- Use Typer for argument parsing
- Provide `--help` documentation
- Rich formatting for output
- Return appropriate exit codes

**Interface must:**
- Interactive mode for `chat` command
- Non-interactive mode for scripting
- Progress indicators for long operations
- Session logging for debugging

## Performance Constraints

### Indexing Performance

**Targets:**
- 10k LOC: <10 seconds
- 100k LOC: <60 seconds
- 1M LOC: <10 minutes

**Optimization strategies:**
- Parallel file processing (asyncio)
- Batch graph insertions (1000+/tx)
- Incremental updates (planned)
- Parser result caching

### Query Performance

**Targets:**
- Simple queries (callers, hierarchy): <1 second
- Complex queries (call graphs, patterns): <5 seconds
- Natural language queries: <10 seconds (includes LLM)

**Optimization strategies:**
- Indexed node properties (qualified_name)
- Cypher query optimization
- Result limiting for large graphs
- Query result caching (planned)

### Resource Usage

**Memory:**
- Parser memory cleanup after each file
- Streaming file processing
- Configurable batch sizes
- Graph connection pooling

**CPU:**
- Async I/O for file operations
- Parallel parsing where possible
- Efficient Tree-sitter node traversal
- Lazy loading of parsers

## Governance

### Decision Making

**Tool design decisions:**
- Must solve real structural query needs
- Must not duplicate existing tools (seekr, docwell)
- Must work across multiple languages
- Must be testable and maintainable

**Language support decisions:**
- Must have Tree-sitter grammar available
- Must represent significant user demand
- Must be maintainable with available resources
- Must provide value beyond text search

**Architecture decisions:**
- Document in ARCHITECTURE.md with rationale
- Consider performance implications
- Maintain backwards compatibility where possible
- Prefer simplicity over premature optimization

### Conflict Resolution

**When tools overlap:**
- Prefer pre-built tools (query_callers) over general query tool
- Document which tool to use when in descriptions
- Deprecate redundant tools gradually

**When languages conflict:**
- Language-specific processors handle unique features
- Factory pattern isolates language differences
- Unified graph schema maintained across all languages

**When performance conflicts with accuracy:**
- Accuracy always wins
- Optimize without sacrificing correctness
- Document performance trade-offs
- Provide configuration for tuning

## Evolution Guidelines

### Breaking Changes

**Avoid breaking:**
- MCP tool schemas (versioning instead)
- Graph schema (migrations instead)
- CLI command signatures (deprecation warnings)

**When unavoidable:**
- Version bump (semver)
- Migration guide in docs
- Deprecation period (2+ releases)
- Clear changelog entry

### Feature Additions

**Prioritize:**
- Common structural query patterns
- Language support for popular languages
- Performance optimizations
- Developer experience improvements

**Defer:**
- Semantic search features (use seekr)
- Documentation search (use docwell)
- Code modification (use file editor tools)
- Static analysis (use ruff, mypy, etc.)

### Technical Debt

**Pay down:**
- Incremental indexing (planned)
- Query result caching (planned)
- Parser error recovery
- Performance profiling

**Accept:**
- Perfect type inference (impossible for dynamic languages)
- 100% language coverage (Tree-sitter limitations)
- Real-time updates (file watching overhead)
- Distributed graph (single Memgraph sufficient)
