# Vision

## Purpose

code-graph-rag exists to answer structural questions about codebases that semantic search and document search cannot. While seekr finds semantically similar code and docwell searches documentation, code-graph-rag understands relationships: who calls this function, what classes inherit from this base, what are the circular dependencies.

## Core Problem

Understanding code structure requires more than text similarity:

- "Who calls this function?" - requires parsing call graphs
- "What inherits from BaseModel?" - requires class hierarchy analysis
- "What modules depend on auth.py?" - requires import graph traversal
- "Show me the call stack for authentication" - requires multi-hop graph queries

Traditional search falls short. We need a knowledge graph.

## Design Philosophy

**1. Precision over fuzzy matching**
- Tree-sitter parsers provide exact AST analysis
- Memgraph stores precise relationships
- Structural queries return definitive answers

**2. Language-agnostic foundation**
- Tree-sitter grammars for all major languages
- Unified graph schema across languages
- Same query tools work for Python, TypeScript, Rust, etc.

**3. Complementary, not competitive**
- seekr: "Find code similar to this authentication pattern"
- docwell: "Search our architecture docs for auth strategy"
- code-graph-rag: "Show me all functions that call verify_token"

**4. Multiple indexing targets**
- Index working project for active development
- Index external GitHub repos for research
- Compare graphs across projects
- Build cross-project knowledge base

**5. MCP-first integration**
- Native MCP server for Claude Desktop
- HTTP server for external integrations
- CLI for interactive exploration
- All modes share same tool set

## Relationship to Broader Infrastructure

### Complementary Tools

**seekr** (semantic search)
- Vector embeddings of code chunks
- Find similar implementations
- Discover related functionality
- "Show me code that does X"

**docwell** (document search)
- Vector search across markdown docs
- Architecture documentation discovery
- Design decision lookup
- "What does our auth guide say about tokens?"

**code-graph-rag** (structural queries)
- Graph of code relationships
- Precise structural analysis
- Dependency tracking
- "Who calls this? What depends on that?"

### Integration Points

All three tools can be used together:

1. Use docwell to understand architecture principles
2. Use code-graph-rag to map actual implementation structure
3. Use seekr to find similar patterns across codebase
4. Compare findings to ensure consistency

### Cross-Project Research

code-graph-rag uniquely supports indexing multiple projects:

```bash
# Index your project
uv run graph-code index

# Index external repo for comparison
uv run graph-code index --repo https://github.com/org/reference-impl

# Query both graphs
"How does our auth differ from reference-impl?"
```

## Extensibility Principles

**1. Parser extensibility**
- Add new Tree-sitter grammars in `grammars/`
- Language-specific processors in `parsers/`
- Unified interface via factory pattern

**2. Query tool extensibility**
- Pre-built tools for common patterns (callers, hierarchy, dependencies)
- Natural language query tool for custom questions
- Expert mode for direct Cypher queries

**3. Integration extensibility**
- MCP server for Claude Desktop
- HTTP API for web integrations
- CLI for scripting and automation
- Shared tool registry across all modes

**4. Graph schema extensibility**
- Core nodes: Function, Class, Module, File
- Core relationships: CALLS, INHERITS, IMPORTS, DEFINES
- Language-specific extensions via node properties
- Custom relationships for domain-specific analysis

## Success Criteria

**Precision**: Structural queries return 100% accurate results based on actual code
**Coverage**: Support all major languages via Tree-sitter grammars
**Performance**: Index 100k LOC projects in <60 seconds
**Usability**: Natural language queries feel intuitive, not forced
**Integration**: Seamless MCP integration with other code analysis tools

## Non-Goals

**Not a semantic search engine** - use seekr for that
**Not a documentation search** - use docwell for that
**Not a code completion tool** - use language servers for that
**Not a static analyzer** - use ruff, mypy, etc. for that
**Not a code modification tool** - use file editor tools for that

We do one thing well: answer structural questions about code relationships.

## Future Considerations

**Enhanced language support**
- Add C#, PHP, Ruby parsers
- Improve type inference for dynamic languages
- Better handling of macros and metaprogramming

**Performance optimizations**
- Incremental indexing (only re-parse changed files)
- Parallel parsing for large codebases
- Graph query caching for common patterns

**Advanced queries**
- Temporal queries (how has this evolved?)
- Change impact analysis (what breaks if I modify this?)
- Architecture conformance (does code match intended design?)

**Cross-project intelligence**
- Pattern mining across indexed repos
- Best practice discovery
- Anti-pattern detection
- Comparative architecture analysis

But core focus remains: precise, fast, structural code queries.
