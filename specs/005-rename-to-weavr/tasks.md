# Tasks: Rename Project to Weavr

**Input**: Design documents from `/specs/005-rename-to-weavr/`
**Prerequisites**: plan.md, spec.md

**Tests**: Not explicitly requested - focusing on systematic renaming and validation through existing test suite.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: Root directory contains `codebase_rag/` (to be renamed to `weavr/`), config files, docs, etc.
- All paths assume repository root at `/Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag/`

---

## Phase 1: Setup (Preparation & Backup)

**Purpose**: Prepare for rename operation and ensure safety measures are in place

- [ ] T001 Create git branch `005-rename-to-weavr` and verify clean working directory
- [ ] T002 Run full test suite to establish baseline before any changes
- [ ] T003 Document current package name and CLI command for reference

---

## Phase 2: Foundational (Core Rename - Blocking All Stories)

**Purpose**: Core infrastructure rename that MUST be complete before ANY user story validation

**⚠️ CRITICAL**: No user story validation can occur until this phase is complete

- [ ] T004 Rename Python package directory from `codebase_rag/` to `weavr/`
- [ ] T005 Update package name in `pyproject.toml` from "graph-code" to "weavr"
- [ ] T006 Update CLI script entry point in `pyproject.toml` from "graph-code" to "weavr"
- [ ] T007 Update setuptools packages configuration in `pyproject.toml` from ["codebase_rag"] to ["weavr"]

**Checkpoint**: Core package structure renamed - user story validation can now begin

---

## Phase 3: User Story 1 - Core Project Functionality (Priority: P1) 🎯 MVP

**Goal**: Ensure all internal code works seamlessly with the new name "weavr"

**Independent Test**: Run full test suite (`uv run pytest`) - all tests must pass without errors

### Implementation for User Story 1

- [ ] T008 [P] [US1] Update all import statements in `weavr/main.py` from `codebase_rag` to `weavr`
- [ ] T009 [P] [US1] Update all import statements in `weavr/mcp/` files from `codebase_rag` to `weavr`
- [ ] T010 [P] [US1] Update all import statements in `weavr/http/` files from `codebase_rag` to `weavr`
- [ ] T011 [P] [US1] Update all import statements in `weavr/parsers/` files from `codebase_rag` to `weavr`
- [ ] T012 [P] [US1] Update all import statements in `weavr/services/` files from `codebase_rag` to `weavr`
- [ ] T013 [P] [US1] Update all import statements in `weavr/tools/` files from `codebase_rag` to `weavr`
- [ ] T014 [P] [US1] Update all import statements in `tests/` files from `codebase_rag` to `weavr`
- [ ] T015 [P] [US1] Update module references in `weavr/__init__.py` if it exists
- [ ] T016 [US1] Search and update any remaining Python code references to `codebase_rag` using `rg "codebase_rag" --type py`
- [ ] T017 [P] [US1] Update Docker Compose service names in `docker-compose.yaml` to use "weavr" prefix
- [ ] T018 [P] [US1] Update Docker image names and labels in `Dockerfile` files to use "weavr"
- [ ] T019 [P] [US1] Update environment variable prefixes in config files from `CODEBASE_RAG_` to `WEAVR_`
- [ ] T020 [P] [US1] Update database/graph node type prefixes in schema files from `codebase_rag` to `weavr`
- [ ] T021 [P] [US1] Update build scripts (`build_binary.py`, etc.) with new package name
- [ ] T022 [P] [US1] Update shell scripts (`init-project-graph.sh`, etc.) with new CLI command name
- [ ] T023 [P] [US1] Update Makefile targets and references to use "weavr"
- [ ] T024 [US1] Clear Python cache: Remove all `__pycache__` directories and `.pyc` files
- [ ] T025 [US1] Reinstall package: Run `uv pip uninstall graph-code && uv pip install -e .`
- [ ] T026 [US1] Verify CLI command works: Run `weavr --help` and verify no import errors
- [ ] T027 [US1] Run full test suite: Execute `uv run pytest` and verify 100% pass rate
- [ ] T028 [US1] Test all CLI commands: `weavr index`, `weavr chat`, `weavr mcp`, `weavr http`

**Checkpoint**: Core functionality complete - project works with new name, all tests pass

---

## Phase 4: User Story 2 - Documentation Accuracy (Priority: P2)

**Goal**: Ensure all documentation reflects the new "weavr" identity consistently

**Independent Test**: Search all markdown files for "code-graph-rag" references (`rg "code-graph-rag" --type md`) - should return zero results except in git history explanations

### Implementation for User Story 2

