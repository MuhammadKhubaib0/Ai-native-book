"""
ROS 2 launch file for the complete VLA (Vision-Language-Action) system.
This launch file starts all necessary nodes for the VLA Capstone project.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, ComposableNodeContainer
from launch_ros.descriptions import ComposableNode
from launch.event_handlers import OnProcessExit
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    """
    Generate the launch description for the VLA system.
    """
    # Declare launch arguments
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Namespace for all VLA nodes'
    )
    
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock if true'
    )
    
    isaac_sim_enabled_arg = DeclareLaunchArgument(
        'isaac_sim_enabled',
        default_value='false',
        description='Enable Isaac Sim integration'
    )
    
    gazebo_enabled_arg = DeclareLaunchArgument(
        'gazebo_enabled',
        default_value='true',
        description='Enable Gazebo simulation'
    )
    
    # Get launch configurations
    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    isaac_sim_enabled = LaunchConfiguration('isaac_sim_enabled')
    gazebo_enabled = LaunchConfiguration('gazebo_enabled')
    
    # Get package directories
    vla_package_dir = get_package_share_directory('vla_capstone')
    gazebo_package_dir = get_package_share_directory('gazebo_ros_pkgs')
    
    # Define nodes
    nodes = []
    
    # 1. Voice processing node
    voice_node = Node(
        package='vla_capstone',
        executable='voice_processor_node',
        name='voice_processor',
        namespace=namespace,
        parameters=[
            {'use_sim_time': use_sim_time},
        ],
        remappings=[
            ('audio_input', 'microphone/audio_raw'),
            ('voice_command', 'vla/voice_command'),
        ],
        output='screen'
    )
    nodes.append(voice_node)
    
    # 2. Vision processing node (only if Isaac Sim is enabled)
    vision_node = Node(
        package='vla_capstone',
        executable='vision_processor_node',
        name='vision_processor',
        namespace=namespace,
        parameters=[
            {'use_sim_time': use_sim_time},
            {'process_isaac_sim_data': isaac_sim_enabled}
        ],
        remappings=[
            ('camera/image_raw', 'isaac_sim/camera/image'),
            ('camera/depth', 'isaac_sim/camera/depth'),
            ('vision_output', 'vla/vision_output'),
        ],
        condition=IfCondition(isaac_sim_enabled),
        output='screen'
    )
    nodes.append(vision_node)
    
    # 3. VLA main processing node
    vla_main_node = Node(
        package='vla_capstone',
        executable='vla_main_node',
        name='vla_main',
        namespace=namespace,
        parameters=[
            {'use_sim_time': use_sim_time},
            {'enable_isaac_sim_integration': isaac_sim_enabled},
        ],
        remappings=[
            ('voice_command', 'vla/voice_command'),
            ('vision_data', 'vla/vision_output'),
            ('action_sequence', 'vla/action_sequence'),
            ('system_state', 'vla/system_state'),
        ],
        output='screen'
    )
    nodes.append(vla_main_node)
    
    # 4. Action execution node
    action_execution_node = Node(
        package='vla_capstone',
        executable='action_execution_node',
        name='action_execution',
        namespace=namespace,
        parameters=[
            {'use_sim_time': use_sim_time},
        ],
        remappings=[
            ('action_sequence', 'vla/action_sequence'),
            ('execution_status', 'vla/execution_status'),
            ('robot_command', 'robot/cmd_vel'),
        ],
        output='screen'
    )
    nodes.append(action_execution_node)
    
    # 5. Navigation node (for navigation actions)
    navigation_node = Node(
        package='nav2_bringup',
        executable='nav2_bringup',
        name='navigation_server',
        namespace=namespace,
        parameters=[
            PathJoinSubstitution([vla_package_dir, 'config', 'nav2_params.yaml']),
            {'use_sim_time': use_sim_time},
        ],
        output='screen'
    )
    nodes.append(navigation_node)
    
    # 6. Perception node (for object detection)
    perception_node = Node(
        package='vla_capstone',
        executable='perception_node',
        name='perception',
        namespace=namespace,
        parameters=[
            {'use_sim_time': use_sim_time},
        ],
        remappings=[
            ('camera/image_raw', 'isaac_sim/camera/image'),
            ('camera/depth', 'isaac_sim/camera/depth'),
            ('object_detections', 'vla/object_detections'),
        ],
        output='screen'
    )
    nodes.append(perception_node)
    
    # 7. Simulation integration node (for Gazebo)
    simulation_node = Node(
        package='vla_capstone',
        executable='simulation_integration_node',
        name='simulation_integration',
        namespace=namespace,
        parameters=[
            {'use_sim_time': use_sim_time},
            {'enable_gazebo': gazebo_enabled},
            {'enable_isaac_sim': isaac_sim_enabled},
        ],
        remappings=[
            ('sim/robot_state', 'robot/odom'),
            ('sim/robot_pose', 'robot/pose'),
        ],
        output='screen'
    )
    nodes.append(simulation_node)
    
    # 8. Error recovery node
    error_recovery_node = Node(
        package='vla_capstone',
        executable='error_recovery_node',
        name='error_recovery',
        namespace=namespace,
        parameters=[
            {'use_sim_time': use_sim_time},
        ],
        remappings=[
            ('execution_status', 'vla/execution_status'),
            ('recovery_command', 'vla/recovery_command'),
        ],
        output='screen'
    )
    nodes.append(error_recovery_node)
    
    # 9. LLM integration node (handles communication with external LLMs)
    llm_node = Node(
        package='vla_capstone',
        executable='llm_integration_node',
        name='llm_integration',
        namespace=namespace,
        parameters=[
            {'use_sim_time': use_sim_time},
        ],
        remappings=[
            ('vla_task_request', 'vla/task_request'),
            ('vla_task_response', 'vla/task_response'),
        ],
        output='screen'
    )
    nodes.append(llm_node)
    
    # 10. Evaluation metrics node
    evaluation_node = Node(
        package='vla_capstone',
        executable='evaluation_metrics_node',
        name='evaluation_metrics',
        namespace=namespace,
        parameters=[
            {'use_sim_time': use_sim_time},
        ],
        remappings=[
            ('execution_results', 'vla/execution_status'),
            ('evaluation_output', 'vla/evaluation_results'),
        ],
        output='screen'
    )
    nodes.append(evaluation_node)
    
    # Conditional inclusion: Isaac Sim launch if enabled
    isaac_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                get_package_share_directory('isaac_sim_ros_bringup'),
                'launch',
                'isaac_sim.launch.py'
            ])
        ]),
        condition=IfCondition(isaac_sim_enabled)
    )
    
    # Conditional inclusion: Gazebo launch if enabled
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                get_package_share_directory('gazebo_ros'),
                'launch',
                'gazebo.launch.py'
            ])
        ]),
        condition=IfCondition(gazebo_enabled)
    )
    
    # Create the launch description
    ld = LaunchDescription()
    
    # Add launch arguments
    ld.add_action(namespace_arg)
    ld.add_action(use_sim_time_arg)
    ld.add_action(isaac_sim_enabled_arg)
    ld.add_action(gazebo_enabled_arg)
    
    # Add conditional launches
    ld.add_action(isaac_sim_launch)
    ld.add_action(gazebo_launch)
    
    # Add all nodes
    for node in nodes:
        ld.add_action(node)
    
    # Add event handlers for graceful shutdown
    for node in nodes:
        ld.add_action(RegisterEventHandler(
            OnProcessExit(
                target_action=node,
                on_exit=[
                    # Custom shutdown logic could go here
                ]
            )
        ))
    
    return ld


# Alternative launch configuration using ComposableNodeContainer for better performance
def generate_composable_launch_description():
    """
    Generate a composable launch description for better performance.
    """
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Namespace for all VLA nodes'
    )
    
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock if true'
    )
    
    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    
    # Create a container for composable nodes
    vla_container = ComposableNodeContainer(
        name='vla_composable_container',
        namespace=namespace,
        package='rclcpp_components',
        executable='component_container_mt',
        parameters=[
            {'use_sim_time': use_sim_time}
        ],
        output='screen'
    )
    
    # Define composable nodes
    composable_nodes = [
        ComposableNode(
            package='vla_capstone',
            plugin='vla_capstone::VoiceProcessorComponent',
            name='voice_processor_component',
            parameters=[
                {'use_sim_time': use_sim_time}
            ],
            remappings=[
                ('audio_input', 'microphone/audio_raw'),
                ('voice_command', 'vla/voice_command'),
            ]
        ),
        ComposableNode(
            package='vla_capstone',
            plugin='vla_capstone::VLAMainComponent',
            name='vla_main_component',
            parameters=[
                {'use_sim_time': use_sim_time}
            ],
            remappings=[
                ('voice_command', 'vla/voice_command'),
                ('action_sequence', 'vla/action_sequence'),
            ]
        ),
        ComposableNode(
            package='vla_capstone',
            plugin='vla_capstone::ActionExecutionComponent',
            name='action_execution_component',
            parameters=[
                {'use_sim_time': use_sim_time}
            ],
            remappings=[
                ('action_sequence', 'vla/action_sequence'),
                ('robot_command', 'robot/cmd_vel'),
            ]
        )
    ]
    
    # Create launch description
    ld = LaunchDescription()
    
    # Add launch arguments
    ld.add_action(namespace_arg)
    ld.add_action(use_sim_time_arg)
    
    # Add container and nodes
    ld.add_action(vla_container)
    
    # Add each composable node to the container
    for node in composable_nodes:
        ld.add_action(node)
    
    return ld


# Additional launch configurations for different scenarios

def generate_minimal_launch_description():
    """
    Generate a minimal launch description for basic functionality.
    """
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Namespace for all VLA nodes'
    )
    
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock if true'
    )
    
    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    
    # Minimal nodes for basic functionality
    nodes = [
        Node(
            package='vla_capstone',
            executable='voice_processor_node',
            name='voice_processor',
            namespace=namespace,
            parameters=[
                {'use_sim_time': use_sim_time},
            ],
            remappings=[
                ('audio_input', 'microphone/audio_raw'),
                ('voice_command', 'vla/voice_command'),
            ],
            output='screen'
        ),
        Node(
            package='vla_capstone',
            executable='vla_main_node',
            name='vla_main',
            namespace=namespace,
            parameters=[
                {'use_sim_time': use_sim_time},
            ],
            remappings=[
                ('voice_command', 'vla/voice_command'),
                ('action_sequence', 'vla/action_sequence'),
            ],
            output='screen'
        ),
        Node(
            package='vla_capstone',
            executable='action_execution_node',
            name='action_execution',
            namespace=namespace,
            parameters=[
                {'use_sim_time': use_sim_time},
            ],
            remappings=[
                ('action_sequence', 'vla/action_sequence'),
                ('robot_command', 'robot/cmd_vel'),
            ],
            output='screen'
        )
    ]
    
    ld = LaunchDescription()
    
    # Add launch arguments
    ld.add_action(namespace_arg)
    ld.add_action(use_sim_time_arg)
    
    # Add minimal nodes
    for node in nodes:
        ld.add_action(node)
    
    return ld


def generate_hardware_launch_description():
    """
    Generate a launch description for running on real hardware.
    """
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Namespace for all VLA nodes'
    )
    
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock if true'
    )
    
    robot_model_arg = DeclareLaunchArgument(
        'robot_model',
        default_value='custom_humanoid',
        description='Robot model to use'
    )
    
    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    robot_model = LaunchConfiguration('robot_model')
    
    # Hardware-specific nodes
    nodes = [
        Node(
            package='vla_capstone',
            executable='voice_processor_node',
            name='voice_processor',
            namespace=namespace,
            parameters=[
                {'use_sim_time': use_sim_time},
            ],
            remappings=[
                ('audio_input', 'microphone/audio_raw'),
                ('voice_command', 'vla/voice_command'),
            ],
            output='screen'
        ),
        Node(
            package='vla_capstone',
            executable='vla_main_node',
            name='vla_main',
            namespace=namespace,
            parameters=[
                {'use_sim_time': use_sim_time},
                {'robot_model': robot_model}
            ],
            remappings=[
                ('voice_command', 'vla/voice_command'),
                ('action_sequence', 'vla/action_sequence'),
                ('robot_state', 'hardware/robot_state'),
            ],
            output='screen'
        ),
        Node(
            package='vla_capstone',
            executable='action_execution_node',
            name='action_execution',
            namespace=namespace,
            parameters=[
                {'use_sim_time': use_sim_time},
                {'robot_model': robot_model}
            ],
            remappings=[
                ('action_sequence', 'vla/action_sequence'),
                ('robot_command', 'hardware/robot_cmd'),
                ('robot_state', 'hardware/robot_state'),
            ],
            output='screen'
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            namespace=namespace,
            parameters=[
                {'robot_description': PathJoinSubstitution([
                    get_package_share_directory('vla_capstone'),
                    'urdf',
                    PathJoinSubstitution([robot_model, 'robot.urdf'])
                ])},
                {'use_sim_time': use_sim_time}
            ],
            output='screen'
        )
    ]
    
    ld = LaunchDescription()
    
    # Add launch arguments
    ld.add_action(namespace_arg)
    ld.add_action(use_sim_time_arg)
    ld.add_action(robot_model_arg)
    
    # Add hardware-specific nodes
    for node in nodes:
        ld.add_action(node)
    
    return ld


# Example usage for different launch configurations
if __name__ == '__main__':
    # The main launch file provides the standard VLA system launch
    # Other configurations can be accessed by calling their respective functions:
    
    # For composable launch: generate_composable_launch_description()
    # For minimal launch: generate_minimal_launch_description()
    # For hardware launch: generate_hardware_launch_description()
    
    # The standard launch is generated by the main function
    launch_description = generate_launch_description()
    
    # This would normally be handled by the launch system,
    # but for testing purposes we can print the structure:
    print("VLA System Launch Configuration Generated")
    print("Nodes included:")
    print("- Voice Processor Node")
    print("- Vision Processor Node (conditional)")
    print("- VLA Main Processing Node")
    print("- Action Execution Node")
    print("- Navigation Server")
    print("- Perception Node")
    print("- Simulation Integration Node")
    print("- Error Recovery Node")
    print("- LLM Integration Node")
    print("- Evaluation Metrics Node")
    
    # Conditional launches:
    print("\nConditional Launches:")
    print("- Isaac Sim (enabled if isaac_sim_enabled:=true)")
    print("- Gazebo (enabled if gazebo_enabled:=true)")
    
    print("\nLaunch with: ros2 launch vla_capstone vla_system.launch.py")
    print("With options: namespace:=vla_robot use_sim_time:=true isaac_sim_enabled:=true gazebo_enabled:=true")