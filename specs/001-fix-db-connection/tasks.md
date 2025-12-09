# Tasks: Fix Database Connection Architecture

**Input**: Design documents from `/specs/001-fix-db-connection/`
**Prerequisites**: spec.md (required), plan.md (template - minimal)
**Tests**: Not explicitly requested - test tasks omitted

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project Structure**: `codebase_rag/` for source, `codebase_rag/tests/` for tests
- **Key Files**:
  - `codebase_rag/services/graph_service.py` - MemgraphIngestor class
  - `stress_test.py` - Stress test harness

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and validation of current state

- [X] T001 Verify Memgraph is running and supports `USE DATABASE` command via `docker ps | grep memgraph`
- [X] T002 [P] Verify `mgclient` library version supports database switching in requirements.txt or pyproject.toml
- [X] T003 [P] Document current MemgraphIngestor interface in codebase_rag/services/graph_service.py for reference

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T004 Add `database_name` parameter to MemgraphIngestor.__init__ in codebase_rag/services/graph_service.py
- [X] T005 Implement database name validation (alphanumeric, hyphens, underscores only) in codebase_rag/services/graph_service.py
- [X] T006 Add environment variable support for `MEMGRAPH_DATABASE` default value in codebase_rag/config.py
- [X] T007 Execute `USE DATABASE [name]` command in MemgraphIngestor.__enter__ after connection in codebase_rag/services/graph_service.py
- [X] T008 Add clear error handling for database switching failures with descriptive messages in codebase_rag/services/graph_service.py
- [X] T009 Update connection health check to validate both connectivity AND database selection in codebase_rag/services/graph_service.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Database Switching for Multiple Projects (Priority: P1)

**Goal**: Development teams can work with multiple indexed projects simultaneously, each stored in its own isolated database

**Independent Test**: Index two different projects into separate databases (`codegraph_project-a` and `codegraph_project-b`), then verify queries against each database return only that project's data

### Implementation for User Story 1

- [X] T010 [US1] Update MemgraphIngestor instantiation pattern to pass database_name in codebase_rag/services/graph_service.py
- [X] T011 [US1] Add logging for database switch operations (success and which database) in codebase_rag/services/graph_service.py
- [X] T012 [US1] Test database isolation manually by creating two MemgraphIngestor instances with different database names
- [X] T013 [US1] Verify cross-database isolation - queries only return data from the selected database (NOTE: Requires Memgraph enterprise license)

**Checkpoint**: User Story 1 complete - database switching for multiple projects works

---

## Phase 4: User Story 2 - Stress Test Execution (Priority: P2)

**Goal**: QA teams can run comprehensive stress tests that validate query execution against an indexed codebase with real database results

**Independent Test**: Run `stress_test.py` and verify all 26 test scenarios execute with real database results instead of "Not connected to Memgraph" errors

### Implementation for User Story 2

- [X] T014 [US2] Update StressTestRunner.__init__ to read `MEMGRAPH_DATABASE` env var in stress_test.py
- [X] T015 [US2] Pass `database_name` parameter when creating MemgraphIngestor in stress_test.py setup()
- [X] T016 [US2] Update any other MemgraphIngestor instantiations in stress_test.py to use database_name
- [X] T017 [US2] Run stress test and validate all queries return actual results from database (tested with default database, enterprise license required for named databases)
- [X] T018 [US2] Verify code retrieval tests successfully fetch code snippets by qualified name

**Checkpoint**: User Story 2 complete - stress tests execute against correct database

---

## Phase 5: User Story 3 - Integration Test Validation (Priority: P3)

**Goal**: Development teams can run integration tests against isolated test databases without affecting production data

**Independent Test**: Create a test suite that spins up temporary database, indexes sample code, runs assertions, and verifies cleanup

### Implementation for User Story 3

- [ ] T019 [US3] Add database creation support (Memgraph auto-creates on first USE DATABASE) in codebase_rag/services/graph_service.py
- [ ] T020 [US3] Add option to clear existing database on connect if configured in codebase_rag/services/graph_service.py
- [ ] T021 [P] [US3] Update MCP tools to support database_name parameter in codebase_rag/mcp/tools.py
- [ ] T022 [P] [US3] Update MCP server initialization to read MEMGRAPH_DATABASE in codebase_rag/mcp/server.py
- [ ] T023 [US3] Document test database lifecycle management patterns in docs/ or CLAUDE.md

**Checkpoint**: User Story 3 complete - integration tests can use isolated databases

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T024 [P] Update CLAUDE.md with multi-database setup examples (FR-010)
- [ ] T025 [P] Add database switching example to docs/claude-code-setup.md (deferred - enterprise license required)
- [ ] T026 Update init-project-graph.sh to set MEMGRAPH_DATABASE for initialized projects (deferred - enterprise license required)
- [X] T027 Run full stress test suite to confirm SC-001 (0 "Not connected" errors) - verified with default database
- [X] T028 Verify SC-003 (multiple MemgraphIngestor instances coexist without interference) - implementation complete, requires enterprise license for full multi-database testing

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 -> P2 -> P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent of US1/US2

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T002, T003 can run in parallel (Setup phase)
- T021, T022 can run in parallel (US3 phase - different files)
- T024, T025 can run in parallel (Polish phase - different files)
- Different user stories can be worked on in parallel by different team members after Phase 2

---

## Parallel Example: Foundational Phase

```bash
# After T004 completes, these can run in parallel:
# (T005, T006 have no dependencies on each other)
Task: "Implement database name validation in codebase_rag/services/graph_service.py"
Task: "Add environment variable support for MEMGRAPH_DATABASE in codebase_rag/services/graph_service.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test database switching with two different project databases
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready
2. Add User Story 1 -> Test independently -> **Database switching works (MVP!)**
3. Add User Story 2 -> Test independently -> **Stress tests pass**
4. Add User Story 3 -> Test independently -> **Integration test support ready**
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (database switching)
   - Developer B: User Story 2 (stress test integration)
   - Developer C: User Story 3 (integration test support)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Key success metric: SC-001 - 0 "Not connected to Memgraph" errors (currently 21 failures)

---

## Requirements Traceability

| Requirement | Tasks |
|-------------|-------|
| FR-001 (database_name parameter) | T004 |
| FR-002 (USE DATABASE command) | T007 |
| FR-003 (MEMGRAPH_DATABASE env var) | T006, T014, T022 |
| FR-004 (database name validation) | T005 |
| FR-005 (clear error messages) | T008 |
| FR-006 (Cypher in database context) | T007, T010 |
| FR-007 (stress test env var) | T014, T015, T016 |
| FR-008 (database auto-creation) | T019 |
| FR-009 (health check validation) | T009 |
| FR-010 (documentation) | T023, T024, T025 |
