# Data Model: Project Folder Structure Reorganization

## Entities

### Textbook Content
- **Description**: The educational material consisting of 4 modules and 17 chapters
- **Location**: website/docs/ directory
- **Format**: Markdown files with frontmatter metadata
- **Fields**: 
  - title: string
  - description: string
  - module: string (module1-ros2, module2-gazebo-unity, module3-isaac, module4-vla)
  - chapter_number: integer
  - content: string (markdown)
  - assets: array of file references (images, code examples)
- **Validation**: Must contain required fields and follow Docusaurus schema
- **Relationships**: Organized hierarchically by module and chapter

### Docusaurus Configuration
- **Description**: Configuration for the Docusaurus static site generator
- **Location**: website/docusaurus.config.js
- **Type**: JavaScript configuration object
- **Fields**:
  - title: string (site title)
  - tagline: string (site tagline)
  - url: string (site URL)
  - baseUrl: string (base path)
  - organizationName: string (GitHub org)
  - projectName: string (GitHub repo)
  - onBrokenLinks: string (behavior setting)
  - onBrokenMarkdownLinks: string (behavior setting)
  - presets: array (Docusaurus presets)
  - themeConfig: object (theme configuration)
- **Validation**: Must conform to Docusaurus configuration schema
- **Relationships**: References to docs/ and static/ directories

### Sidebar Configuration
- **Description**: Navigation structure for the textbook content
- **Location**: website/sidebars.js
- **Type**: JavaScript object defining navigation
- **Fields**:
  - module1-ros2: array of chapter references
  - module2-gazebo-unity: array of chapter references
  - module3-isaac: array of chapter references
  - module4-vla: array of chapter references
- **Validation**: Each reference must point to an existing doc file
- **Relationships**: Connects to Textbook Content entities

### Static Assets
- **Description**: Images, diagrams, code examples, and other static resources
- **Location**: website/static/ directory
- **Type**: File system resources
- **Fields**:
  - path: string (relative path from static/ directory)
  - type: string (image, code example, etc.)
  - references: array of entities that reference this asset
- **Validation**: Must have valid file extensions and meet size constraints
- **Relationships**: Referenced by Textbook Content entities

### Backend Structure
- **Description**: Placeholder structure for FastAPI backend
- **Location**: backend/ directory
- **Type**: Python module structure
- **Fields**:
  - api: directory containing API routes
  - db: directory containing database models
  - rag: directory containing RAG logic
  - main.py: FastAPI application entry point
  - requirements.txt: Python dependencies
- **Validation**: Must follow Python package conventions
- **Relationships**: Independent from frontend components

### RAG Scripts
- **Description**: Standalone scripts for RAG implementation
- **Location**: rag/ directory
- **Type**: Python scripts
- **Fields**:
  - ingest.py: Document ingestion script
  - query.py: Query testing script
  - requirements.txt: Python dependencies
- **Validation**: Must follow Python conventions
- **Relationships**: Related to Textbook Content entities for indexing