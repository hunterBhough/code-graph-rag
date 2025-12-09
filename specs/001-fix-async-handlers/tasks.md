# Tasks: Fix Async Handlers for Structural Query Tools

**Input**: Design documents from `/specs/001-fix-async-handlers/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify environment and understand existing code structure

- [X] T001 Verify Memgraph is running with `docker ps | grep memgraph`
- [X] T002 Run stress test to capture baseline failure state with `uv run stress_test.py`

---

## Phase 2: Foundational (Core Handler Changes)

**Purpose**: Make all 7 structural query tool handlers async - this is the core fix that all user stories depend on

**CRITICAL**: No user story validation can begin until this phase is complete

### Identify the 7 Handlers to Fix

The handlers are the inner functions returned by these `create_*_tool()` functions in `codebase_rag/tools/structural_queries.py`:

1. `create_find_callers_tool` → `find_callers` handler (line 554-567)
2. `create_class_hierarchy_tool` → `class_hierarchy` handler (line 2107-2122)
3. `create_dependency_analysis_tool` → `dependency_analysis` handler (line 926-941)
4. `create_interface_implementations_tool` → `interface_implementations` handler (line 1229-1242)
5. `create_expert_mode_tool` → `expert_mode_cypher` handler (line 1501-1516)
6. `create_call_graph_tool` → `call_graph_generator` handler (line 1835-1850)
7. `create_module_exports_tool` → `module_exports` handler (line 2269-2281)

### Implementation Tasks

- [X] T003 [P] Convert `find_callers` handler to async in codebase_rag/tools/structural_queries.py:554-567
- [X] T004 [P] Convert `class_hierarchy` handler to async in codebase_rag/tools/structural_queries.py:2107-2122
- [X] T005 [P] Convert `dependency_analysis` handler to async in codebase_rag/tools/structural_queries.py:926-941
- [X] T006 [P] Convert `interface_implementations` handler to async in codebase_rag/tools/structural_queries.py:1229-1242
- [X] T007 [P] Convert `expert_mode_cypher` handler to async in codebase_rag/tools/structural_queries.py:1501-1516
- [X] T008 [P] Convert `call_graph_generator` handler to async in codebase_rag/tools/structural_queries.py:1835-1850
- [X] T009 [P] Convert `module_exports` handler to async in codebase_rag/tools/structural_queries.py:2269-2281

**Checkpoint**: All 7 handlers are now async functions

---

## Phase 3: User Story 1 - Stress Tests Pass (Priority: P1)

**Goal**: All structural query tests (S1-S7) and edge case tests (E6-E15) pass without async-related errors

**Independent Test**: Run `uv run stress_test.py` and verify S1-S7 tests pass

### Validation Tasks

- [X] T010 [US1] Run stress test and verify S1 (query_callers basic) passes
- [X] T011 [US1] Run stress test and verify S2 (query_hierarchy basic) passes
- [X] T012 [US1] Run stress test and verify S3 (query_dependencies basic) passes
- [X] T013 [US1] Run stress test and verify S4 (query_implementations basic) passes
- [X] T014 [US1] Run stress test and verify S5 (query_call_graph basic) passes
- [X] T015 [US1] Run stress test and verify S6 (query_module_exports basic) passes
- [X] T016 [US1] Run stress test and verify S7 (query_cypher expert mode) passes
- [X] T017 [US1] Run stress test and verify edge case tests E6-E15 pass (no "dict can't be awaited" errors)

**Checkpoint**: User Story 1 complete - structural query tests pass

---

## Phase 4: User Story 2 - Concurrent Operations Work (Priority: P1)

**Goal**: Concurrent query operations (CONC1-CONC4) function correctly with asyncio.gather()

**Independent Test**: Run `uv run stress_test.py` and verify CONC1-CONC4 tests pass

### Validation Tasks

- [X] T018 [US2] Run stress test and verify CONC1 (concurrent structural queries) passes
- [X] T019 [US2] Run stress test and verify CONC2 (concurrent mixed operations) passes
- [X] T020 [US2] Run stress test and verify CONC3 (high load - 10 concurrent) passes with 80%+ success
- [X] T021 [US2] Run stress test and verify CONC4 (concurrent error handling) passes

**Checkpoint**: User Story 2 complete - concurrent operations work

---

## Phase 5: User Story 3 - MCP Server Tool Invocation Works (Priority: P1)

**Goal**: MCP server can successfully invoke any structural query tool

**Independent Test**: Start MCP server and invoke `query_callers` tool via MCP protocol

### Validation Tasks

- [X] T022 [US3] Run stress test and verify MCP4 (return type consistency) passes
- [X] T023 [US3] Verify MCP server starts without errors with `uv run -m mcp_server.server`
- [X] T024 [US3] Verify project isolation tests ISO1-ISO3 pass

**Checkpoint**: User Story 3 complete - MCP server integration works

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and success criteria verification

- [X] T025 Run full stress test suite and verify pass rate improves from 37.7% to at least 80%
- [X] T026 Verify all 7 structural query tests (S1-S7) pass - SC-002
- [X] T027 Verify all 4 concurrent operation tests (CONC1-CONC4) pass - SC-003
- [X] T028 Verify all edge case tests (E6-E15) pass - SC-004
- [X] T029 Verify MCP integration test MCP4 passes - SC-005
- [X] T030 Verify project isolation tests (ISO1-ISO3) pass - SC-006

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can proceed in parallel after Phase 2 (validation only)
  - Or sequentially in priority order (P1 → P1 → P1)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Validates core fix
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Validates concurrency
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - Validates MCP integration

### Within Phase 2

- All tasks T003-T009 are parallelizable - they modify different functions in the same file
- Each change is independent: `def handler_name(...):` → `async def handler_name(...):`

### Parallel Opportunities

- T003-T009 can all run in parallel (different functions, same pattern)
- T010-T017 can run after Phase 2 completes (all part of stress test validation)
- T018-T021 can run after Phase 2 completes
- T022-T024 can run after Phase 2 completes

---

## Parallel Example: Phase 2 (Foundational)

```bash
# All 7 handler conversions can be done in parallel:
Task: "Convert find_callers handler to async in codebase_rag/tools/structural_queries.py:554-567"
Task: "Convert class_hierarchy handler to async in codebase_rag/tools/structural_queries.py:2107-2122"
Task: "Convert dependency_analysis handler to async in codebase_rag/tools/structural_queries.py:926-941"
Task: "Convert interface_implementations handler to async in codebase_rag/tools/structural_queries.py:1229-1242"
Task: "Convert expert_mode_cypher handler to async in codebase_rag/tools/structural_queries.py:1501-1516"
Task: "Convert call_graph_generator handler to async in codebase_rag/tools/structural_queries.py:1835-1850"
Task: "Convert module_exports handler to async in codebase_rag/tools/structural_queries.py:2269-2281"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify environment)
2. Complete Phase 2: Foundational (convert all 7 handlers to async)
3. Complete Phase 3: User Story 1 (validate stress tests pass)
4. **STOP and VALIDATE**: Run `uv run stress_test.py` and check S1-S7 pass
5. If passing, continue to User Story 2 and 3

### The Actual Code Changes

Each handler change follows this exact pattern:

**Before:**
```python
def handler_name(
    param1: type1,
    param2: type2 = default,
) -> dict[str, Any]:
    """Docstring."""
    return query_tool.execute(ingestor, param1, param2)
```

**After:**
```python
async def handler_name(
    param1: type1,
    param2: type2 = default,
) -> dict[str, Any]:
    """Docstring."""
    return query_tool.execute(ingestor, param1, param2)
```

The only change is adding `async` before `def`. The function body remains identical because:
- The underlying `query_tool.execute()` calls are synchronous
- Making the handler async allows it to be awaited by the MCP server
- No actual async I/O is performed inside these handlers

---

## Notes

- [P] tasks = different files or independent functions, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable after Phase 2 completion
- All user stories are P1 priority (equally critical)
- The fix is minimal: just adding `async` keyword to 7 function definitions
- Avoid: changing function logic, modifying return types, or breaking existing behavior
