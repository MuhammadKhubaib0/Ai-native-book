# Quickstart Guide: ROS 2 Textbook Development

**Feature**: 1-ros2-textbook-chapters
**Date**: 2025-12-12

## Getting Started

This quickstart guide will help you set up the development environment for the ROS 2 textbook chapters.

### Prerequisites

1. **System Requirements**:
   - Operating System: Ubuntu 22.04 LTS (recommended) or compatible Linux distribution
   - RAM: 8GB minimum, 16GB recommended
   - Storage: 10GB free space for ROS 2 installation and examples
   - For simulation examples: GPU with at least 2GB VRAM recommended

2. **Software Requirements**:
   - Git
   - Node.js (v16 or higher) and npm
   - Python 3.8 or higher
   - ROS 2 Humble Hawksbill
   - Docusaurus CLI: `npm install -g @docusaurus/cli`

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

3. **Install ROS 2 Humble** (if not already installed):
   Follow the official installation guide: https://docs.ros.org/en/humble/Installation.html

4. **Source ROS 2 Environment**:
   ```bash
   source /opt/ros/humble/setup.bash
   ```

5. **Install Python Dependencies** (if any required for examples):
   ```bash
   pip3 install rclpy
   ```

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
   - Add a new MDX file in `website/docs/module1-ros2/`
   - Follow the naming convention: `chapter-number-title.mdx`
   - Use the Docusaurus documentation structure

2. **Example Chapter Structure**:
   ```md
   ---
   id: intro-to-ros2
   title: Introduction to ROS 2
   sidebar_position: 1
   ---
   
   # Introduction to ROS 2
   
   Content of the chapter goes here...
   
   ## Architecture
   
   Explanation of ROS 2 architecture...
   
   import CodeBlock from '@theme/CodeBlock';
   import HelloWorldPython from '!!raw-loader!@site/static/ros2-examples/chapter1/hello_world.py';
   
   ```python
   {HelloWorldPython}
   ```
   
   ## Nodes, Topics, and Services
   
   Explanation of core concepts...
   ```

3. **Add Code Examples**:
   - Place Python examples in `static/ros2-examples/chapter1/`
   - Reference them in MDX files using the CodeBlock component

### Testing Code Examples

1. **Set Up ROS 2 Workspace**:
   ```bash
   mkdir -p ~/ros2_textbook_ws/src
   cd ~/ros2_textbook_ws
   colcon build
   source install/setup.bash
   ```

2. **Run an Example**:
   ```bash
   cd ~/ros2_textbook_ws
   # Copy example files from the textbook repository
   cp /path/to/textbook/static/ros2-examples/chapter1/*.py src/
   colcon build
   source install/setup.bash
   
   # Run the example
   ros2 run my_package example_node
   ```

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

2. **ROS 2 Issues**:
   - Make sure to source the ROS 2 environment in each new terminal
   - Check ROS 2 installation with: `ros2 --version`
   - Verify environment setup with: `echo $ROS_DISTRO`

3. **Python Import Errors**:
   - Ensure rclpy is installed: `pip3 install rclpy`
   - Make sure you're using Python 3.8 or higher: `python3 --version`