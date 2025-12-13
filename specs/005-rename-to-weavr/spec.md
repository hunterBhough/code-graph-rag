# Feature Specification: Rename Project to Weavr

**Feature Branch**: `005-rename-to-weavr`
**Created**: 2025-12-13
**Status**: Draft
**Input**: User description: "Rename project from code-graph-rag to weavr across all code, documentation, and external references"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Project Functionality (Priority: P1)

Developer can use the renamed project without any errors or broken references.

**Why this priority**: This is the foundation - if internal code doesn't work after the rename, nothing else matters. All functionality must continue working seamlessly.

**Independent Test**: Can be fully tested by running the full test suite after renaming all internal code references. Delivers a working project with new name.

**Acceptance Scenarios**:

1. **Given** the project has been renamed internally, **When** a developer runs the test suite, **Then** all tests pass without errors
2. **Given** the project has been renamed, **When** a developer imports modules using new names, **Then** all imports resolve correctly
3. **Given** the CLI has been renamed, **When** a developer runs `weavr` commands, **Then** all commands execute successfully
4. **Given** package metadata has been updated, **When** a developer installs the package, **Then** it installs with the name `weavr`

---

### User Story 2 - Documentation Accuracy (Priority: P2)

Developer reading documentation sees accurate project name and understands the project's identity.

**Why this priority**: After core functionality works, documentation must be consistent to avoid confusion for new and existing users.

**Independent Test**: Can be fully tested by reviewing all documentation files and verifying they reference "weavr" consistently. Delivers clear project identity.

**Acceptance Scenarios**:

1. **Given** all documentation has been updated, **When** a developer reads README.md, **Then** they see "weavr" as the project name with correct description
2. **Given** documentation has been updated, **When** a developer reads ARCHITECTURE.md and VISION.md, **Then** all references use "weavr" consistently
3. **Given** CLAUDE.md has been updated, **When** a developer or AI assistant reads it, **Then** they understand this is the weavr project
4. **Given** inline code comments reference the project, **When** a developer reads them, **Then** they use "weavr" terminology

---

### User Story 3 - External Service Integration (Priority: P3)

Other services in the ai_agency ecosystem can correctly reference and use the renamed project.

**Why this priority**: After internal consistency is achieved, external integrations need to be updated to maintain ecosystem coherence.

**Independent Test**: Can be fully tested by verifying that http-service-wrappers and mcp-service-wrappers reference the new name correctly. Delivers cross-service compatibility.

**Acceptance Scenarios**:

1. **Given** http-service-wrappers has been updated, **When** it references this project, **Then** it uses "weavr" in all configurations and documentation
2. **Given** mcp-service-wrappers has been updated, **When** it references this project, **Then** it uses "weavr" in all configurations and documentation
3. **Given** service configurations have been updated, **When** services try to connect to weavr, **Then** connections succeed with new naming

---

### User Story 4 - Ecosystem-Wide Consistency (Priority: P4)

Any project across the entire ai_agency repository that references this tool uses the correct name.

**Why this priority**: While important for long-term consistency, scattered references in other projects are lower priority than core functionality and direct integrations.

**Independent Test**: Can be fully tested by searching all ai_agency projects for old references and verifying they've been updated. Delivers complete ecosystem consistency.

**Acceptance Scenarios**:

1. **Given** all ai_agency projects have been searched, **When** looking for "code-graph-rag" references, **Then** no references to the old name remain
2. **Given** project registry has been updated, **When** other tools query the registry, **Then** they see "weavr" as the correct project name
3. **Given** cross-project documentation has been updated, **When** developers read about available tools, **Then** they see "weavr" listed

---

### Edge Cases

- What happens when old Docker images exist with code-graph-rag naming?
- What happens when cached dependencies reference the old package name?
- What happens when git history references the old name in commit messages?
- What happens when external GitHub users have forked the repository with the old name?
- What happens when MCP client configurations still reference code-graph-rag?

## Requirements *(mandatory)*

### Functional Requirements

