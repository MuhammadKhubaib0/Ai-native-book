# Data Model: Isaac AI Robot Brain Module (NVIDIA Isaac)

## Overview
This document defines the key data entities and models for Module 3: The AI-Robot Brain (NVIDIA Isaac). This module focuses on Isaac Sim for photorealistic simulation, Isaac ROS for perception, and Nav2 for humanoid navigation.

## Entity Models

### 1. Simulation Environment
**Description**: Represents the digital world where robots operate, containing physics properties, lighting conditions, and objects that interact with robots.

**Attributes**:
- environment_id (string): Unique identifier for the simulation environment
- name (string): Human-readable name of the environment
- description (string): Brief description of the environment
- physics_properties (object): Contains gravity, friction, and other physics parameters
- lighting_conditions (object): Contains ambient lighting, directional lights, and shadows configuration
- objects (array): List of objects in the environment with their properties
- robot_assets (array): List of robot models included in the environment
- usd_path (string): Path to the USD file representing the environment
- created_timestamp (datetime): When the environment was created
- modified_timestamp (datetime): When the environment was last modified

**Relationships**:
- Contains many Robot Models
- Contains many Objects
- Associated with many Simulation Sessions

### 2. Robot Model
**Description**: Digital representation of physical robots with kinematic properties, sensors, and actuators for simulation.

**Attributes**:
- robot_id (string): Unique identifier for the robot model
- model_name (string): Name of the robot model (e.g., "TurtleBot3", "Atlas", "A1")
- description (string): Brief description of the robot
- urdf_path (string): Path to the URDF file defining the robot
- sdf_path (string): Path to the SDF file defining the robot (if applicable)
- kinematic_properties (object): Contains joint limits, degrees of freedom, etc.
- sensor_configurations (array): List of sensors attached to the robot
- actuator_configurations (array): List of actuators attached to the robot
- kinematic_chain (object): Defines the robot's kinematic structure
- mass_properties (object): Contains mass, center of mass, moments of inertia
- material_properties (object): Defines visual properties and materials
- created_timestamp (datetime): When the model was created
- modified_timestamp (datetime): When the model was last modified

**Relationships**:
- Belongs to one Simulation Environment
- Associated with many Perception Pipelines
- Associated with many Navigation Configurations
- Used in many Simulation Sessions

### 3. Perception Pipeline
**Description**: Collection of algorithms that process sensor data to understand the environment, including VSLAM, object detection, and depth estimation.

**Attributes**:
- pipeline_id (string): Unique identifier for the perception pipeline
- name (string): Name of the perception pipeline
- description (string): Brief description of the pipeline
- pipeline_type (enum): Type of pipeline (VSLAM, Object Detection, Depth Estimation, Semantic Segmentation)
- algorithm_config (object): Configuration parameters for the algorithm
- input_topics (array): List of ROS topics the pipeline subscribes to
- output_topics (array): List of ROS topics the pipeline publishes to
- computational_requirements (object): GPU/CPU requirements for the pipeline
- accuracy_metrics (object): Contains accuracy measurements for the pipeline
- performance_metrics (object): Contains latency, throughput measurements
- calibration_data (object): Camera intrinsic/extrinsic calibration for vision-based pipelines
- created_timestamp (datetime): When the pipeline was created
- modified_timestamp (datetime): When the pipeline was last modified

**Relationships**:
- Associated with one Robot Model
- Associated with many Synthetic Datasets
- Used in many Simulation Sessions

### 4. Navigation Configuration
**Description**: Framework configuration that enables autonomous movement, including path planning, obstacle avoidance, and recovery behaviors.

**Attributes**:
- config_id (string): Unique identifier for the navigation configuration
- name (string): Name of the navigation configuration
- description (string): Brief description of the configuration
- robot_type (enum): Type of robot (wheeled, bipedal, quadraped)
- planner_type (enum): Path planning algorithm (Dijkstra, A*, RRT, etc.)
- costmap_config (object): Configuration for the local and global costmaps
- recovery_behaviors (array): List of recovery behaviors for navigation
- controller_config (object): Configuration for motion controllers
- footprint_config (object): Robot footprint definition for collision checking
- dynamic_obstacle_handling (object): Configuration for handling moving obstacles
- humanoid_specific_params (object): Parameters specific to bipedal locomotion
- created_timestamp (datetime): When the configuration was created
- modified_timestamp (datetime): When the configuration was last modified

**Relationships**:
- Associated with one Robot Model
- Used in many Simulation Sessions
- Associated with many Navigation Sessions

### 5. Synthetic Dataset
**Description**: Artificially generated collections of images and sensor data with ground truth annotations for training machine learning models.

**Attributes**:
- dataset_id (string): Unique identifier for the dataset
- name (string): Name of the dataset
- description (string): Brief description of the dataset
- dataset_type (enum): Type of data (image, pointcloud, lidar, etc.)
- size (integer): Number of samples in the dataset
- annotation_type (enum): Type of annotations (bounding boxes, segmentation masks, depth maps, etc.)
- domain_randomization_params (object): Parameters used for domain randomization
- generation_config (object): Configuration used during generation
- generation_timestamp (datetime): When the dataset was generated
- sensor_config (object): Configuration of the sensor used to generate the data
- synthetic_environment (object): Reference to the environment used for generation
- created_timestamp (datetime): When the dataset record was created
- modified_timestamp (datetime): When the record was last modified

**Relationships**:
- Generated from many Simulation Environments
- Generated using many Perception Pipelines
- Associated with many Training Sessions

## State Transitions

### Simulation Environment States
- **CREATION**: Environment is being designed and configured
- **VALIDATION**: Environment is being tested for physics and lighting correctness
- **READY**: Environment is ready for simulation sessions
- **IN_USE**: Environment is currently being used in a simulation
- **ARCHIVED**: Environment is no longer actively used but preserved for reference

### Perception Pipeline States
- **DESIGN**: Pipeline is being designed and configured
- **TRAINING**: Pipeline is being trained (if applicable)
- **VALIDATION**: Pipeline performance is being evaluated
- **ACTIVE**: Pipeline is operational and processing data
- **DEPRECATED**: Pipeline is no longer recommended for use

### Navigation Configuration States
- **DESIGN**: Configuration is being designed and tuned
- **SIMULATION_TEST**: Configuration is being tested in simulation
- **DEPLOYMENT_READY**: Configuration is ready for deployment
- **ACTIVE**: Configuration is being used for navigation
- **ARCHIVED**: Configuration is deprecated but preserved for reference

## Validation Rules

### Simulation Environment Validation
- Required fields: environment_id, name, usd_path
- Name must be unique within the system
- USD path must point to a valid file
- Physics properties must have valid values (e.g., gravity within reasonable range)

### Robot Model Validation
- Required fields: robot_id, model_name, urdf_path
- Model name must be unique
- URDF file must be valid and parseable
- Kinematic properties must be consistent with URDF definition

### Perception Pipeline Validation
- Required fields: pipeline_id, name, pipeline_type, input_topics, output_topics
- Pipeline type must be a valid enum value
- Input and output topics must follow ROS naming conventions
- Computational requirements must be compatible with target hardware

### Navigation Configuration Validation
- Required fields: config_id, name, robot_type, planner_type
- Robot type and planner type must be valid enum values
- Costmap configuration must have valid parameters
- Humanoid-specific parameters are required when robot_type is "bipedal"

### Synthetic Dataset Validation
- Required fields: dataset_id, name, dataset_type, size
- Size must be a positive integer
- Annotation type must be relevant to the dataset type
- Generation timestamp must not be in the future