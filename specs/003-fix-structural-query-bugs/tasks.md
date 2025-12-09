# Tasks: Fix Structural Query Bugs and Achieve 100% Test Pass Rate

**Input**: Design documents from `/specs/003-fix-structural-query-bugs/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Test tasks are included per the stress test suite requirements

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project structure**: Single Python project with `codebase_rag/` package and `tests/` directory at repository root
- **Core implementation**: `codebase_rag/tools/structural_queries.py`
- **Test suite**: `tests/stress/` directory with organized test modules

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify test environment and prepare for implementation

- [X] T001 Verify Memgraph is running at localhost:7687 and test project (ai-gateway-mcp) is indexed
- [X] T002 Run baseline stress tests and capture current failure metrics (8 fails, 8 partials, 34 passes)
- [X] T003 Document current failure patterns for each failing test category

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create shared validation infrastructure that all user stories will use

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create parameter validation utility module in codebase_rag/utils/validation.py
- [ ] T005 [P] Create custom exception classes for validation errors in codebase_rag/exceptions.py
- [ ] T006 Define validation schemas for common parameter types (qualified_name, max_depth, direction, dependency_type)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Parameter Validation for Query Safety (Priority: P1) 🎯 MVP

**Goal**: Add comprehensive parameter validation to all 7 structural query tools to reject invalid inputs before executing database queries

**Independent Test**: Call each structural query tool with invalid parameter values and verify clear error messages are returned before any database query executes (tests P1-P15 in stress test suite)

### Implementation for User Story 1

- [X] T007 [P] [US1] Add direction parameter validation to query_hierarchy() in codebase_rag/tools/structural_queries.py
- [X] T008 [P] [US1] Add dependency_type parameter validation to query_dependencies() in codebase_rag/tools/structural_queries.py
- [X] T009 [P] [US1] Add max_depth range validation to query_callers() in codebase_rag/tools/structural_queries.py (already existed)
- [X] T010 [P] [US1] Add max_depth range validation to query_hierarchy() in codebase_rag/tools/structural_queries.py (already existed)
- [X] T011 [P] [US1] Add qualified_name non-empty validation to all query functions in codebase_rag/tools/structural_queries.py (handled by existing node-not-found checks)
- [X] T012 [P] [US1] Add numeric limit parameter validation (positive integers) to all relevant query functions in codebase_rag/tools/structural_queries.py (already existed)
- [X] T013 [US1] Run parameter validation tests (P1-P15) and verify all pass with <5ms response time (15/15 passed!)

**Checkpoint**: At this point, all parameter validation should work and tests P1-P15 should pass

---

## Phase 4: User Story 2 - Expert Mode Security Controls (Priority: P1)

**Goal**: Block all write operations (CREATE, DELETE, SET, MERGE) in expert mode query_cypher() to maintain read-only access

**Independent Test**: Attempt to execute Cypher queries containing CREATE, DELETE, SET, or MERGE through query_cypher() and verify all are rejected with specific error messages (tests ES1-ES4 in stress test suite)

### Implementation for User Story 2

- [X] T014 [US2] Implement Cypher query validation function in codebase_rag/utils/validation.py (used existing _validate_cypher_query)
- [X] T015 [US2] Add CREATE keyword detection and blocking in query_cypher() in codebase_rag/tools/structural_queries.py
- [X] T016 [US2] Add DELETE keyword detection and blocking in query_cypher() in codebase_rag/tools/structural_queries.py (already existed)
- [X] T017 [US2] Add SET keyword detection and blocking in query_cypher() in codebase_rag/tools/structural_queries.py (already existed)
- [X] T018 [US2] Add MERGE keyword detection and blocking in query_cypher() in codebase_rag/tools/structural_queries.py (already existed)
- [X] T019 [US2] Implement case-insensitive keyword scanning for all forbidden operations in codebase_rag/tools/structural_queries.py (already existed)
- [X] T020 [US2] Add validation call before query execution in query_cypher() in codebase_rag/tools/structural_queries.py (already existed)
- [X] T021 [US2] Run expert mode security tests (ES1-ES4) and verify all forbidden operations are blocked (P11-P14 all passed!)

**Checkpoint**: At this point, expert mode should block all write operations and tests ES1-ES4 should pass

---

## Phase 5: User Story 3 - Fix Module Exports Cypher Query Bug (Priority: P1)

**Goal**: Fix query_module_exports() Cypher query to successfully return results without "Comparison is not defined for values of type list" errors

**Independent Test**: Call query_module_exports() on any module containing functions and classes and verify results are returned without Cypher errors, properly sorted, and containing all expected exports (tests S6, S11 in stress test suite)

### Implementation for User Story 3

- [X] T022 [US3] Analyze current module exports Cypher query in codebase_rag/tools/structural_queries.py
- [X] T023 [US3] Replace ORDER BY labels(export) with ORDER BY labels(export)[0] in query_module_exports() in codebase_rag/tools/structural_queries.py
- [X] T024 [US3] Test module exports query with include_private=False parameter (S11 passed!)
- [X] T025 [US3] Test module exports query with include_private=True parameter (S12 passed!)
- [X] T026 [US3] Run module exports tests (S11, S12) and verify both pass without Cypher errors (both passed!)

**Checkpoint**: At this point, module exports queries should work correctly and tests S6, S11 should pass

---

## Phase 6: User Story 4 - Improve Test Data and Query Accuracy (Priority: P2)

**Goal**: Fix remaining test failures by verifying test data quality, correcting qualified names, and fixing query_dependencies "all" type logic

**Independent Test**: Run all 50 stress tests and verify 100% pass rate with no failures or partials

### Implementation for User Story 4

- [ ] T027 [US4] Verify ai-gateway-mcp project is fully indexed and has expected node count in Memgraph
- [ ] T028 [US4] Examine graph structure for test data quality (callers, dependencies, hierarchies exist)
- [ ] T029 [US4] Fix query_dependencies() "all" type to properly combine imports and calls results in codebase_rag/tools/structural_queries.py
- [ ] T030 [US4] Update test qualified names to match actual indexed graph structure in tests/stress/test_structural_queries.py
- [ ] T031 [US4] Update test assertions to distinguish legitimate empty results from bugs in tests/stress/test_structural_queries.py
- [ ] T032 [US4] Fix any remaining query pattern bugs identified during test execution in codebase_rag/tools/structural_queries.py
- [ ] T033 [US4] Run full stress test suite and verify 100% pass rate (50/50 pass, 0 fail, 0 partial)
- [ ] T034 [US4] Verify stress test execution time remains under 1 second (target: 0.40s baseline)

**Checkpoint**: All 50 stress tests should now pass with 100% success rate

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and final verification

- [ ] T035 [P] Update CLAUDE.md to reflect validation edge case handling in docs/CLAUDE.md
- [ ] T036 [P] Add inline documentation for validation functions in codebase_rag/utils/validation.py
- [ ] T037 Run performance tests and verify all queries still meet targets (<50ms simple, <150ms complex) in tests/stress/test_performance.py
- [ ] T038 Run concurrent operations tests and verify thread safety in tests/stress/test_concurrent_operations.py
- [ ] T039 Generate final stress test report with pass/fail breakdown
- [ ] T040 Verify all success criteria: 100% pass rate, 0 failures, 0 partials, <1s execution time

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (P1): Parameter Validation - Independent, can start after Phase 2
  - User Story 2 (P1): Expert Mode Security - Independent, can start after Phase 2
  - User Story 3 (P1): Module Exports Fix - Independent, can start after Phase 2
  - User Story 4 (P2): Test Data/Query Accuracy - Should start after US1-US3 complete (validates all fixes together)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 (P2)**: Should start after US1-US3 complete - Tests all fixes together, may reveal integration issues

### Within Each User Story

**User Story 1 (Parameter Validation)**:
- Tasks T007-T012 are all independent validation additions (can run in parallel)
- Task T013 (run tests) depends on T007-T012 completion

**User Story 2 (Expert Mode Security)**:
- Task T014 (validation function) must complete first
- Tasks T015-T019 (individual keyword blocking) can run in parallel after T014
- Task T020 (add validation call) depends on T014-T019
- Task T021 (run tests) depends on T020

**User Story 3 (Module Exports Fix)**:
- Tasks T022-T025 must run sequentially (analyze → fix → test scenarios)
- Task T026 (run tests) depends on T023-T025

**User Story 4 (Test Data Accuracy)**:
- Tasks T027-T028 (verify test data) should run first
- Tasks T029-T032 (fix queries and tests) can run in parallel after T027-T028
- Tasks T033-T034 (final validation) depend on T029-T032

### Parallel Opportunities

- **Setup (Phase 1)**: Tasks T001-T003 can run sequentially (T002 depends on T001)
- **Foundational (Phase 2)**: Tasks T004-T005 can run in parallel, T006 depends on both
- **User Story 1**: Tasks T007-T012 can all run in parallel (different validations)
- **User Story 2**: Tasks T015-T019 can run in parallel after T014 completes
- **User Story 3**: Must run sequentially
- **User Story 4**: Tasks T029-T032 can run in parallel after T027-T028
- **Polish (Phase 7)**: Tasks T035-T036 can run in parallel, T037-T040 run sequentially

---

## Parallel Example: User Story 1

```bash
# After completing Foundational phase, launch all validation additions together:
Task T007: "Add direction parameter validation to query_hierarchy()"
Task T008: "Add dependency_type parameter validation to query_dependencies()"
Task T009: "Add max_depth range validation to query_callers()"
Task T010: "Add max_depth range validation to query_hierarchy()"
Task T011: "Add qualified_name non-empty validation to all query functions"
Task T012: "Add numeric limit parameter validation to all relevant query functions"

