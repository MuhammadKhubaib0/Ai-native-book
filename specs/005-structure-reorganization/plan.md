# Implementation Plan: Project Folder Structure Reorganization

**Branch**: `005-structure-reorganization` | **Date**: Monday, December 15, 2025 | **Spec**: [link](./spec.md)
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Reorganize the existing Docusaurus textbook from a monolithic structure to a professional full-stack architecture with separate frontend (website/), backend (backend/), and RAG (rag/) directories. The implementation will preserve all existing content (4 modules, 17 chapters) while establishing clean separation for future development without breaking Docusaurus functionality.

## Technical Context

**Language/Version**: JavaScript/Node.js (Docusaurus), Python 3.8+ (FastAPI)
**Primary Dependencies**: Docusaurus 2.x, FastAPI 0.100+, npm
**Storage**: N/A (Content stored in docs/ as markdown files)
**Testing**: Manual verification of content accessibility and functionality
**Target Platform**: Web (Docusaurus static site with FastAPI backend)
**Project Type**: Web application (when "frontend" + "backend" detected)
**Performance Goals**: Maintain current Docusaurus performance levels
**Constraints**: <2 minutes for npm start, preserve all existing content without modification, maintain all functionality
**Scale/Scope**: 17 textbook chapters, 4 modules, 10k+ lines of content

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No violations detected in the feature specification that would conflict with project constitution.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
# Web application structure
website/
├── docs/                # All textbook content (moved from root)
│   ├── module1-ros2/
│   ├── module2-gazebo-unity/
│   ├── module3-isaac/
│   └── module4-vla/
├── src/                 # React components (moved from root)
│   ├── components/
│   ├── css/
│   └── pages/
├── static/              # Static assets (moved from root)
│   ├── diagrams/
│   ├── ros2-examples/
│   ├── simulation-examples/
│   └── isaac-examples/
├── docusaurus.config.js # Main config (moved from root)
├── sidebars.js          # Sidebar config (moved from root)
├── package.json         # Dependencies (moved from root)
├── babel.config.js      # If exists (moved from root)
└── README.md            # Frontend docs (moved from root)

backend/                 # FastAPI backend (new, empty structure)
├── api/                 # API routes (placeholder)
│   └── __init__.py
├── db/                  # Database models (placeholder)
│   └── __init__.py
├── rag/                 # RAG logic (placeholder)
│   └── __init__.py
├── main.py              # FastAPI entry point (placeholder)
├── requirements.txt     # Python dependencies (placeholder)
└── README.md            # Backend docs (placeholder)

rag/                     # Standalone RAG scripts (new, empty)
├── ingest.py            # Document ingestion (placeholder)
├── query.py             # Query testing (placeholder)
└── README.md            # RAG docs (placeholder)

.gitignore               # Updated ignore patterns
README.md                # Root project README (updated)
```

**Structure Decision**: Selected web application structure with clear separation of frontend (Docusaurus) and backend (FastAPI) components. The website/ directory will contain all Docusaurus code and content, while backend/ will hold the FastAPI skeleton for future RAG implementation. An additional rag/ directory is created for standalone RAG scripts.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [N/A] | [No violations found] | [N/A] |