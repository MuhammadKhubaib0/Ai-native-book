#!/usr/bin/env python3
# This is how we mark the script as executable and that it should be run with Python 3

import rclpy
from rclpy.node import Node


def main(args=None):
    # Initialize the ROS 2 client library
    rclpy.init(args=args)
    
    # Create an instance of your custom node class
    node = MinimalNode()
    
    # Use the spin function to periodically process callbacks
    rclpy.spin(node)
    
    # Destroy the node explicitly (optional - otherwise it will be done automatically when the node object goes out of scope)
    node.destroy_node()
    rclpy.shutdown()


class MinimalNode(Node):
    def __init__(self):
        # Initialize the parent Node class with a name
        super().__init__('minimal_publisher')