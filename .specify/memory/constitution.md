<!-- 
SYNC IMPACT REPORT:
Version change: N/A → 1.0.0
Modified principles: N/A (new constitution)
Added sections: All sections (new document)
Removed sections: N/A
Templates requiring updates: ⚠ pending (.specify/templates/plan-template.md, .specify/templates/spec-template.md, .specify/templates/tasks-template.md)
Follow-up TODOs: None
-->
# Physical AI & Humanoid Robotics Textbook Constitution

## Core Principles

### I. Education-First Approach
Every feature and design decision must prioritize educational value and learning outcomes. Content must be accessible to students with Python + basic AI/ML background, maintain reading level appropriate for Grade 12-14 (undergraduate), and include clear examples with comprehensive documentation. This ensures the textbook serves its primary purpose as an educational tool.

### II. Interactive Intelligence
Intelligence features (RAG chatbot, personalization, auto-generated content) must enhance the learning experience without overshadowing the core educational content. All AI features should be seamlessly integrated to provide immediate value to learners while maintaining accuracy and relevance to the subject matter.

### III. Quality and Accuracy (NON-NEGOTIABLE)
Content must meet strict academic standards: 50% peer-reviewed sources (IEEE, ACM, ROS 2 docs, NVIDIA papers), all hardware specs citing manufacturer docs, and code examples tested on ROS 2 Humble. Plagiarism is completely unacceptable, ensuring all materials are original and properly attributed.

### IV. Accessibility and Inclusivity
The textbook must be accessible across different devices and languages, supporting mobile users and providing Urdu translation capabilities. Content should be structured to accommodate different learning backgrounds and needs while maintaining a consistent, high-quality learning experience for all users.

### V. Modularity and Maintainability
Content should be organized in well-structured, modular chapters (6-8 chapters covering all 4 modules) that can be updated independently. Each chapter should contain runnable code examples, diagrams, and citations following APA 7th edition format. This allows for continuous improvements without disrupting the entire curriculum.

### VI. Performance and Scalability
All components (frontend, backend, databases) must operate efficiently on free tiers (Qdrant free tier, Neon free tier) and support low-end devices (students on phones). Bundle sizes must remain small, and response times for interactive features should be under 3 seconds to ensure a smooth learning experience.

## Technical Standards

### Frontend Development
All frontend components must follow Docusaurus 3.x best practices, include responsive design for mobile devices, implement search functionality, and provide syntax highlighting for Python, ROS 2, and URDF. The user interface must be clean, fast, and intuitive for learners to navigate without confusion.

### Backend Architecture
Backend services (FastAPI, OpenAI Agents SDK, Qdrant Cloud, Neon Postgres) must maintain secure, scalable operations with proper error handling, structured logging, and reliable API response times. The RAG chatbot must provide accurate answers with proper citations to book content only.

### Code Quality
All code must pass linting standards (pylint ≥ 8.0), include comprehensive error handling, implement proper authentication with Better-Auth, and follow established patterns for testability and maintainability. All code examples must be tested and verified before inclusion in chapters.

## Development Workflow

### Content Creation Process
Each chapter follows a structured creation process: research (using peer-reviewed sources), drafting (with attention to reading level), diagram creation (using Mermaid, Draw.io XML, or SVG), code example development and testing, citation formatting (APA 7th), and peer review. This ensures consistent quality across all educational materials.

### Testing and Quality Assurance
Before each commit, code must pass linting, markdown must pass spell-check, and all links must be tested for validity. Before deployment, the application must achieve a Lighthouse score > 90, all API endpoints must return 200 status, database connections must be verified, and HTTPS must be enabled.

### Continuous Integration
All changes follow a CI/CD process via GitHub Actions with automated quality checks, deployment verification, and rollback capabilities. Changes must not degrade performance, security, or user experience without explicit justification and approval.

## Governance

This constitution governs all decisions for the Physical AI & Humanoid Robotics Textbook project. All amendments require documentation in commit messages with clear justification and migration plans if needed. All pull requests and reviews must verify compliance with these principles and standards.

All team members must ensure their contributions align with these core principles and maintain the educational integrity of the project. Any deviation from these principles must be explicitly documented and approved by project leadership.

**Version**: 1.0.0 | **Ratified**: 2025-12-12 | **Last Amended**: 2025-12-12