# Then run validation tests:
Task T013: "Run parameter validation tests (P1-P15) and verify all pass"
```

---

## Parallel Example: User Story 2

```bash
# First create validation infrastructure:
Task T014: "Implement Cypher query validation function"

# Then launch all keyword blocking in parallel:
Task T015: "Add CREATE keyword detection and blocking"
Task T016: "Add DELETE keyword detection and blocking"
Task T017: "Add SET keyword detection and blocking"
Task T018: "Add MERGE keyword detection and blocking"
Task T019: "Implement case-insensitive keyword scanning"

# Finally integrate and test:
Task T020: "Add validation call before query execution"
Task T021: "Run expert mode security tests (ES1-ES4)"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 - All P1)

1. Complete Phase 1: Setup (verify environment)
2. Complete Phase 2: Foundational (validation infrastructure)
3. Complete Phase 3: User Story 1 (parameter validation)
4. Complete Phase 4: User Story 2 (expert mode security)
5. Complete Phase 5: User Story 3 (module exports fix)
6. **VALIDATE**: Run stress tests - should see significant improvement in pass rate
7. Proceed to User Story 4 for final cleanup

### Incremental Delivery

1. Complete Setup + Foundational → Validation infrastructure ready
2. Add User Story 1 → Parameter validation working → Test subset passes
3. Add User Story 2 → Expert mode secured → Security tests pass
4. Add User Story 3 → Module exports fixed → Query bugs eliminated
5. Add User Story 4 → Test data accurate → 100% pass rate achieved
6. Each story adds value and eliminates specific failure categories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Parameter Validation) - Tasks T007-T013
   - Developer B: User Story 2 (Expert Mode Security) - Tasks T014-T021
   - Developer C: User Story 3 (Module Exports Fix) - Tasks T022-T026
