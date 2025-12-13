# Quickstart: Rename Implementation Guide

**Feature**: Rename code-graph-rag to weavr
**Estimated Time**: 45-60 minutes (including validation)
**Risk Level**: Medium (comprehensive testing required)

## Prerequisites

- [ ] All changes committed and pushed on current branch
- [ ] Clean working directory (`git status` shows no uncommitted changes)
- [ ] Docker Compose stack running (`docker compose ps`)
- [ ] Test suite passing on current code (`uv run pytest`)

## Implementation Steps

### Step 1: Update Package Configuration (5 min)

**File**: `pyproject.toml`

```toml
# Change these lines:
[project]
name = "weavr"  # was: "graph-code"

[project.scripts]
weavr = "weavr.main:app"  # was: graph-code = "codebase_rag.main:app"

[tool.setuptools]
packages = ["weavr"]  # was: ["codebase_rag"]

[tool.pytest.ini_options]
testpaths = ["weavr/tests"]  # was: ["codebase_rag/tests"]
```

**Verify**:
```bash
# Check the changes
git diff pyproject.toml
```

---

### Step 2: Rename Python Package Directory (2 min)

**Command**:
```bash
# Use git mv to preserve history
git mv codebase_rag weavr
```

**Verify**:
```bash
# Check directory exists
ls -la weavr/

# Check git staged the move
git status
```

---

### Step 3: Update All Python Imports (10 min)

**Search and replace**:
```bash
# Find all import statements (review first)
rg "from codebase_rag" --type py
rg "import codebase_rag" --type py

# For each file, update imports:
# from codebase_rag.X → from weavr.X
# import codebase_rag → import weavr
```

**Helper script** (optional):
```bash
# Create a script to automate (careful!)
fd -e py -x sed -i '' 's/from codebase_rag/from weavr/g' {}
fd -e py -x sed -i '' 's/import codebase_rag/import weavr/g' {}
```

**Verify**:
```bash
# Should return 0 results
rg "codebase_rag" --type py -g "!specs/"
```

---

### Step 4: Update Documentation (15 min)

**Files to update**:

1. **README.md**:
   - Title: "# Weavr"
   - Description: Explain "weaving connections between codebases"
   - Installation: `pip install weavr` or `uv pip install weavr`
   - Commands: All `graph-code` → `weavr`
   - Add attribution section (see template below)

2. **CLAUDE.md**:
   - Header: `# weavr`
   - Description update
   - All command examples: `graph-code` → `weavr`

3. **VISION.md**:
   - Project name throughout
   - Add "weavr" metaphor explanation

4. **ARCHITECTURE.md**:
   - Update project references
   - Command examples: `graph-code` → `weavr`

**Attribution Template**:
```markdown
## Attribution

This project is a fork of [code-graph-rag](https://github.com/original/code-graph-rag),
renamed to **weavr** to better reflect its purpose of weaving connections between
codebases through structural code graph analysis.
```

**Verify**:
```bash
# Should return 0 results
rg "code-graph-rag" README.md CLAUDE.md VISION.md ARCHITECTURE.md
rg "graph-code" -g "*.md" -g "!specs/"
```

---

### Step 5: Update Docker Documentation (2 min)

**File**: `docker-compose.yaml`

**Change**: Update comments only (DO NOT change service names or stack name)

```yaml
# Weavr Infrastructure
# Shared Memgraph instance for:
# - weavr (structural code analysis)
# - vector-search-mcp (semantic code search)
# - docwell (document search)

name: codebase-intelligence  # NO CHANGE - shared stack
```

**Verify**:
```bash
# Stack should still start
docker compose up -d
docker compose ps
```

---

### Step 6: Run Complete Test Suite (5 min)

**Command**:
```bash
uv run pytest -v --tb=short
```

**Expected**: 100% pass rate, 0 failures, 0 errors

**If failures occur**:
1. Check error messages for import errors
2. Look for hardcoded `codebase_rag` references
3. Fix and re-run
4. DO NOT proceed until all tests pass

---

### Step 7: Update External Service References (10 min)

**Locations**:

