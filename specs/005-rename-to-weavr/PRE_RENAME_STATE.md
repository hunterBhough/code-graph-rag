# Pre-Rename State Documentation

**Date**: 2025-12-13
**Branch**: 005-rename-to-weavr
**Commit**: 3ae669d

## Current Package Configuration

### Package Identity
- **Package Name**: `graph-code`
- **Version**: 0.0.24
- **Python Module**: `codebase_rag`
- **CLI Command**: `graph-code`

### Key Identifiers

**pyproject.toml**:
```toml
[project]
name = "graph-code"

[project.scripts]
graph-code = "codebase_rag.main:app"

[tool.setuptools]
packages = ["codebase_rag"]

[tool.pytest.ini_options]
testpaths = ["codebase_rag/tests"]
```

**Directory Structure**:
- Main package: `codebase_rag/`
- Test suite: `codebase_rag/tests/`

### Test Baseline (Before Rename)

**Test Run Date**: 2025-12-13
**Full Test Suite Results**:
- ✅ **438 passed**
- ❌ **286 failed** (C++, Rust, Lua, some Java tests - pre-existing failures)
- ⏭️ **106 skipped** (Java tests)
- ⚠️ **4 errors** (Memgraph-related tests - pre-existing errors)
- ⚠️ **176,161 warnings** (pre-existing warnings)
- ⏱️ **Duration**: 51.66s

**Test Log**: Saved to `/tmp/test-baseline.log`

### Expected Post-Rename State

After the rename operation completes successfully:
- Package name: `graph-code` → `weavr`
- Python module: `codebase_rag` → `weavr`
- CLI command: `graph-code` → `weavr`
- Directory: `codebase_rag/` → `weavr/`

**Success Criteria**:
- All 438 passing tests MUST still pass
- Test failure/error/skip counts should remain the same
- No new import errors or module resolution issues
- CLI commands work with new `weavr` entry point

### Repository State

**Git Branch**: `005-rename-to-weavr` (created and checked out)
**Working Directory**: Clean (all preparatory changes committed)
**Last Commit**: 3ae669d - "docs: prepare project documentation for rename to weavr"

### External References to Update

**Known Integration Points**:
1. `../http-service-wrappers/` (if exists)
2. `../mcp-service-wrappers/` (if exists)
3. Project registry: `~/code/ai_agency/shared/scripts/registry/projects.json`
4. Entire ai_agency repository ecosystem references

### Notes

This baseline establishes the pre-rename state for validation purposes. After the rename operations complete, we will:
1. Re-run the test suite to ensure the same 438 tests pass
2. Verify CLI commands work with the new `weavr` entry point
3. Confirm no new errors or import issues are introduced
4. Validate that the rename is purely cosmetic with zero functional changes
