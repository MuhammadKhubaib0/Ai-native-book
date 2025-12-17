# API Contract: Textbook Content Service

**Feature**: 1-ros2-textbook-chapters
**Date**: 2025-12-12

## Overview

This document describes the API contract for the textbook content service that will serve educational content, including chapters, code examples, and related resources for the ROS 2 textbook.

## Endpoints

### GET /api/textbook/modules

Retrieve a list of all textbook modules.

**Request**:
- Method: GET
- Path: /api/textbook/modules
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
      "id": "module1-ros2",
      "title": "The Robotic Nervous System (ROS 2)",
      "description": "Introduction to ROS 2 architecture, Nodes, Topics, Services, Python agents with rclpy, and URDF for humanoids",
      "chaptersCount": 4,
      "estimatedReadingTime": 180,
      "prerequisites": ["Python programming", "Basic AI/ML concepts"]
    }
  ]
}
```

### GET /api/textbook/modules/{moduleId}

Retrieve details of a specific textbook module.

**Request**:
- Method: GET
- Path: /api/textbook/modules/{moduleId}
- Headers: None required
- Parameters: 
  - moduleId: string (path parameter, e.g., "module1-ros2")

**Response**:
- Status: 200 OK
- Content-Type: application/json
- Body:
```json
{
  "id": "module1-ros2",
  "title": "The Robotic Nervous System (ROS 2)",
  "description": "Introduction to ROS 2 architecture, Nodes, Topics, Services, Python agents with rclpy, and URDF for humanoids",
  "chaptersCount": 4,
  "estimatedReadingTime": 180,
  "prerequisites": ["Python programming", "Basic AI/ML concepts"],
  "learningOutcomes": [
    "Explain ROS 2 architecture, Nodes, Topics, and Services",
    "Create Python agents that interface with ROS 2 using rclpy",
    "Create and interpret humanoid URDFs",
    "Build a simple robotic arm controller"
  ],
  "chapters": [
    {
      "id": "module1-chapter1",
      "title": "Introduction to ROS 2",
      "sequence": 1,
      "estimatedReadingTime": 45
    },
    {
      "id": "module1-chapter2", 
      "title": "Python Agents Bridging ROS 2",
      "sequence": 2,
      "estimatedReadingTime": 45
    },
    {
      "id": "module1-chapter3",
      "title": "Humanoid Robot Description with URDF",
      "sequence": 3,
      "estimatedReadingTime": 45
    },
    {
      "id": "module1-chapter4",
      "title": "Practical Lab: Building and Testing a Simulated Arm Controller",
      "sequence": 4,
      "estimatedReadingTime": 45
    }
  ]
}
```

### GET /api/textbook/chapters/{chapterId}

Retrieve the content of a specific textbook chapter.

**Request**:
- Method: GET
- Path: /api/textbook/chapters/{chapterId}
- Headers: None required
- Parameters:
  - chapterId: string (path parameter, e.g., "module1-chapter1")

**Response**:
- Status: 200 OK
- Content-Type: application/json
- Body:
```json
{
  "id": "module1-chapter1",
  "title": "Introduction to ROS 2",
  "moduleId": "module1-ros2",
  "sequence": 1,
  "wordCount": 2200,
  "estimatedReadingTime": 45,
  "objectives": [
    "Understand ROS 2 architecture",
    "Explain Nodes, Topics, and Services",
    "Identify use cases for ROS 2"
  ],
  "prerequisites": ["Python programming", "Basic understanding of robotics"],
  "content": "# Introduction to ROS 2\n\n## Architecture\n\nROS 2 (Robot Operating System 2) is a flexible framework for writing robot applications...",
  "codeExamples": [
    {
      "id": "ex1",
      "title": "Simple Publisher",
      "description": "A basic publisher node that sends messages",
      "language": "python",
      "fileName": "basic_publisher.py"
    }
  ],
  "exercises": [
    {
      "id": "ex1",
      "title": "Node Identification",
      "type": "conceptual",
      "difficulty": "beginner"
    }
  ],
  "citations": [
    {
      "id": "cite1",
      "title": "ROS 2 Design",
      "authors": ["Anonymous"],
      "publicationYear": 2022
    }
  ]
}
```

### GET /api/textbook/code-examples/{exampleId}

Retrieve the content of a specific code example.

**Request**:
- Method: GET
- Path: /api/textbook/code-examples/{exampleId}
- Headers: None required
- Parameters:
  - exampleId: string (path parameter)

**Response**:
- Status: 200 OK
- Content-Type: application/json
- Body:
```json
{
  "id": "ex1",
  "chapterId": "module1-chapter1",
  "title": "Simple Publisher",
  "description": "A basic publisher node that sends messages",
  "language": "python",
  "code": "#!/usr/bin/env python3\n\nimport rclpy\nfrom std_msgs.msg import String\n\nclass SimplePublisher:\n    def __init__(self):\n        # Initialize the node\n        self.node = rclpy.create_node('simple_publisher')\n        # Create a publisher\n        self.publisher = self.node.create_publisher(String, 'chatter', 10)\n        \n    def publish_message(self, msg):\n        self.publisher.publish(msg)\n\n# Example usage would go here\n",
  "fileName": "basic_publisher.py",
  "requiresSimulation": false,
  "dependencies": ["rclpy", "std_msgs"]
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