- [X] T029 [P] [US2] Update project name and description in `README.md` to "weavr"
- [X] T030 [P] [US2] Add attribution section in `README.md` crediting original code-graph-rag project
- [X] T031 [P] [US2] Update project identity and metaphor explanation in `CLAUDE.md`
- [X] T032 [P] [US2] Update all references to project name in `docs/ARCHITECTURE.md`
- [X] T033 [P] [US2] Update all references to project name in `docs/VISION.md`
- [X] T034 [P] [US2] Update CLI command examples in documentation from `graph-code` to `weavr`
- [X] T035 [P] [US2] Update installation instructions in `README.md` to use "weavr" package name
- [X] T036 [P] [US2] Search and update inline code comments referencing project name using `rg "code.graph.rag|graph-code" --type py`
- [X] T037 [P] [US2] Update contributing guidelines in `CONTRIBUTING.md` with new project name
- [X] T038 [P] [US2] Update any example code files in `examples/` directory to use new imports
- [X] T039 [P] [US2] Update configuration examples in `config/` directory with new naming
- [X] T040 [US2] Verify documentation consistency: Search for any remaining "code-graph-rag" references in docs
- [X] T041 [US2] Review and update MCP server configuration examples with new name

**Checkpoint**: Documentation complete - all docs consistently reference "weavr"

---

## Phase 5: User Story 3 - External Service Integration (Priority: P3)

**Goal**: Update direct integration points (service wrappers) to reference the renamed project

**Independent Test**: Verify service wrapper configurations reference "weavr" correctly and services can connect

### Implementation for User Story 3

- [ ] T042 [P] [US3] Update all references in `../http-service-wrappers/` to use "weavr" (if directory exists)
- [ ] T043 [P] [US3] Update all references in `../mcp-service-wrappers/` to use "weavr" (if directory exists)
- [ ] T044 [P] [US3] Update service configuration files in wrapper projects with new service name
- [ ] T045 [P] [US3] Update wrapper documentation to reference "weavr" instead of "code-graph-rag"
- [ ] T046 [US3] Test service wrapper connections: Start weavr server and verify wrappers can connect
- [ ] T047 [US3] Update any API endpoint paths in wrappers that reference the old name

**Checkpoint**: Service integrations updated - wrappers successfully connect to renamed service

---

## Phase 6: User Story 4 - Ecosystem-Wide Consistency (Priority: P4)

**Goal**: Ensure complete consistency across the entire ai_agency repository

**Independent Test**: Search entire ai_agency repo for "code-graph-rag" (`rg "code-graph-rag" ~/code/ai_agency/`) - verify only acceptable references remain

### Implementation for User Story 4

- [ ] T048 [US4] Search ai_agency repository for all references: `rg "code-graph-rag" ~/code/ai_agency/ --type-not md`
- [ ] T049 [P] [US4] Update project registry at `~/code/ai_agency/shared/scripts/registry/projects.json` using registry-manager.py
- [ ] T050 [P] [US4] Update any cross-project configuration files that reference this service
- [ ] T051 [P] [US4] Update any shared scripts that call the old CLI command name
- [ ] T052 [P] [US4] Update any AI agent configurations that reference code-graph-rag
- [ ] T053 [US4] Verify no code references remain: Run comprehensive search excluding git history and docs
- [ ] T054 [US4] Document the rename in shared ai_agency documentation (if applicable)

**Checkpoint**: Ecosystem consistency achieved - all ai_agency references updated

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cleanup, and prepare for repository rename

- [ ] T055 [P] Update GitHub-specific configurations: issue templates, workflow files in `.github/` directory
- [ ] T056 [P] Update any GitHub Actions workflows that reference the old package name
- [ ] T057 [P] Create migration notes for users documenting the rename
- [ ] T058 Run comprehensive validation: Execute all tests, check all CLI commands, verify documentation
- [ ] T059 Document GitHub repository rename instructions for manual completion by user
- [ ] T060 Prepare git commit with comprehensive rename changes
- [ ] T061 Review all changes and verify no breaking changes introduced

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - **US1 (Core Functionality)**: Must complete first - validates internal consistency
  - **US2 (Documentation)**: Can start after US1 or in parallel (different files)
  - **US3 (Service Integration)**: Should start after US1 completes (needs working service)
  - **US4 (Ecosystem Consistency)**: Can run after US1 completes
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories - MUST COMPLETE FIRST
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent from other stories
- **User Story 3 (P3)**: Can start after User Story 1 (needs working renamed service)
- **User Story 4 (P4)**: Can start after User Story 1 (needs internal consistency first)

### Within Each User Story

#### User Story 1 (Core Functionality):
1. Package rename tasks (T008-T015) can run in parallel - different files
2. Config updates (T017-T023) can run in parallel - different files
3. Cache cleanup and reinstall (T024-T025) must run sequentially after code changes
4. Validation tasks (T026-T028) must run last in sequence

#### User Story 2 (Documentation):
1. All documentation updates (T029-T041) can run in parallel - different files
2. Final verification (T040-T041) should run after updates

#### User Story 3 (Service Integration):
1. Wrapper updates (T042-T045) can run in parallel - different repositories
2. Connection tests (T046-T047) must run after wrapper updates

#### User Story 4 (Ecosystem Consistency):
1. Search first (T048), then parallel updates (T049-T052)
2. Final verification (T053-T054) runs last

### Parallel Opportunities

