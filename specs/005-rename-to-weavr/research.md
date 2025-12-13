# Research: Project Rename Best Practices

**Feature**: Rename code-graph-rag to weavr
**Date**: 2025-12-13

## Research Questions Addressed

Since this is a pure rename operation with no new functionality, the research focuses on comprehensive rename strategies and risk mitigation.

### 1. Python Package Renaming Strategy

**Decision**: Multi-step rename with verification at each stage

**Rationale**:
- Python package names must match directory names for import resolution
- `pyproject.toml` package name controls pip installation name
- Entry point scripts must reference correct module paths
- Import statements throughout codebase must be updated atomically

**Approach**:
1. Update `pyproject.toml`: Change package name and entry point
2. Rename physical directory: `codebase_rag/` → `weavr/`
3. Update all import statements: `from codebase_rag.*` → `from weavr.*`
4. Update test configuration: pytest paths and module references
5. Verify with test suite execution

**Alternatives Considered**:
- **Gradual migration**: Rejected - creates import ambiguity and partial failure states
- **Symlinks**: Rejected - adds unnecessary complexity and isn't cross-platform
- **Import aliasing**: Rejected - doesn't actually rename, just masks the old name

### 2. Docker Infrastructure Renaming

**Decision**: Update compose service names and container references, preserve data volumes

**Rationale**:
- Docker Compose stack name (`codebase-intelligence`) is already generic and shared
- Service names are referenced in connection strings
- Volume names should be preserved to avoid data loss
- Container names are for human reference and can be updated

**Approach**:
1. Keep stack name: `codebase-intelligence` (already neutral, shared infrastructure)
2. Keep service names: `memgraph`, `lab` (generic, used by multiple projects)
3. Keep volume names: Existing data preserved
4. Update comments/documentation referencing the project

**Alternatives Considered**:
- **Full infrastructure rename**: Rejected - breaks other services (vector-search-mcp, docwell) that share the stack
- **Create new stack**: Rejected - duplicates infrastructure unnecessarily
- **Separate databases**: Rejected - against design philosophy of shared graph

### 3. External Reference Discovery Strategy

**Decision**: Multi-tool search approach with verification

**Rationale**:
- References exist in multiple contexts: code imports, documentation, configuration files
- Case variations matter: `code-graph-rag`, `code_graph_rag`, `codebase_rag`, `graph-code`
- Must search across entire ai_agency repository
- Must update specific integration points (http/mcp-service-wrappers)

**Search Patterns**:
```bash
# Code references
rg -i "codebase_rag" ~/code/ai_agency
rg -i "code-graph-rag" ~/code/ai_agency
rg -i "graph-code" ~/code/ai_agency

# Configuration files specifically
rg -i -g "*.{json,yaml,yml,toml,md}" "codebase_rag|code-graph-rag|graph-code" ~/code/ai_agency

# Python imports
rg "from codebase_rag" ~/code/ai_agency
rg "import codebase_rag" ~/code/ai_agency
```

**Verification**:
- After rename, search for old names (should return zero results except git history)
- Run all affected project test suites
- Verify service-wrapper integrations manually

**Alternatives Considered**:
- **IDE global search**: Rejected - not scriptable, doesn't cover all file types
- **git grep**: Rejected - slower than ripgrep, less flexible patterns
- **Manual review**: Rejected - error-prone at scale (50+ projects)

### 4. Documentation Update Strategy

**Decision**: Complete rewrite of identity docs, targeted updates elsewhere

**Rationale**:
- CLAUDE.md defines project identity and metaphor - needs complete update
- VISION.md explains purpose and philosophy - needs new framing
- README.md is first impression - needs new branding
- ARCHITECTURE.md is mostly technical - minimal changes
- Inline comments rarely reference project name - spot fixes only

**Priority Order**:
1. **README.md** (P0): First impression, installation instructions
2. **CLAUDE.md** (P0): AI assistant context, project understanding
3. **VISION.md** (P1): Project philosophy and purpose
4. **ARCHITECTURE.md** (P2): Technical details, mostly unchanged
5. **Inline comments** (P3): Only if they reference project name explicitly

**Content Updates**:
- Add "weavr" metaphor explanation (weaving connections between codebases)
- Add attribution to original code-graph-rag project
- Update all command examples: `graph-code` → `weavr`
- Update package installation: `pip install graph-code` → `pip install weavr`

**Alternatives Considered**:
- **Find-replace all docs**: Rejected - loses context, breaks git history references intentionally kept
- **Keep old README**: Rejected - confusing for new users
- **Minimal documentation updates**: Rejected - violates success criteria SC-003, SC-004

### 5. Git and Version Control Strategy

**Decision**: Keep git history intact, user handles GitHub repo rename separately

**Rationale**:
- Git history contains valuable context (commits, PRs, issues)
- GitHub repository rename is a separate manual step outside code scope
- Old references in commit messages are acceptable and expected
- Git remote URLs will need updating after GitHub rename

**Out of Scope** (per feature spec):
- Rewriting git history to change old references
- Migrating GitHub issues/PRs content
- Updating external forks or clones
- Automated repository rename (requires GitHub API/manual action)

**In Scope**:
- Update `.git/config` remote URLs (after user renames GitHub repo)
- Update any GitHub Actions workflow files
- Update issue/PR templates if they reference project name

**Alternatives Considered**:
- **Git history rewrite**: Rejected - dangerous, breaks external references, violates scope
- **Squash and restart history**: Rejected - loses valuable development context
- **Automated GitHub rename**: Rejected - requires elevated permissions, manual is safer

### 6. Testing and Validation Strategy

**Decision**: Comprehensive test execution with zero tolerance for failures

**Rationale**:
- Success criteria SC-001 requires 100% test pass rate
- 150+ test files cover all supported languages and features
- Tests validate that structural queries still work correctly
- Test failures indicate missed references or broken imports

**Validation Sequence**:
1. **Unit tests**: Verify individual components work with new names
2. **Integration tests**: Verify MCP/HTTP servers work end-to-end
3. **Language tests**: Verify all 6 language parsers still function
4. **Manual smoke test**: Run actual CLI commands, verify output
5. **External integration**: Test http/mcp-service-wrapper connections

**Pass Criteria**:
- All pytest tests pass (0 failures, 0 errors)
- No import errors when running `weavr` command
- MCP server starts without errors
- HTTP server responds to health checks
- Docker Compose stack starts successfully

**Alternatives Considered**:
- **Spot testing**: Rejected - too risky, could miss edge cases
- **Gradual rollout**: Rejected - rename is atomic or nothing
- **Manual testing only**: Rejected - 150+ tests exist for a reason

## Technology Choices Confirmed

No new technologies required. This is purely a rename operation using:

- **Python standard library**: `os.rename()` for directory rename (via git mv)
- **ripgrep (rg)**: Fast text search across large codebases
- **fd**: File discovery for targeted updates
- **pytest**: Existing test framework for validation
- **git**: Version control for tracking changes
- **Docker Compose**: Infrastructure unchanged

## Risk Mitigation Summary

| Risk | Mitigation |
|------|------------|
| Missed references | Multi-pattern search with rg, comprehensive testing |
| Broken imports | Atomic rename, full test suite execution |
| External service breakage | Test service-wrapper integrations explicitly |
| Docker data loss | Preserve volume names, no data migration needed |
| Git history confusion | Keep history intact, clear commit message |
| Test failures | Zero tolerance policy, fix all failures before merge |

## Implementation Readiness

All research questions resolved. No clarifications needed. Ready to proceed to Phase 1 (Design).
