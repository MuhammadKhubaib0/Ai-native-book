# API Contract: Simulation Content Service

**Feature**: 2-gazebo-unity-digital-twin
**Date**: 2025-12-12

## Overview

This document describes the API contract for the simulation content service that will serve educational content, including chapters, simulation examples, and related resources for the Gazebo Unity Digital Twin textbook module.

## Endpoints

### GET /api/simulation-content/modules

Retrieve a list of all simulation content modules.

**Request**:
- Method: GET
- Path: /api/simulation-content/modules
- Headers: None required
- Parameters: None

**Response**:
- Status: 200 OK
- Content-Type: application/json
- Body:
```json
{
  "modules": [
    {
      "id": "module2-gazebo-unity",
      "title": "The Digital Twin (Gazebo & Unity)",
      "description": "Physics simulation in Gazebo, sensor simulation, Unity integration for high-fidelity rendering, sim-to-real principles",
      "chaptersCount": 4,
      "estimatedReadingTime": 240,
      "prerequisites": ["ROS 2 basics", "Nodes, Topics, Services", "URDF understanding"]
    }
  ]
}
```

### GET /api/simulation-content/modules/{moduleId}

Retrieve details of a specific simulation content module.

**Request**:
- Method: GET
- Path: /api/simulation-content/modules/{moduleId}
- Headers: None required
- Parameters: 
  - moduleId: string (path parameter, e.g., "module2-gazebo-unity")

**Response**:
- Status: 200 OK
- Content-Type: application/json
- Body:
```json
{
  "id": "module2-gazebo-unity",
  "title": "The Digital Twin (Gazebo & Unity)",
  "description": "Physics simulation in Gazebo, sensor simulation, Unity integration for high-fidelity rendering, sim-to-real principles",
  "chaptersCount": 4,
  "estimatedReadingTime": 240,
  "prerequisites": ["ROS 2 basics", "Nodes, Topics, Services", "URDF understanding"],
  "learningOutcomes": [
    "Explain physics simulation concepts in Gazebo",
    "Implement sensor simulations with realistic noise models",
    "Build Unity scenes with high-fidelity rendering",
    "Apply sim-to-real transfer techniques"
  ],
  "chapters": [
    {
      "id": "module2-chapter1",
      "title": "Physics Simulation in Gazebo",
      "sequence": 1,
      "estimatedReadingTime": 60
    },
    {
      "id": "module2-chapter2", 
      "title": "Sensor Simulation and Integration",
      "sequence": 2,
      "estimatedReadingTime": 60
    },
    {
      "id": "module2-chapter3",
      "title": "Unity for High-Fidelity Rendering",
      "sequence": 3,
      "estimatedReadingTime": 60
    },
    {
      "id": "module2-chapter4",
      "title": "Sim-to-Real Transfer Techniques",
      "sequence": 4,
      "estimatedReadingTime": 60
    }
  ],
  "simulationEnvironments": [
    {
      "id": "env1",
      "name": "Basic Physics World",
      "type": "gazebo",
      "description": "Simple world with basic physics simulation"
    },
    {
      "id": "env2",
      "name": "Sensor Test Environment",
      "type": "gazebo",
      "description": "Environment with various sensors for testing"
    },
    {
      "id": "env3",
      "name": "Humanoid Interaction Scene",
      "type": "unity",
      "description": "High-fidelity Unity scene for human-robot interaction"
    }
  ]
}
```

### GET /api/simulation-content/chapters/{chapterId}

Retrieve the content of a specific simulation chapter.

**Request**:
- Method: GET
- Path: /api/simulation-content/chapters/{chapterId}
- Headers: None required
- Parameters:
  - chapterId: string (path parameter, e.g., "module2-chapter1")

**Response**:
- Status: 200 OK
- Content-Type: application/json
- Body:
```json
{
  "id": "module2-chapter1",
  "title": "Physics Simulation in Gazebo",
  "moduleId": "module2-gazebo-unity",
  "sequence": 1,
  "wordCount": 2000,
  "estimatedReadingTime": 60,
  "objectives": [
    "Understand rigid body dynamics in Gazebo",
    "Implement contact models and friction parameters",
    "Create custom Gazebo worlds"
  ],
  "prerequisites": ["ROS 2 basics", "URDF understanding"],
  "content": "# Physics Simulation in Gazebo\n\n## Rigid Body Dynamics\n\nGazebo simulates rigid body dynamics using physics engines like ODE, Bullet, or DART...",
  "codeExamples": [
    {
      "id": "ex1",
      "title": "Empty World SDF",
      "description": "Basic Gazebo world with physics properties",
      "language": "sdf",
      "fileName": "empty_world.sdf"
    }
  ],
  "exercises": [
    {
      "id": "ex1",
      "title": "Physics Parameters",
      "type": "simulation",
      "difficulty": "intermediate"
    }
  ],
  "citations": [
    {
      "id": "cite1",
      "title": "Gazebo Physics",
      "authors": ["Koenig, N.", "Howard, A."],
      "publicationYear": 2004
    }
  ],
  "simulationEnvironments": [
    {
      "id": "env1",
      "name": "Basic Physics World",
      "type": "gazebo",
      "description": "Simple world with basic physics simulation"
    }
  ]
}
```

### GET /api/simulation-content/simulation-environments/{environmentId}

Retrieve the content of a specific simulation environment.

**Request**:
- Method: GET
- Path: /api/simulation-content/simulation-environments/{environmentId}
- Headers: None required
- Parameters:
  - environmentId: string (path parameter)

**Response**:
- Status: 200 OK
- Content-Type: application/json
- Body:
```json
{
  "id": "env1",
  "chapterId": "module2-chapter1",
  "name": "Basic Physics World",
  "type": "gazebo",
  "description": "Simple world with basic physics simulation",
  "components": ["ground_plane", "cube", "sphere"],
  "physicsEngine": "ode",
  "parameters": {
    "gravity": [0, 0, -9.8],
    "friction": 0.5
  },
  "sensors": [
    {
      "id": "sensor1",
      "name": "camera1",
      "type": "camera",
      "topic": "/camera/image_raw"
    }
  ],
  "robots": [],
  "environmentAssets": ["models/ground_plane", "models/cube", "models/sphere"],
  "files": [
    {
      "fileName": "physics_world.sdf",
      "downloadUrl": "/api/simulation-content/simulation-environments/env1/files/physics_world.sdf",
      "size": 2500
    }
  ]
}
```

## Error Responses

For all endpoints, the following error responses may occur:

### 404 Not Found
- **Cause**: Requested resource does not exist
- **Response Body**:
```json
{
  "error": "Resource not found",
  "details": "The requested resource could not be found"
}
```

### 400 Bad Request
- **Cause**: Invalid request parameters
- **Response Body**:
```json
{
  "error": "Invalid request",
  "details": "The request contains invalid parameters"
}
```

### 500 Internal Server Error
- **Cause**: Server-side error
- **Response Body**:
```json
{
  "error": "Internal server error",
  "details": "An unexpected error occurred on the server"
}
```

## Validation Rules

All API requests and responses must adhere to the following validation rules:

1. All identifiers use lowercase with hyphens as separators
2. All timestamps use ISO 8601 format
3. All text fields are properly encoded (UTF-8)
4. Response bodies follow the defined schema
5. Numeric values are within acceptable ranges
6. Physics parameter values are physically realistic (e.g., gravity magnitude around 9.8 m/s²)
7. Simulation environment file paths are valid and accessible