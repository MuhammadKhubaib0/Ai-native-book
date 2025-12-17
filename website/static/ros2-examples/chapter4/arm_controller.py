#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Header
import math
import time
from builtin_interfaces.msg import Time


class ArmController(Node):
    def __init__(self):
        super().__init__('arm_controller')
        
        # Create publisher for joint states
        self.joint_publisher = self.create_publisher(JointState, '/joint_states', 10)
        
        # Define joint names
        self.joint_names = [
            'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
            'wrist_flex_joint', 'wrist_roll_joint', 'gripper_joint'
        ]
        
        # Timer for updating joint positions
        self.timer = self.create_timer(0.1, self.timer_callback)
        
        # Initialize joint positions
        self.joint_positions = [0.0] * len(self.joint_names)
        
        # Movement pattern index
        self.pattern_idx = 0
        
        # Define movement patterns
        self.movement_patterns = [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # Home position
            [0.5, 0.3, 0.2, 0.1, 0.4, 0.01],  # Pattern 1
            [-0.3, 0.5, 0.4, -0.2, 0.6, 0.015],  # Pattern 2
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # Home position again
            [0.2, -0.4, 0.6, 0.3, -0.5, 0.02]  # Pattern 3
        ]
        
        self.get_logger().info('Arm Controller node initialized')

    def timer_callback(self):
        # Create JointState message
        msg = JointState()
        
        # Set header
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"
        
        # Set joint names
        msg.name = self.joint_names
        
        # Update positions based on current pattern
        pattern = self.movement_patterns[self.pattern_idx]
        
        # Move toward the target position
        for i in range(len(self.joint_positions)):
            # Apply a smooth transition to the target position
            self.joint_positions[i] += (pattern[i] - self.joint_positions[i]) * 0.1
            
        # Publish the joint positions
        msg.position = self.joint_positions
        
        # Publish the message
        self.joint_publisher.publish(msg)
        
        # Log current positions
        self.get_logger().info(f'Published joint states: {self.joint_positions}')
        
        # Change pattern every 5 seconds
        if self.get_clock().now().nanoseconds // 1_000_000_000 % 5 == 0 and self.pattern_idx < len(self.movement_patterns) - 1:
            self.pattern_idx += 1
            self.get_logger().info(f'Switching to pattern {self.pattern_idx + 1}')


def main(args=None):
    rclpy.init(args=args)
    
    arm_controller = ArmController()
    
    try:
        rclpy.spin(arm_controller)
    except KeyboardInterrupt:
        pass
    finally:
        arm_controller.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()