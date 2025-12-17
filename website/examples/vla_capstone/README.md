# Vision-Language-Action (VLA) Capstone for Humanoid Robots

This repository contains the implementation of the VLA Capstone module for the Physical AI & Humanoid Robotics textbook. This module demonstrates the integration of voice recognition, large language models, and robotic action execution in simulation environments.

## Overview

The VLA Capstone system implements a complete pipeline for creating autonomous humanoid robots that can understand voice commands and execute them in simulation. The system integrates:

- **Voice Recognition**: Using OpenAI Whisper for speech-to-text conversion
- **Large Language Models**: For cognitive planning and action generation
- **Vision Processing**: With Isaac Sim for photorealistic simulation and perception
- **Action Execution**: In Gazebo simulation environment
- **Multimodal Fusion**: Combining voice, vision, and other sensory inputs

## Features

- End-to-end voice-to-action pipeline
- Integration with Isaac Sim and Gazebo simulation environments
- RT-1, RT-2, OpenVLA architecture support
- Error recovery and confidence management
- Educational curriculum integration with student progress tracking
- Performance optimized for real-time operation

## Prerequisites

- Python 3.11+
- ROS 2 Humble Hawksbill
- NVIDIA Isaac Sim (optional for advanced perception)
- Gazebo Garden or later
- OpenAI API key
- Appropriate hardware (GPU recommended for LLM and vision processing)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/[ORG]/physical-intelligence-textbook.git
   cd physical-intelligence-textbook
   ```

2. Set up the Python environment:
   ```bash
   python -m venv vla-env
   source vla-env/bin/activate  # On Windows: vla-env\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure API keys:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. Build the ROS 2 workspace:
   ```bash
   cd ~/vla_ws
   colcon build
   source install/setup.bash
   ```

## Usage

### Running the Complete System

1. Start simulation environment (Isaac Sim or Gazebo)
2. Start the VLA system:
   ```bash
   cd website
   python -m uvicorn examples.vla_capstone.api.vla_api:app --host 0.0.0.0 --port 8000
   ```
3. Send voice commands via the API or use the ROS 2 interface

### Example Voice Commands

- "Go to the kitchen and find the red cup"
- "Navigate to the table and pick up the blue box"
- "Find the person and tell them to come here"

## Architecture

The system follows a modular architecture with clear separation of concerns:

- **API Layer**: REST endpoints for voice commands and system control
- **Service Layer**: Core functionality like LLM processing, vision integration, fusion
- **Model Layer**: Data models for voice commands, actions, and system state
- **Integration Layer**: Connectors to simulation environments and ROS 2
- **Validation Layer**: Checks for input validity and action safety
- **Evaluation Layer**: Metrics and assessment tools

## Testing

Run the complete test suite:

```bash
python -m pytest website/examples/vla_capstone/tests/
```

To run performance benchmarks:

```bash
python website/examples/vla_capstone/tests/test_performance.py
```

## Curriculum Integration

This capstone project integrates with the broader robotics curriculum:
- Builds upon ROS 2 concepts from Module 1
- Uses Isaac Sim simulation from Module 3
- Applies Gazebo simulation concepts from Module 2
- Combines all technologies into a cohesive application

## Educational Objectives

Students completing this module will understand:
- How to integrate multiple AI technologies in a robotics application
- Techniques for multimodal fusion of vision, language, and action
- Methods for creating robust autonomous systems
- Approaches for error recovery and handling uncertainty
- Best practices for embodied AI systems

## Performance Targets

- Voice recognition: ≤500ms processing time
- LLM action generation: ≤3 seconds response time
- Action execution: High success rate in simulation
- System reliability: 95%+ uptime during demonstrations

## Contributing

We welcome contributions to the VLA Capstone implementation. Please see our contributing guidelines in the main repository.

## License

This project is licensed under Apache 2.0 - see the LICENSE file for details.

## Acknowledgments

- NVIDIA for Isaac Sim and related tools
- OpenAI for Whisper and GPT models
- OSRF for Gazebo simulation
- The robotics and AI research communities whose work makes this possible