# Data Model: Gazebo Unity Digital Twin

**Feature**: 2-gazebo-unity-digital-twin
**Date**: 2025-12-12

## Entities

### Chapter
- **Fields**:
  - id: string (unique identifier, e.g. "module2-chapter1")
  - title: string (chapter title)
  - module: string (module identifier, e.g. "module2-gazebo-unity")
  - sequence: integer (chapter number within module)
  - wordCount: integer (total word count)
  - estimatedReadingTime: integer (in minutes)
  - objectives: array of strings (learning objectives)
  - prerequisites: array of strings (required knowledge from Module 1)
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
  - language: string (programming language, e.g. "python", "csharp", "sdf")
  - code: string (the actual code)
  - fileName: string (filename for downloadable version)
  - requiresSimulation: boolean (whether example needs Gazebo/Unity to run)
  - dependencies: array of strings (Gazebo/Unity packages or other dependencies)
  - testResults: string (expected output or behavior)

- **Validation Rules**:
  - language must be one of supported languages (python, csharp, sdf, urdf, etc.)
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
  - type: string (type of diagram: "svg", "mermaid", "png", "sdf-visualization", "unity-scene")
  - sourceFormat: string (source format: "mermaid", "drawio", "svg", "sdf", "unity")
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
  - type: string (type: "conceptual", "simulation", "coding", "analysis")
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

### SimulationEnvironment
- **Fields**:
  - id: string (unique identifier)
  - chapterId: string (reference to parent Chapter)
  - name: string (name of the simulation environment)
  - type: string (one of "gazebo", "unity", "gazebo-unity-integration")
  - description: string (what the environment simulates)
  - components: array of string (the components of the environment)
  - physicsEngine: string (physics engine used, e.g. "ode", "bullet", "dart")
  - parameters: object (physics parameters like gravity, friction, etc.)
  - sensors: array of Sensor objects
  - robots: array of Robot objects
  - environmentAssets: array of string (files or assets needed for the environment)

- **Validation Rules**:
  - type must be one of the allowed types
  - physicsEngine must be supported by the environment type
  - components must not be empty

- **Relationships**:
  - Many SimulationEnvironments to one Chapter
  - One SimulationEnvironment to many Sensors, Robots

### Sensor
- **Fields**:
  - id: string (unique identifier)
  - simulationEnvironmentId: string (reference to parent SimulationEnvironment)
  - name: string (name of the sensor, e.g. "lidar_1", "imu_1")
  - type: string (sensor type, e.g. "lidar", "depth_camera", "imu", "force_torque")
  - topic: string (ROS topic where sensor publishes data)
  - parameters: object (sensor-specific parameters like range, resolution, etc.)
  - noiseModel: object (description of the noise model for the sensor)
  - position: object (3D position in the environment)
  - orientation: object (3D orientation in the environment)

- **Validation Rules**:
  - type must be one of the supported sensor types
  - topic must follow ROS naming conventions
  - position and orientation must be valid 3D coordinates

- **Relationships**:
  - Many Sensors to one SimulationEnvironment

### Robot
- **Fields**:
  - id: string (unique identifier)
  - simulationEnvironmentId: string (reference to parent SimulationEnvironment)
  - name: string (name of the robot)
  - urdfPath: string (path to the URDF file describing the robot)
  - controllerConfig: object (configuration for robot controllers)
  - initialPosition: object (3D starting position in the environment)
  - initialOrientation: object (3D starting orientation in the environment)
  - state: string (operational state of the robot)

- **Validation Rules**:
  - urdfPath must point to a valid URDF file
  - initialPosition and initialOrientation must be valid 3D coordinates

- **Relationships**:
  - Many Robots to one SimulationEnvironment

### Module
- **Fields**:
  - id: string (unique identifier, e.g. "module2-gazebo-unity")
  - title: string (module title)
  - description: string (overview of module content)
  - totalChapters: integer (number of chapters in the module)
  - totalWordCount: integer (combined word count of all chapters)
  - prerequisites: array of strings (knowledge required from Module 1)
  - learningOutcomes: array of strings (what students will learn)
  - simulationEnvironments: array of SimulationEnvironment objects
  - chapters: array of Chapter objects

- **Validation Rules**:
  - totalChapters must match actual count of chapters
  - learningOutcomes must not be empty

- **Relationships**:
  - One Module to many Chapters, SimulationEnvironments