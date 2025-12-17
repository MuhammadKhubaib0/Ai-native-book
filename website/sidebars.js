// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  module1Sidebar: [
    {
      type: 'category',
      label: 'Module 1: The Robotic Nervous System (ROS 2)',
      items: [
        'module1-ros2/intro',
        'module1-ros2/python-agents',
        'module1-ros2/urdf-humanoids',
        'module1-ros2/practical-lab',
      ],
      collapsed: false,
    },
  ],
  module2Sidebar: [
    {
      type: 'category',
      label: 'Module 2: The Digital Twin (Gazebo & Unity)',
      items: [
        'module2-gazebo-unity/physics-simulation',
        'module2-gazebo-unity/sensor-simulation',
        'module2-gazebo-unity/unity-rendering',
        'module2-gazebo-unity/sim-to-real-transfer',
      ],
      collapsed: false,
    },
  ],
  module3Sidebar: [
    {
      type: 'category',
      label: 'Module 3: NVIDIA Isaac',
      items: [
        'module3-isaac/isaac-sim/overview',
        'module3-isaac/isaac-sim/setup',
        'module3-isaac/isaac-ros/perception',
        'module3-isaac/isaac-ros/vslam',
        'module3-isaac/synthetic-data/generation',
        'module3-isaac/synthetic-data/domain-randomization',
        'module3-isaac/nav2-humanoid/navigation',
        'module3-isaac/nav2-humanoid/path-planning',
        'module3-isaac/jetson-deployment/optimization',
        'module3-isaac/jetson-deployment/quantization',
      ],
      collapsed: false,
    },
  ],
  module4Sidebar: [
    {
      type: 'category',
      label: 'Module 4: Voice-to-Action (VLA)',
      items: [
        'module4-vla/voice-to-action',
        'module4-vla/llm-driven-planning',
        'module4-vla/capstone-autonomous-humanoid',
      ],
      collapsed: false,
    },
  ],
};

module.exports = sidebars;