<!--
SYNC IMPACT REPORT
==================
Version Change: 0.0.0 → 1.0.0 (MAJOR - initial constitution)
Modified Principles: N/A (new constitution)
Added Sections:
  - Core Principles (5 principles)
  - Technical Standards
  - Development Workflow
  - Governance
Removed Sections: N/A
Template Status:
  - .specify/templates/plan-template.md: ✅ Compatible (Constitution Check section exists)
  - .specify/templates/spec-template.md: ✅ Compatible (requirements-focused)
  - .specify/templates/tasks-template.md: ✅ Compatible (phase-based structure)
Follow-up TODOs: None
-->

# Code-Graph-RAG Constitution

## Core Principles

### I. Graph-First Intelligence

The knowledge graph is the authoritative source of codebase understanding. All code analysis, querying, and AI-assisted operations MUST flow through the graph database.

- Every codebase insight MUST be derivable from graph queries
- Natural language queries translate to Cypher; results come from graph, not heuristics
- Graph schema defines what the system "knows" about code
- New language support MUST update the graph schema, not bypass it

**Rationale**: Graphs capture relationships (calls, contains, defines) that flat text search cannot. Consistent graph access ensures reproducible, explainable results.

### II. Multi-Language Universality

All supported programming languages receive equal treatment through a unified graph schema. No language receives special handling that breaks schema consistency.

- Unified node types: Project, Module, Class, Function, Method across ALL languages
- Unified relationships: CONTAINS, DEFINES, CALLS, DEPENDS_ON apply universally
- Language-specific features (decorators, generics, traits) map to common patterns
- Adding a language MUST NOT require schema changes; only parser configuration

**Rationale**: AI tools querying the graph should not need language-specific logic. A query for "functions that call X" works identically for Python, Rust, or TypeScript.

### III. AI-Native Interface

The MCP (Model Context Protocol) server is the primary interface for AI tools to access codebase intelligence. Design decisions prioritize AI consumption patterns.

- MCP tools MUST be the first-class way AI accesses the graph
- Tool responses MUST be structured for LLM consumption (concise, actionable)
- Natural language → Cypher translation is core functionality, not an add-on
- Semantic search (embeddings) supplements structural graph queries

**Rationale**: This project exists to give AI systems deep codebase understanding. Every feature must answer: "How does this help an AI work with code?"

### IV. Parse Precision

Tree-sitter AST parsing is the only acceptable method for code analysis. No regex-based parsing, no heuristic guessing.

- All code extraction MUST use Tree-sitter grammars
- Function boundaries, class definitions, call sites come from AST nodes only
- Adding language support requires a Tree-sitter grammar; no exceptions
- Code snippets retrieved MUST match exact AST node boundaries

**Rationale**: Regex and heuristics produce false positives/negatives. AST parsing guarantees structural correctness. AI tools need reliable data.

### V. Safe Code Operations

Code modifications require explicit confirmation and preserve the ability to recover. The system defaults to read-only operations.

- All file writes MUST show diffs before execution
- Surgical code replacement targets specific AST nodes, not line ranges
- Original code MUST be recoverable (via git, backups, or undo)
- Batch modifications MUST be individually reviewable
- MCP edit tools MUST respect project directory boundaries

**Rationale**: AI-assisted code changes can cascade unexpectedly. Explicit confirmation and recovery paths prevent irreversible damage.

## Technical Standards

### Database Requirements

- Memgraph is the required graph database (Cypher-compatible, in-memory performance)
- Each project gets its own database: `codegraph_<project-name>`
- Group-level databases (`codegraph_<group>`) aggregate related projects
- Graph updates MUST be atomic per-file to prevent partial states

### Embedding Requirements

- Semantic search uses code-specialized embeddings (nomic-embed-code or equivalent)
- Embeddings are stored alongside graph nodes, not in separate systems
- Vector similarity thresholds MUST be tunable per-query

### Configuration Standards

- Provider configuration (Ollama, OpenAI, Google) uses explicit environment variables
- No hardcoded API endpoints or model names in source code
- Mixed provider configurations (different models for orchestrator vs cypher) MUST be supported

## Development Workflow

### Testing Requirements

- Parser changes require test coverage for affected language
- MCP tool changes require integration tests with sample queries
- Graph schema changes require migration scripts and backward compatibility tests

### Code Change Protocol

- New language support follows the documented `add-grammar` workflow
- Infrastructure changes (init scripts, hooks) require testing on sample projects
- Breaking changes to MCP tools require version bumps and changelog entries

### Documentation Updates

- README.md reflects user-facing features and setup
- CLAUDE.md provides AI-agent guidance for working with the codebase
- docs/INFRASTRUCTURE.md covers deployment and project initialization

## Governance

This constitution supersedes all other development practices for code-graph-rag.

**Amendment Process**:
1. Propose changes via PR with rationale
2. Changes affecting Core Principles require explicit approval
3. Document migration path for any principle modifications
4. Update dependent templates when principles change

**Versioning**:
- MAJOR: Principle removals, fundamental changes to graph schema
- MINOR: New principles, expanded guidance, new technical standards
- PATCH: Clarifications, typo fixes, non-behavioral changes

**Compliance**:
- All PRs MUST verify alignment with Core Principles
- Complexity that violates principles requires documented justification
- The CLAUDE.md file serves as runtime guidance for AI agents

**Version**: 1.0.0 | **Ratified**: 2025-12-06 | **Last Amended**: 2025-12-06