1. **http-service-wrappers/**:
   ```bash
   cd ../http-service-wrappers
   rg "code-graph-rag|codebase_rag|graph-code"
   # Update configuration files and documentation
   ```

2. **mcp-service-wrappers/**:
   ```bash
   cd ../mcp-service-wrappers
   rg "code-graph-rag|codebase_rag|graph-code"
   # Update configuration files and documentation
   ```

3. **Project Registry**:
   ```bash
   python ~/code/ai_agency/shared/scripts/registry/registry-manager.py update weavr \
     --path ~/code/ai_agency/shared/mcp-servers/weavr \
     --description "Structural code graph analysis - weaving connections between codebases"
   ```

**Verify**:
```bash
python ~/code/ai_agency/shared/scripts/registry/registry-manager.py list | grep weavr
```

---

### Step 8: Search Entire Ecosystem (5 min)

**Command**:
```bash
# From ai_agency root
cd ~/code/ai_agency

# Search for any remaining references
rg "code-graph-rag" --type-add 'config:*.{json,yaml,yml,toml}' -t config
rg "codebase_rag" --type py -g "!.git/" -g "!specs/"
rg "graph-code" -g "!.git/" -g "!specs/"
```

**Action**: Update any found references (excluding git history and spec files)

---

### Step 9: Manual Smoke Tests (5 min)

**Tests**:

```bash
# 1. CLI help works
weavr --help

# 2. Index command works
weavr index

# 3. Chat command works
weavr chat "show me all functions"

# 4. MCP server starts
weavr mcp

# 5. HTTP server starts
weavr http
```

**Expected**: All commands execute without import errors

---

### Step 10: Final Verification (5 min)

**Checklist**:

- [ ] `weavr --help` executes successfully
- [ ] All tests pass: `uv run pytest`
- [ ] No old references: `rg "codebase_rag" --type py -g "!specs/"`
- [ ] No old package: `rg "graph-code" -g "!specs/" -g "!.git/"`
- [ ] Documentation updated: Manual review of README, CLAUDE.md, VISION.md
- [ ] Docker works: `docker compose up -d`
- [ ] Registry updated: `registry-manager.py list | grep weavr`

**If all pass**:
```bash
git add -A
git commit -m "feat: rename project from code-graph-rag to weavr

- Rename Python package: codebase_rag → weavr
- Rename CLI command: graph-code → weavr
- Update all import statements and references
- Update documentation with weavr identity and attribution
- Update external service references and registry
- All tests passing (100% pass rate)

Relates to #005-rename-to-weavr"
```

---

## Rollback Procedure

If critical issues arise:

```bash
# Before committing (if in progress)
git reset --hard HEAD
git clean -fd

# After committing (if pushed)
git revert HEAD
# Or for complete rollback:
git reset --hard <previous-commit-hash>
```

---

## Post-Implementation

After successful implementation:

1. **User action required**: Rename GitHub repository
   - Settings → Repository → Rename
   - Update git remote URL locally

2. **Optional**: Rebuild Docker images with new tags

3. **Optional**: Publish to PyPI as `weavr` package

---

## Common Issues

### Import Errors After Rename

**Symptom**: `ModuleNotFoundError: No module named 'codebase_rag'`

**Fix**:
```bash
# Check for missed imports
rg "codebase_rag" --type py

# Check Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### Tests Fail to Discover

**Symptom**: pytest finds 0 tests

**Fix**:
```bash
# Check pytest configuration
grep testpaths pyproject.toml
# Should be: testpaths = ["weavr/tests"]

# Verify tests exist
ls -la weavr/tests/
```

### CLI Command Not Found

**Symptom**: `weavr: command not found`

**Fix**:
```bash
# Reinstall package
uv pip install -e .

# Or use direct invocation
uv run weavr --help
```

### Docker Containers Won't Start

**Symptom**: Compose errors

**Fix**:
```bash
# Check if service names were changed (they shouldn't be)
grep "services:" docker-compose.yaml -A 10

# Reset Docker
docker compose down
docker compose up -d
```

---

## Time Estimates by Step

| Step | Time | Can Skip? |
|------|------|-----------|
| 1. Package config | 5 min | No |
| 2. Rename directory | 2 min | No |
| 3. Update imports | 10 min | No |
| 4. Update docs | 15 min | No |
| 5. Docker comments | 2 min | Yes (cosmetic) |
| 6. Test suite | 5 min | No |
| 7. External refs | 10 min | Partial (critical services only) |
| 8. Ecosystem search | 5 min | No |
| 9. Smoke tests | 5 min | No |
| 10. Verification | 5 min | No |

**Total**: 45-60 minutes (conservative estimate)