- **Phase 1 (Setup)**: All tasks sequential (verification tasks)
- **Phase 2 (Foundational)**: All tasks sequential (interdependent rename operations)
- **Within User Story 1**: Import updates (T008-T015) can run in parallel, config updates (T017-T023) can run in parallel
- **Within User Story 2**: All documentation updates (T029-T039) can run in parallel
- **Within User Story 3**: Wrapper updates (T042-T045) can run in parallel
- **Within User Story 4**: Registry and config updates (T049-T052) can run in parallel after search
- **Cross-Story Parallelization**: US2 can run in parallel with US1 completion verification

---

## Parallel Example: User Story 1

```bash
# After Foundational phase completes:

# Launch all import updates together:
Task: "Update all import statements in weavr/main.py from codebase_rag to weavr"
Task: "Update all import statements in weavr/mcp/ files from codebase_rag to weavr"
Task: "Update all import statements in weavr/http/ files from codebase_rag to weavr"
Task: "Update all import statements in weavr/parsers/ files from codebase_rag to weavr"
Task: "Update all import statements in weavr/services/ files from codebase_rag to weavr"
Task: "Update all import statements in weavr/tools/ files from codebase_rag to weavr"
Task: "Update all import statements in tests/ files from codebase_rag to weavr"

# Then launch all config updates together:
Task: "Update Docker Compose service names in docker-compose.yaml to use weavr prefix"
Task: "Update Docker image names and labels in Dockerfile files to use weavr"
Task: "Update environment variable prefixes in config files from CODEBASE_RAG_ to WEAVR_"
Task: "Update database/graph node type prefixes in schema files from codebase_rag to weavr"
Task: "Update build scripts (build_binary.py, etc.) with new package name"
Task: "Update shell scripts (init-project-graph.sh, etc.) with new CLI command name"
Task: "Update Makefile targets and references to use weavr"
```

---

## Parallel Example: User Story 2

```bash
# All documentation updates can run together:
Task: "Update project name and description in README.md to weavr"
Task: "Add attribution section in README.md crediting original code-graph-rag project"
Task: "Update project identity and metaphor explanation in CLAUDE.md"
Task: "Update all references to project name in docs/ARCHITECTURE.md"
Task: "Update all references to project name in docs/VISION.md"
Task: "Update CLI command examples in documentation from graph-code to weavr"
Task: "Update installation instructions in README.md to use weavr package name"
Task: "Update contributing guidelines in CONTRIBUTING.md with new project name"
Task: "Update any example code files in examples/ directory to use new imports"
Task: "Update configuration examples in config/ directory with new naming"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (backup and baseline)
2. Complete Phase 2: Foundational (core package rename)
3. Complete Phase 3: User Story 1 (internal code consistency)
4. **STOP and VALIDATE**: Run full test suite, test all CLI commands
5. If all tests pass, US1 is complete - project is functional with new name

### Incremental Delivery

1. Complete Setup + Foundational → Core rename done
2. Add User Story 1 → Test independently → **MVP Complete** (functional "weavr" project)
3. Add User Story 2 → Test independently → Documentation consistent
4. Add User Story 3 → Test independently → Service integrations updated
5. Add User Story 4 → Test independently → Full ecosystem consistency
6. Polish phase → Ready for repository rename

### Sequential Strategy (Recommended)

Since this is a rename operation with cascading effects:

1. Setup + Foundational must complete first
2. User Story 1 MUST complete and validate before other stories
3. User Story 2 can proceed after US1 validation (parallel to US3/US4)
4. User Story 3 should proceed after US1 (needs working service)
5. User Story 4 can proceed after US1 (needs internal consistency)
6. Polish after all stories complete

---

## Notes

- **[P]** tasks = different files, no dependencies
- **[Story]** label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each phase or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: Clear Python cache and reinstall package after code changes
- **GitHub rename**: User must manually rename repository after all code changes complete
- **Attribution**: Maintain credit to original code-graph-rag project in documentation
- **Git history**: Old references in commit history are acceptable and expected

---

## Task Summary

- **Total Tasks**: 61
- **Setup Phase**: 3 tasks
- **Foundational Phase**: 4 tasks (BLOCKING)
- **User Story 1**: 21 tasks (Core functionality)
- **User Story 2**: 13 tasks (Documentation)
- **User Story 3**: 6 tasks (Service integration)
- **User Story 4**: 7 tasks (Ecosystem consistency)
- **Polish Phase**: 7 tasks

**Parallel Opportunities**:
- Within US1: 14 parallelizable tasks (import and config updates)
- Within US2: 11 parallelizable tasks (documentation updates)
- Within US3: 4 parallelizable tasks (wrapper updates)
- Within US4: 4 parallelizable tasks (registry and config updates)

**Independent Test Criteria**:
- US1: All tests pass, CLI commands work
- US2: Zero old name references in docs
- US3: Service wrappers connect successfully
- US4: Zero code references in ecosystem (excluding git history)

**Suggested MVP Scope**: Setup + Foundational + User Story 1 (28 tasks total)
