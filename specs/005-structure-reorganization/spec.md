# Feature Specification: Project Folder Structure Reorganization

**Feature Branch**: `005-structure-reorganization`
**Created**: Monday, December 15, 2025
**Status**: Draft
**Input**: User description: "Project Folder Structure Reorganization Target: Reorganize existing Docusaurus textbook into professional full-stack structure with separate frontend and backend folders Success criteria: - Create website/ folder containing all Docusaurus frontend code - Create backend/ folder with FastAPI structure for future RAG implementation - Move existing docs/, src/, static/ into website/ directory - Update all configuration files and import paths - Verify npm start works after reorganization without any errors - All 17 chapters remain accessible and functional - No content loss or modification - Clean separation ready for backend development Constraints: - Must preserve all existing content (4 modules, 17 chapters) - Must not break Docusaurus functionality - Update docusaurus.config.js paths if needed - Update package.json scripts if needed - Keep all code examples, diagrams, and assessments intact - Maintain Git history if using version control Not building: - Backend implementation (just folder structure) - RAG chatbot functionality (separate feature) - Database connections (separate feature) - API endpoints (separate feature) Final Structure: website/ # Docusaurus frontend ├── docs/ # All textbook content (moved from root) │ ├── module1-ros2/ │ ├── module2-gazebo-unity/ │ ├── module3-isaac/ │ └── module4-vla/ ├── src/ # React components (moved from root) │ ├── components/ │ ├── css/ │ └── pages/ ├── static/ # Static assets (moved from root) │ ├── diagrams/ │ ├── ros2-examples/ │ ├── simulation-examples/ │ └── isaac-examples/ ├── docusaurus.config.js # Main config (moved from root) ├── sidebars.js # Sidebar config (moved from root) ├── package.json # Dependencies (moved from root) ├── babel.config.js # If exists (moved from root) └── README.md # Frontend docs (moved from root) backend/ # FastAPI backend (new, empty structure) ├── api/ # API routes (placeholder) │ └── __init__.py ├── db/ # Database models (placeholder) │ └── __init__.py ├── rag/ # RAG logic (placeholder) │ └── __init__.py ├── main.py # FastAPI entry point (placeholder) ├── requirements.txt # Python dependencies (placeholder) └── README.md # Backend docs (placeholder) rag/ # Standalone RAG scripts (new, empty) ├── ingest.py # Document ingestion (placeholder) ├── query.py # Query testing (placeholder) └── README.md # RAG docs (placeholder) .gitignore # Updated ignore patterns README.md # Root project README (updated) Tasks: 1. Create new folder structure (website/, backend/, rag/) 2. Move existing files to website/ folder 3. Update all path references in configs 4. Create placeholder files in backend/ and rag/ 5. Test npm start in website/ directory 6. Update root README.md with new structure info 7. Verify all chapters load correctly"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Access Textbook Content (Priority: P1)

As a student or educator, I want to access the ROS2 textbook content without any disruption after the restructuring, so I can continue learning or teaching with all materials intact.

**Why this priority**: This is the most critical requirement as it ensures continuity of learning experience and preserves all existing content (4 modules, 17 chapters).

**Independent Test**: Can be fully tested by verifying that all 17 chapters load correctly in the restructured website directory and that all content, diagrams, and code examples remain accessible without errors.

**Acceptance Scenarios**:

1. **Given** The project structure has been reorganized, **When** I navigate to any textbook chapter via URL, **Then** the content loads correctly with no broken links or missing resources
2. **Given** The project structure has been reorganized, **When** I click on navigation elements in Docusaurus, **Then** all pages and sections remain accessible and functional

---

### User Story 2 - Develop Backend Services (Priority: P2)

As a developer, I want a clean separation between frontend and backend code, so I can implement new backend services without affecting the textbook content.

**Why this priority**: Enables future backend development for RAG implementation while maintaining clear separation of concerns.

**Independent Test**: Can be verified by checking that the backend/ directory contains an empty FastAPI structure ready for development, with no interference to the website/ directory functionality.

**Acceptance Scenarios**:

1. **Given** The project structure has been reorganized, **When** I access the backend/ directory, **Then** I find a properly structured FastAPI skeleton ready for development
2. **Given** The project structure has been reorganized, **When** I run npm start in the website/ directory, **Then** the frontend functions normally without backend dependencies

---

### User Story 3 - Maintain Development Environment (Priority: P3)

As a contributor to the textbook project, I want the development environment to function normally after reorganization, so I can continue contributing without disruption.

**Why this priority**: Ensures the development workflow remains unchanged for ongoing contributions to the textbook content.

**Independent Test**: Can be verified by starting the Docusaurus development server in the new website/ directory and ensuring all development features work correctly.

**Acceptance Scenarios**:

1. **Given** The project has been restructured, **When** I run npm start in the website directory, **Then** the development server starts without errors and hot-reload functions work
2. **Given** The project has been restructured, **When** I make changes to documentation, **Then** the development server reflects changes correctly

---

### Edge Cases

- What happens when a user accesses deep links to textbook content after the reorganization? All existing URLs should redirect appropriately or continue working.
- How does the system handle missing path references after moving files? All internal references must be updated to prevent broken links.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST maintain access to all 17 chapters and their content without loss after reorganization
- **FR-002**: System MUST allow compilation and serving of the Docusaurus textbook from the new website/ directory
- **FR-003**: System MUST update all internal path references to reflect the new directory structure
- **FR-004**: System MUST preserve all existing content including diagrams, code examples, and assessments
- **FR-005**: System MUST provide a structured backend/ directory with FastAPI skeleton for future development
- **FR-006**: System MUST include a rag/ directory with placeholder scripts for future implementation
- **FR-007**: System MUST update the root README.md to document the new structure
- **FR-008**: Users MUST be able to run npm start in the website directory and have the textbook function correctly

### Key Entities *(include if feature involves data)*

- **Textbook Content**: The educational material consisting of 4 modules and 17 chapters with associated diagrams, code examples, and assessments that must remain accessible after reorganization
- **Website Directory**: Contains all Docusaurus frontend code including docs/, src/, static/, and configuration files
- **Backend Directory**: Contains FastAPI structure for future RAG implementation with API routes, database models, and RAG logic placeholders
- **RAG Scripts**: Standalone scripts for document ingestion and query testing for future implementation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 17 textbook chapters remain accessible and functional after reorganization (100% of content preserved)
- **SC-002**: The Docusaurus development server starts successfully with npm start in the website/ directory without errors (100% success rate)
- **SC-003**: The new directory structure separates frontend and backend concerns cleanly with zero cross-dependencies (0 coupling between website and backend directories)
- **SC-004**: Content creators can continue to contribute to the textbook without any changes to their workflow (0 disruption to existing development process)