# Tasks: Project Folder Structure Reorganization

**Feature**: Project Folder Structure Reorganization
**Branch**: `005-structure-reorganization`
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Input**: User stories with priorities from spec.md, technical requirements from plan.md

## Implementation Strategy

**MVP Scope**: Start with User Story 1 (textbook content access) as the minimum viable product, ensuring that all 17 chapters remain accessible after reorganization. This provides immediate value while preserving existing functionality.

**Delivery Approach**: 
1. Complete foundational tasks first (directory creation, file movement)
2. Implement User Story 1 (content preservation)
3. Add User Story 2 (backend structure)
4. Complete User Story 3 (development environment)
5. Polish & verification across all components

## Dependencies

**User Story 2** depends on foundational setup and directory structure being complete, but can be developed in parallel with User Story 1 after Phase 2.

**User Story 3** depends on both User Stories 1 and 2 being completed to ensure the development environment functions after reorganization.

## Parallel Execution Examples

- T001-T004 (directory creation) can be done in parallel with initial file copying tasks
- Backend API structure (T015-T019) can be created in parallel with frontend configuration updates
- RAG scripts (T020-T022) can be created in parallel with backend structure

---

## Phase 1: Setup

**Goal**: Initialize the project structure needed for reorganization

- [x] T001 Create website/ directory structure with docs/, src/, static/ subdirectories
- [x] T002 Create module subdirectories under website/docs/ (module1-ros2, module2-gazebo-unity, module3-isaac, module4-vla)
- [x] T003 Create src subdirectories under website/src/ (components, css, pages)
- [x] T004 Create static subdirectories under website/static/ (diagrams, ros2-examples, simulation-examples, isaac-examples)
- [x] T005 Create backend/ directory structure with api/, db/, rag/ subdirectories
- [x] T006 Create rag/ directory for standalone RAG scripts

---

## Phase 2: Foundational Tasks

**Goal**: Move existing files and update configuration paths to support new structure

- [x] T007 [P] Move existing docs/ content to website/docs/ directory preserving all content
- [x] T008 [P] Move existing src/ content to website/src/ directory preserving all components
- [x] T009 [P] Move existing static/ content to website/static/ directory preserving all assets
- [x] T010 [P] Move docusaurus.config.js to website/ directory and update internal paths
- [x] T011 [P] Move sidebars.js to website/ directory and update doc references
- [x] T012 [P] Move package.json to website/ directory and verify scripts work in new location
- [x] T013 [P] Move babel.config.js to website/ directory if it exists
- [x] T014 [P] Move website/README.md to website/ directory

---

## Phase 3: User Story 1 - Access Textbook Content (Priority: P1)

**Goal**: Ensure all 17 chapters remain accessible and functional after reorganization

**Independent Test**: Can verify that all 17 chapters load correctly in the restructured website directory and that all content, diagrams, and code examples remain accessible without errors.

- [x] T023 [US1] Update all internal path references in moved documentation files to reflect new directory structure
- [x] T024 [US1] Verify all module directories contain correct chapter files from original docs/
- [x] T025 [US1] Test that all chapter navigation works correctly in the new structure
- [x] T026 [US1] Verify all diagrams and images in static/ directory are accessible from documentation
- [x] T027 [US1] Check all code examples in markdown files reference correct paths
- [x] T028 [US1] Update sidebar navigation to reflect new directory structure
- [ ] T029 [US1] Verify all deep links to textbook content work correctly after reorganization
- [ ] T030 [US1] Confirm all 17 textbook chapters load without errors

---

## Phase 4: User Story 2 - Develop Backend Services (Priority: P2)

**Goal**: Provide a clean separation between frontend and backend with FastAPI structure ready for development

**Independent Test**: Can verify that the backend/ directory contains an empty FastAPI structure ready for development, with no interference to the website/ directory functionality.

- [x] T031 [P] [US2] Create backend/main.py with basic FastAPI application structure
- [x] T032 [P] [US2] Create backend/api/__init__.py as placeholder for API routes
- [x] T033 [P] [US2] Create backend/db/__init__.py as placeholder for database models
- [x] T034 [P] [US2] Create backend/rag/__init__.py as placeholder for RAG logic
- [x] T035 [P] [US2] Create backend/requirements.txt with basic FastAPI dependencies
- [x] T036 [P] [US2] Create backend/README.md with setup instructions
- [x] T037 [US2] Verify website/ directory functionality is not affected by backend structure
- [x] T038 [US2] Implement basic health check endpoint per API contract

---

## Phase 5: User Story 3 - Maintain Development Environment (Priority: P3)

**Goal**: Ensure Docusaurus development environment functions normally after reorganization

**Independent Test**: Can verify starting the Docusaurus development server in the new website/ directory and ensuring all development features work correctly.

- [x] T039 [US3] Update website/package.json scripts to work properly in new directory structure
- [x] T040 [US3] Test npm start command in website directory and verify dev server functions
- [x] T041 [US3] Verify hot-reload functionality works after making changes to documentation
- [x] T042 [US3] Test all Docusaurus build and deployment commands in new structure
- [x] T043 [US3] Confirm Docusaurus configuration properly references new static asset paths
- [x] T044 [US3] Verify all development tools and plugins work in new structure

---

## Phase 6: RAG Implementation Structure

**Goal**: Set up standalone RAG scripts directory for future implementation

- [x] T045 [P] Create rag/ingest.py with placeholder document ingestion functionality
- [x] T046 [P] Create rag/query.py with placeholder query testing functionality
- [x] T047 [P] Create rag/requirements.txt with basic Python dependencies for RAG
- [x] T048 [P] Create rag/README.md with RAG implementation instructions

---

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Update project metadata and verify complete functionality

- [x] T049 Update root README.md to document the new project structure
- [x] T050 Update .gitignore to include new directory structure patterns
- [x] T051 Run npm start in website directory and verify full textbook functionality
- [x] T052 Verify all 17 chapters are accessible and all content preserved
- [x] T053 Test that backend directory structure is properly separated with no dependencies
- [x] T054 Verify all static assets, diagrams, and code examples are accessible
- [x] T055 Document any changes to contribution workflow in README or documentation
- [x] T056 Update any documentation links or references to account for directory changes
- [x] T057 Final verification that all success criteria from spec are met