# Rename Contract: code-graph-rag → weavr

**Version**: 1.0
**Date**: 2025-12-13
**Status**: Draft

## Purpose

This contract defines the exact transformations required for the project rename and serves as a verification checklist for implementation.

## Scope

This contract covers all identifier transformations within:
- This repository
- Direct integration points (http-service-wrappers, mcp-service-wrappers)
- ai_agency ecosystem references
- Project registry

## Transformation Rules

### 1. Python Module Names

**Rule**: Replace all instances of `codebase_rag` with `weavr` in Python contexts

| Context | Old | New | Validation |
|---------|-----|-----|------------|
| Directory name | `codebase_rag/` | `weavr/` | `ls weavr/` succeeds |
| Import statements | `from codebase_rag.X` | `from weavr.X` | No ImportError |
| Import statements | `import codebase_rag` | `import weavr` | No ImportError |
| Type annotations | `codebase_rag.Type` | `weavr.Type` | mypy passes |
| Docstrings | Module references | Updated | rg returns 0 matches |
| Test imports | All test files | Updated | pytest passes |

**Verification Command**:
```bash
# Should return 0 results
rg "codebase_rag" --type py -g "!specs/" -g "!.git/"
```

---

### 2. Package Distribution Names

**Rule**: Replace `graph-code` with `weavr` in package configuration

| Context | Old | New | Validation |
|---------|-----|-----|------------|
| Package name | `name = "graph-code"` | `name = "weavr"` | pyproject.toml updated |
| Entry point | `graph-code = "codebase_rag.main:app"` | `weavr = "weavr.main:app"` | pyproject.toml updated |
| Setuptools | `packages = ["codebase_rag"]` | `packages = ["weavr"]` | pyproject.toml updated |
| README install | `pip install graph-code` | `pip install weavr` | README.md updated |

**Verification Command**:
```bash
# Should return 0 results
rg "graph-code" -g "!specs/" -g "!.git/"

# Entry point should work
weavr --help
```

---

### 3. CLI Command References

**Rule**: Replace `graph-code` command with `weavr` in all documentation and examples

| Context | Old Pattern | New Pattern | Validation |
|---------|-------------|-------------|------------|
| README commands | `uv run graph-code` | `uv run weavr` | Updated |
| CLAUDE.md examples | `graph-code index` | `weavr index` | Updated |
| Documentation | All command examples | Updated | Manual review |
| Shell scripts | Any automation | Updated | Scripts run |

**Verification Command**:
```bash
# In documentation only
rg "graph-code" -g "*.md" -g "!specs/" -g "!.git/"
```

---

### 4. Documentation References

**Rule**: Replace project name references consistently

| Document | Old References | New References | Special Notes |
|----------|---------------|----------------|---------------|
| README.md | "code-graph-rag" | "weavr" | Add attribution section |
| CLAUDE.md | "code-graph-rag" | "weavr" | Update project description |
| VISION.md | "code-graph-rag" | "weavr" | Explain "weavr" metaphor |
| ARCHITECTURE.md | "code-graph-rag" | "weavr" | Technical details mostly unchanged |
| Inline comments | Project references | Updated | Only where project name appears |

**Attribution Requirement**:
All primary documentation (README, VISION) must include:
> This project is a fork of [code-graph-rag](https://github.com/original/code-graph-rag), renamed to better reflect its purpose of weaving connections between codebases.

**Verification Command**:
```bash
# Should return 0 results in main docs
rg "code-graph-rag" README.md CLAUDE.md VISION.md ARCHITECTURE.md
```

---

### 5. Docker Infrastructure

**Rule**: Update only documentation comments, preserve shared infrastructure names

| Component | Action | Rationale |
|-----------|--------|-----------|
| Stack name (`codebase-intelligence`) | **NO CHANGE** | Shared by multiple services |
| Service names (`memgraph`, `lab`) | **NO CHANGE** | Generic, reusable |
| Container names | **NO CHANGE** | Already generic |
| Volume names | **NO CHANGE** | Preserve existing data |
| Documentation comments | Update | Clarify weavr is using this infrastructure |

**Verification**:
```bash
# Should start successfully
docker compose up -d

# Should preserve data
docker volume ls | grep codebase-intelligence
```

---

### 6. External Ecosystem References

**Rule**: Update integration points and registry

| Location | Old Reference | New Reference | Validation |
|----------|---------------|---------------|------------|
| http-service-wrappers/ | Configuration files | Updated | Service connects |
| mcp-service-wrappers/ | Configuration files | Updated | Service connects |
| Project registry | `"code-graph-rag"` entry | `"weavr"` entry | Registry query succeeds |
| Other ai_agency projects | Code references | Updated | Cross-project search |

**Verification Commands**:
```bash
# From ai_agency root
rg "code-graph-rag" --type-add 'config:*.{json,yaml,yml,toml}' -t config
rg "codebase_rag" --type py

# Registry
python ~/code/ai_agency/shared/scripts/registry/registry-manager.py list | grep weavr
```

---

### 7. Test Configuration

**Rule**: Update all test references and paths

| File | Old | New | Validation |
|------|-----|-----|------------|
| pyproject.toml | `testpaths = ["codebase_rag/tests"]` | `testpaths = ["weavr/tests"]` | pytest finds tests |
| Test imports | `from codebase_rag.` | `from weavr.` | All imports resolve |
| Test data | File paths with old name | Updated if applicable | Tests pass |

**Verification Command**:
```bash
uv run pytest -v
# Should: 100% pass rate, 0 failures, 0 errors
```

---

## Exclusions (Do NOT Change)

The following MUST NOT be changed:

1. **Git History**:
   - Commit messages containing old names
   - Tag names
   - Branch names (except current feature branch)

2. **Infrastructure Names**:
   - Docker stack: `codebase-intelligence`
   - Docker services: `memgraph`, `lab`
   - Docker volumes: existing volume names

3. **External References**:
   - Forks of the repository
   - External users' configurations
   - Original code-graph-rag project

4. **Graph Schema**:
   - Memgraph node labels
   - Memgraph edge types
   - Query patterns (unless they reference package name)

## Success Criteria

All of the following must be true:

- [ ] `weavr --help` command executes successfully
- [ ] `uv run weavr index` indexes a test project without errors
- [ ] `uv run pytest` shows 100% pass rate
- [ ] `rg "codebase_rag" --type py -g "!specs/" -g "!.git/"` returns 0 results
- [ ] `rg "graph-code" -g "!specs/" -g "!.git/"` returns 0 results
- [ ] `rg "code-graph-rag" README.md CLAUDE.md VISION.md` returns 0 results
- [ ] `docker compose up -d` starts successfully
- [ ] External service wrappers can connect to weavr
- [ ] Project registry contains "weavr" entry
- [ ] Attribution to original project exists in README

## Rollback Plan

If critical failures occur:

1. **Immediate**: Revert all changes via `git reset --hard`
2. **Partial**: Use git to selectively revert problematic files
3. **Infrastructure**: No rollback needed (names unchanged)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-13 | Initial contract for rename operation |
