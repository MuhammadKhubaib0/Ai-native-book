# Quickstart Guide: Gazebo Unity Digital Twin Development

**Feature**: 2-gazebo-unity-digital-twin
**Date**: 2025-12-12

## Getting Started

This quickstart guide will help you set up the development environment for the Gazebo Unity Digital Twin textbook chapters.

### Prerequisites

1. **System Requirements**:
   - Operating System: Ubuntu 22.04 LTS (recommended) or compatible Linux distribution for Gazebo; Windows 10/11 or macOS for Unity
   - RAM: 16GB minimum (32GB recommended for Unity development)
   - Storage: 20GB free space for Gazebo, Unity, and examples
   - For Unity: Dedicated GPU with at least 4GB VRAM recommended
   - For Gazebo: GPU with OpenGL 2.0+ support

2. **Software Requirements**:
   - Git
   - Node.js (v16 or higher) and npm
   - Python 3.8 or higher
   - ROS 2 Humble Hawksbill
   - Gazebo Harmonic
   - Unity Hub and Unity 2022.3 LTS
   - Docusaurus CLI: `npm install -g @docusaurus/cli`
   - Unity ML-Agents Toolkit

### Setting Up the Environment

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd physical-ai-textbook
   ```

2. **Install Docusaurus Dependencies**:
   ```bash
   cd website
   npm install
   ```

3. **Install Gazebo Harmonic** (if not already installed):
   Follow the official installation guide: https://gazebosim.org/docs/harmonic/install

4. **Install Unity 2022.3 LTS**:
   - Download and install Unity Hub
   - Use Unity Hub to install Unity 2022.3 LTS
   - Install the ML-Agents package through Package Manager

5. **Install ROS 2 Humble** (if not already installed):
   Follow the official installation guide: https://docs.ros.org/en/humble/Installation.html

6. **Source ROS 2 Environment**:
   ```bash
   source /opt/ros/humble/setup.bash
   ```

7. **Install Unity ML-Agents**:
   - Open Unity Hub
   - Create a new 3D project or open an existing one
   - Go to Window > Package Manager
   - Install ML-Agents Toolkit from the package manager

### Running the Textbook Locally

1. **Start the Docusaurus Development Server**:
   ```bash
   cd website
   npm run start
   ```

2. **Access the Textbook**:
   Open your browser and go to http://localhost:3000

### Adding New Content

1. **Create a New Chapter**:
   - Add a new MDX file in `website/docs/module2-gazebo-unity/`
   - Follow the naming convention: `chapter-number-title.mdx`
   - Use the Docusaurus documentation structure

2. **Example Chapter Structure**:
   ```md
   ---
   id: physics-simulation
   title: Physics Simulation in Gazebo
   sidebar_position: 1
   ---
   
   # Physics Simulation in Gazebo
   
   Content of the chapter goes here...
   
   ## Rigid Body Dynamics
   
   Explanation of rigid body dynamics in Gazebo...
   
   import CodeBlock from '@theme/CodeBlock';
   import PhysicsExampleSDF from '!!raw-loader!@site/static/simulation-examples/chapter1/physics_demo.sdf';
   
   ```xml
   {PhysicsExampleSDF}
   ```
   
   ## Gravity and Collisions
   
   Explanation of gravity and collision models...
   ```

3. **Add Simulation Examples**:
   - Place SDF files in `static/simulation-examples/chapter1/`
   - Place Unity scene files in `static/simulation-examples/chapter3/`
   - Place Python examples in appropriate chapter directories
   - Reference them in MDX files using the CodeBlock component

### Testing Gazebo Simulations

1. **Set Up Gazebo Workspace**:
   ```bash
   mkdir -p ~/gazebo_textbook_ws/src
   cd ~/gazebo_textbook_ws
   colcon build
   source install/setup.bash
   ```

2. **Run a Gazebo Example**:
   ```bash
   cd ~/gazebo_textbook_ws
   # Copy example files from the textbook repository
   cp /path/to/textbook/static/simulation-examples/chapter1/* src/
   colcon build
   source install/setup.bash
   
   # Launch the Gazebo simulation
   gazebo --verbose /path/to/your/world.sdf
   ```

### Testing Unity Scenes

1. **Open Unity Project**:
   - Launch Unity Hub
   - Open the textbook Unity project located at `website/static/simulation-examples/unity-project/`
   - Navigate to the scene files in Assets/Scenes/

2. **Run a Unity Example**:
   - Select the scene file you want to run
   - Click the Play button in the Unity Editor
   - Verify that the scene loads correctly and performs as expected

### Building for Production

1. **Build the Static Site**:
   ```bash
   cd website
   npm run build
   ```

2. **Serve the Built Site** (for testing):
   ```bash
   npm run serve
   ```

### Troubleshooting

1. **Docusaurus Issues**:
   - If you encounter npm errors, try clearing the cache: `npm cache clean --force`
   - If modules are missing, reinstall with: `rm -rf node_modules && npm install`

2. **Gazebo Issues**:
   - Make sure to source the ROS 2 environment in each new terminal
   - Check Gazebo installation with: `gazebo --version`
   - Verify environment setup with: `echo $GAZEBO_VERSION`

3. **Unity Issues**:
   - Ensure Unity 2022.3 LTS is installed via Unity Hub
   - Check that ML-Agents is properly installed in your project
   - Verify that your system meets Unity's hardware requirements

4. **Python Import Errors**:
   - Ensure rclpy is installed: `pip3 install rclpy`
   - Make sure you're using Python 3.8 or higher: `python3 --version`