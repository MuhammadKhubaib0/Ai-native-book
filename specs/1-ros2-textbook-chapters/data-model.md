# Data Model: ROS 2 Textbook Chapters

**Feature**: 1-ros2-textbook-chapters
**Date**: 2025-12-12

## Entities

### Chapter
- **Fields**:
  - id: string (unique identifier, e.g. "module1-chapter1")
  - title: string (chapter title)
  - module: string (module identifier, e.g. "module1-ros2")
  - sequence: integer (chapter number within module)
  - wordCount: integer (total word count)
  - estimatedReadingTime: integer (in minutes)
  - objectives: array of strings (learning objectives)
  - prerequisites: array of strings (required knowledge)
  - content: string (the chapter content in MDX format)
  - codeExamples: array of CodeExample objects
  - diagrams: array of Diagram objects
  - exercises: array of Exercise objects
  - citations: array of Citation objects

- **Validation Rules**:
  - wordCount must be between 1500 and 2500
  - sequence must be positive integer
  - objectives must not be empty
  - content must be valid MDX format

- **Relationships**:
  - One Module to many Chapters
  - One Chapter to many CodeExamples, Diagrams, Exercises, Citations

### CodeExample
- **Fields**:
  - id: string (unique identifier)
  - chapterId: string (reference to parent Chapter)
  - title: string (example title)
  - description: string (what the example demonstrates)
  - language: string (programming language, e.g. "python")
  - code: string (the actual code)
  - fileName: string (filename for downloadable version)
  - requiresSimulation: boolean (whether example needs simulation to run)
  - dependencies: array of strings (ROS 2 packages or other dependencies)
  - testResults: string (expected output or behavior)

- **Validation Rules**:
  - language must be one of supported languages (python, urdf, etc.)
  - code must be syntactically valid for the specified language
  - fileName must have appropriate extension for the language

- **Relationships**:
  - Many CodeExamples to one Chapter

### Diagram
- **Fields**:
  - id: string (unique identifier)
  - chapterId: string (reference to parent Chapter)
  - title: string (diagram title)
  - description: string (what the diagram illustrates)
  - type: string (type of diagram: "svg", "mermaid", "png", "urdf-visualization")
  - sourceFormat: string (source format: "mermaid", "drawio", "svg", "urdf")
  - content: string (the diagram definition)
  - altText: string (accessibility description)

- **Validation Rules**:
  - type must be one of supported types
  - content must be valid for the sourceFormat
  - altText must not be empty

- **Relationships**:
  - Many Diagrams to one Chapter

### Exercise
- **Fields**:
  - id: string (unique identifier)
  - chapterId: string (reference to parent Chapter)
  - title: string (exercise title)
  - description: string (the exercise problem statement)
  - type: string (type: "conceptual", "coding", "simulation")
  - difficulty: string (one of "beginner", "intermediate", "advanced")
  - expectedOutcome: string (what the student should learn)
  - solution: string (solution approach, if appropriate)
  - hints: array of strings (helpful hints for the student)

- **Validation Rules**:
  - type must be one of valid exercise types
  - difficulty must be one of the allowed values
  - description must not be empty

- **Relationships**:
  - Many Exercises to one Chapter

### Citation
- **Fields**:
  - id: string (unique identifier)
  - chapterId: string (reference to parent Chapter)
  - type: string (one of "book", "journal", "conference", "online", "documentation", "video")
  - title: string (title of the cited work)
  - authors: array of strings (author names)
  - publicationYear: integer (year of publication)
  - url: string (URL if available)
  - doi: string (digital object identifier if applicable)
  - publisher: string (publisher name)
  - pages: string (page range if applicable)
  - accessedDate: string (date when source was accessed)

- **Validation Rules**:
  - type must be one of valid citation types
  - at least one of url or doi must be provided
  - publicationYear must be a reasonable year (2000-2026)

- **Relationships**:
  - Many Citations to one Chapter

### Module
- **Fields**:
  - id: string (unique identifier, e.g. "module1-ros2")
  - title: string (module title)
  - description: string (overview of module content)
  - totalChapters: integer (number of chapters in the module)
  - totalWordCount: integer (combined word count of all chapters)
  - prerequisites: array of strings (knowledge required before starting module)
  - learningOutcomes: array of strings (what students will learn)
  - chapters: array of Chapter objects

- **Validation Rules**:
  - totalChapters must match actual count of chapters
  - learningOutcomes must not be empty

- **Relationships**:
  - One Module to many Chapters