**Internal Code Updates:**
- **FR-001**: System MUST rename all Python module references from `codebase_rag` to `weavr`
- **FR-002**: System MUST update package name in pyproject.toml from code-graph-rag to weavr
- **FR-003**: System MUST update all import statements throughout the codebase
- **FR-004**: System MUST rename the main Python package directory from `codebase_rag/` to `weavr/`
- **FR-005**: System MUST update CLI command names from `graph-code` to `weavr`

**Configuration and Infrastructure:**
- **FR-006**: System MUST update Docker Compose service names and image references
- **FR-007**: System MUST update Dockerfile labels and metadata
- **FR-008**: System MUST update environment variable names that reference the project
- **FR-009**: System MUST update any database or graph node type prefixes from codebase_rag to weavr

**Documentation Updates:**
- **FR-010**: System MUST update README.md with new project name and description
- **FR-011**: System MUST update CLAUDE.md with new project name and metaphor explanation
- **FR-012**: System MUST update ARCHITECTURE.md with new project name
- **FR-013**: System MUST update VISION.md with new project name and identity
- **FR-014**: System MUST update any inline code comments that reference the project name
- **FR-015**: System MUST add attribution note in README crediting original code-graph-rag project

**External Service References:**
- **FR-016**: System MUST update all references in ../http-service-wrappers
- **FR-017**: System MUST update all references in ../mcp-service-wrappers
- **FR-018**: System MUST search and update references across entire ai_agency repository
- **FR-019**: System MUST update project registry at ~/code/ai_agency/shared/scripts/registry/projects.json

**GitHub and Version Control:**
- **FR-020**: User MUST manually rename GitHub repository from code-graph-rag to weavr
- **FR-021**: System MUST verify git remotes point to correctly renamed repository after manual rename
- **FR-022**: System MUST update any GitHub-specific configurations (issues templates, workflows, etc.)

### Key Entities

- **Project Identity**: The name and branding of the project (weavr), including its metaphor (weaving connections between codebases) and differentiation from the original fork
- **Module References**: All Python imports, package names, and directory structures that identify the code
- **Service Configurations**: External service references in wrapper projects and ecosystem tools
- **Documentation**: All markdown files, comments, and explanatory text that describe the project

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All test suites pass with 100% success rate after rename completion
- **SC-002**: Zero import errors when running `weavr` CLI commands
- **SC-003**: All documentation files (README, ARCHITECTURE, VISION, CLAUDE.md) reference "weavr" with zero mentions of "code-graph-rag"
- **SC-004**: External service wrappers (http and mcp) successfully reference and use the renamed project
- **SC-005**: Search across entire ai_agency repository returns zero references to "code-graph-rag" in code or configuration (git history excluded)
- **SC-006**: Package installs successfully with name "weavr" via pip/uv
- **SC-007**: Docker services start successfully with updated naming
- **SC-008**: Project registry contains accurate entry for "weavr" with correct path and metadata

## Assumptions

- The user will manually rename the GitHub repository from code-graph-rag to weavr
- Git history will retain references to the old name (this is acceptable and expected)
- External users who have forked the original repository are not in scope for this rename
- The original code-graph-rag project will remain available as a separate reference repository
- Attribution to the original project will be maintained in documentation

## Scope Boundaries

**In Scope:**
- All code within this repository
- All documentation within this repository
- References in direct integration points (http-service-wrappers, mcp-service-wrappers)
- References across ai_agency repository
- Project registry updates

**Out of Scope:**
- GitHub repository rename (manual user task)
- Git commit history rewriting
- Updates to external forks or clones
- Communication to external users about the rename
- Migration scripts for existing user installations
- Updates to the original code-graph-rag project

## Dependencies

- User must complete GitHub repository rename before updating git remote URLs
- Test suite must be functional before validation
- Project registry manager script must be available at ~/code/ai_agency/shared/scripts/registry/registry-manager.py

## Risks

- **Risk**: Tests may fail due to hardcoded references to old name
  - **Mitigation**: Comprehensive search and replace with verification

- **Risk**: External services may break if not all references are found
  - **Mitigation**: Systematic search across all known integration points

- **Risk**: Docker images may need rebuilding with new naming
  - **Mitigation**: Clear documentation of rebuild requirements

- **Risk**: Cached imports or dependencies may cause confusion
  - **Mitigation**: Clear cache instructions in implementation plan
