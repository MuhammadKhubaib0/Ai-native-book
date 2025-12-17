# Research: Project Folder Structure Reorganization

## Decision: Directory Structure for Full-Stack Separation

**Rationale**: To maintain clear separation of concerns between frontend and backend components while preserving all existing textbook content and functionality. Moving toward a professional full-stack architecture enables future development of backend services (particularly RAG implementation) without interfering with the existing Docusaurus textbook.

**Alternatives considered**:
1. Keep all code in a monolithic structure - rejected because it doesn't allow for clean backend development
2. Create subdirectories within existing structure - rejected because it could complicate navigation and build processes
3. Separate into completely different repositories - rejected because the textbook and RAG functionality are closely related features

## Decision: Docusaurus Configuration File Migration

**Rationale**: Docusaurus configuration files (docusaurus.config.js, sidebars.js, etc.) must be moved to the new website/ directory to maintain proper functionality. This ensures the Docusaurus build process works correctly within the new directory structure.

**Alternatives considered**:
1. Keep configuration files in root and reference website/ - rejected because it would complicate the build process
2. Rewrite configuration from scratch - rejected because existing configuration contains important settings for navigation, plugins, and styling

## Decision: Package.json and Dependencies Handling

**Rationale**: The existing package.json and associated dependencies should move to the website/ directory where they're relevant for the Docusaurus frontend. A new package.json is not needed for the backend since FastAPI doesn't require npm dependencies.

**Alternatives considered**:
1. Keep package.json in root - rejected because it would make the project structure confusing
2. Create separate package.json for backend - rejected because backend is Python-based and doesn't use npm

## Decision: Path Reference Updates

**Rationale**: All internal path references in configuration files, code examples, and documentation must be updated to reflect the new directory structure. This ensures no broken links or missing resources after the reorganization.

**Alternatives considered**:
1. Use symbolic links - rejected because it adds complexity and may not work across all platforms
2. Keep old paths and use build-time substitutions - rejected because it's more complex and error-prone than direct updates

## Decision: Frontend vs Backend Technology Stack

**Rationale**: Maintain Docusaurus (React-based) for the frontend textbook content and use FastAPI for the backend due to its excellent integration with Python ML/AI libraries needed for RAG implementation.

**Alternatives considered**:
1. Rewrite frontend in another framework - rejected because Docusaurus is already well-suited for documentation sites
2. Use different backend framework (e.g., Express.js) - rejected because Python/ FastAPI is more appropriate for RAG/ML workflows