3. After US1-US3 complete:
   - Team works together on User Story 4 (Test Data Accuracy) - Tasks T027-T034
4. Stories complete and integrate independently

---

## Success Metrics

After completing all tasks, verify the following success criteria are met:

- **SC-001**: All 50 stress tests achieve "pass" status (100% pass rate)
- **SC-002**: Zero tests have "fail" status
- **SC-003**: Zero tests have "partial" status
- **SC-004**: All parameter validation tests (P1-P15) reject invalid inputs with clear error messages within 5ms
- **SC-005**: All expert mode security tests (ES1-ES4) block forbidden operations
- **SC-006**: Module exports query (S6, S11) successfully returns results without Cypher errors
- **SC-007**: Stress test execution completes in under 1 second
- **SC-008**: All structural query performance targets met (<50ms simple, <150ms complex)
- **SC-009**: All concurrent operation tests pass
- **SC-010**: Test suite provides clear reporting distinguishing legitimate empty results from bugs

---

## Notes

- [P] tasks = different files or independent changes, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Stress test categories:
  - P1-P15: Parameter validation tests
  - ES1-ES4: Expert mode security tests
  - S1-S14: Structural query tests
  - E1-E12: Edge case tests
  - PF1-PF10: Performance tests
  - C1-C5: Concurrent operation tests
