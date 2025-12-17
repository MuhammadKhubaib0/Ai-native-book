"""
ROS 2 node for multimodal fusion in the VLA system.
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Image, PointCloud2, CameraInfo
from geometry_msgs.msg import PoseStamped
from ..models.multimodal_input import MultimodalInput
from ..models.action_step import ActionStep
from ..services.multimodal_fusion import MultimodalFusionService
from ..services.vision_integration import VisionIntegrationService
from ..services.conflict_resolver import ConflictResolver
from ..services.confidence_manager import ConfidenceManager
from ..validation.multimodal_validation import MultimodalValidationService
from ..config import settings
from ..architectures.vla_selector import VLASelector, VLAArchitectureType
import numpy as np
import cv2
from cv_bridge import CvBridge
import json
import asyncio
from threading import Thread
from datetime import datetime


class MultimodalFusionNode(Node):
    """
    ROS 2 node that fuses multimodal inputs (voice, vision, sensors) for decision making.
    """
    
    def __init__(self):
        super().__init__('multimodal_fusion_node')
        
        # Initialize services
        self.fusion_service = MultimodalFusionService()
        self.vision_service = VisionIntegrationService()
        self.conflict_resolver = ConflictResolver()
        self.confidence_manager = ConfidenceManager()
        self.validator = MultimodalValidationService()
        self.vla_selector = VLASelector()
        
        # Initialize CvBridge for image processing
        self.cv_bridge = CvBridge()
        
        # Data storage for multimodal inputs
        self.latest_voice_data = None
        self.latest_vision_data = None
        self.latest_sensor_data = None
        self.latest_action_sequence = None
        
        # Create subscribers
        self.voice_subscriber = self.create_subscription(
            String,
            'voice_command',
            self.voice_callback,
            10
        )
        
        self.image_subscriber = self.create_subscription(
            Image,
            'camera/image_raw',
            self.image_callback,
            10
        )
        
        self.depth_subscriber = self.create_subscription(
            Image,
            'camera/depth',
            self.depth_callback,
            10
        )
        
        self.lidar_subscriber = self.create_subscription(
            PointCloud2,
            'lidar/points',
            self.lidar_callback,
            10
        )
        
        # Create publishers
        self.fusion_result_publisher = self.create_publisher(
            String,
            'multimodal_fusion_result',
            10
        )
        
        self.action_publisher = self.create_publisher(
            String,  # In a real implementation, this would be a custom action message type
            'fused_action',
            10
        )
        
        self.conflict_publisher = self.create_publisher(
            String,
            'multimodal_conflicts',
            10
        )
        
        # Timer for multimodal fusion processing
        self.fusion_timer = self.create_timer(0.5, self.process_multimodal_inputs)  # Process every 0.5 seconds
        
        self.get_logger().info('Multimodal Fusion Node started')
    
    def voice_callback(self, msg: String):
        """
        Handle incoming voice command messages.
        
        :param msg: String message containing the voice command
        """
        self.get_logger().info(f'Received voice command: {msg.data}')
        
        # Parse the voice command and extract relevant information
        self.latest_voice_data = {
            "transcribed_text": msg.data,
            "timestamp": self.get_clock().now().seconds_nanoseconds(),
            "processed": False
        }
    
    def image_callback(self, msg: Image):
        """
        Handle incoming image messages.
        
        :param msg: Image message from camera
        """
        try:
            # Convert ROS Image message to OpenCV image
            cv_image = self.cv_bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
            
            # Process the image using vision service
            # In a real implementation, this would use the Isaac Sim integration
            # For this example, we'll just store the image
            image_data = {
                "width": msg.width,
                "height": msg.height,
                "encoding": msg.encoding,
                "data": cv_image,  # This would be processed in a real implementation
                "timestamp": msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
            }
            
            self.latest_vision_data = image_data
            self.get_logger().info(f'Received image: {msg.width}x{msg.height}')
        except Exception as e:
            self.get_logger().error(f'Error processing image: {e}')
    
    def depth_callback(self, msg: Image):
        """
        Handle incoming depth image messages.
        
        :param msg: Depth Image message from camera
        """
        try:
            # Convert ROS Image message to numpy array
            depth_image = self.cv_bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
            
            # Process the depth data
            depth_data = {
                "image": depth_image,
                "min_depth": float(np.min(depth_image)),
                "max_depth": float(np.max(depth_image)),
                "timestamp": msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
            }
            
            self.latest_vision_data = self.latest_vision_data or {}
            self.latest_vision_data.update({"depth": depth_data})
            self.get_logger().info(f'Received depth image: min={depth_data["min_depth"]:.2f}, max={depth_data["max_depth"]:.2f}')
        except Exception as e:
            self.get_logger().error(f'Error processing depth image: {e}')
    
    def lidar_callback(self, msg: PointCloud2):
        """
        Handle incoming LIDAR point cloud messages.
        
        :param msg: PointCloud2 message from LIDAR sensor
        """
        try:
            # Process LIDAR data
            # In a real implementation, this would convert the PointCloud2 to useful format
            # For this example, we'll extract basic info
            lidar_data = {
                "frame_id": msg.header.frame_id,
                "timestamp": msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9,
                "width": msg.width,
                "height": msg.height,
                "is_dense": msg.is_dense
            }
            
            self.latest_sensor_data = self.latest_sensor_data or {}
            self.latest_sensor_data.update({"lidar": lidar_data})
            self.get_logger().info(f'Received LIDAR data: {msg.width}x{msg.height} points')
        except Exception as e:
            self.get_logger().error(f'Error processing LIDAR data: {e}')
    
    def process_multimodal_inputs(self):
        """
        Process all available multimodal inputs and perform fusion.
        This runs periodically via timer.
        """
        if not self._has_sufficient_data():
            return
        
        # Create multimodal input
        multimodal_input = MultimodalInput(
            id=f"fusion_input_{int(datetime.now().timestamp())}",
            visual_data=self.latest_vision_data,
            sensor_data=self.latest_sensor_data,
            voice_input_id=self.latest_voice_data["transcribed_text"] if self.latest_voice_data else None,
            confidence=0.8,
            timestamp=datetime.now()
        )
        
        # Validate the multimodal input
        validation_result = self.validator.validate_multimodal_input(multimodal_input)
        if not validation_result.is_valid:
            self.get_logger().error(f"Invalid multimodal input: {validation_result.errors}")
            return
        
        # Process the input in a separate thread to avoid blocking
        fusion_thread = Thread(target=self._perform_fusion, args=(multimodal_input,))
        fusion_thread.start()
    
    def _has_sufficient_data(self) -> bool:
        """
        Check if we have sufficient data from different modalities.
        
        :return: True if sufficient data is available, False otherwise
        """
        return (
            (self.latest_vision_data is not None) or
            (self.latest_sensor_data is not None) or
            (self.latest_voice_data is not None)
        )
    
    def _perform_fusion(self, multimodal_input: MultimodalInput):
        """
        Perform the actual multimodal fusion in a separate thread.
        
        :param multimodal_input: The multimodal input to fuse
        """
        try:
            self.get_logger().info("Performing multimodal fusion...")
            
            # Extract data from multimodal input
            voice_data = {"text": multimodal_input.voice_input_id} if multimodal_input.voice_input_id else None
            vision_data = multimodal_input.visual_data
            sensor_data = multimodal_input.sensor_data
            
            # Detect conflicts between modalities
            conflicts = self.conflict_resolver.detect_conflicts(voice_data, vision_data, sensor_data)
            
            if conflicts:
                self.get_logger().warning(f"Detected {len(conflicts)} conflicts between modalities")
                
                # Publish conflict information
                conflict_msg = String()
                conflict_msg.data = json.dumps({
                    "conflicts": [
                        {"type": c[0].value, "source1": c[1], "source2": c[2]}
                        for c in conflicts
                    ],
                    "timestamp": datetime.now().isoformat()
                })
                self.conflict_publisher.publish(conflict_msg)
                
                # Resolve conflicts
                resolution_results = self.conflict_resolver.resolve_conflicts(
                    conflicts, voice_data, vision_data, sensor_data
                )
                
                # In a real implementation, the resolution would be used in fusion
                self.get_logger().info(f"Resolved {len(resolution_results)} conflicts")
            
            # Perform multimodal fusion with conflict resolution results
            fused_result, confidence = self.fusion_service.fuse_modalities(
                voice_data=voice_data,
                vision_data=vision_data,
                sensor_data=sensor_data
            )
            
            # Validate the fusion result
            fusion_result_validation = self.validator.validate_multimodal_fusion_result(
                {
                    "fused_output": fused_result,
                    "confidence": confidence,
                    "method": self.fusion_service.fusion_method.value
                },
                ["voice", "vision", "sensor"]  # Input modalities
            )
            
            if not fusion_result_validation.is_valid:
                self.get_logger().warning(f"Fusion result validation issues: {fusion_result_validation.errors}")
            
            # Check if we should execute the action based on confidence
            should_execute = self.confidence_manager.should_execute_action(confidence)
            
            if should_execute:
                self.get_logger().info(f"Action approved with confidence {confidence:.2f}")
                
                # Generate action sequence from fusion result
                action_sequence = self._create_action_sequence_from_result(fused_result)
                
                if action_sequence:
                    # Publish the action sequence
                    action_msg = String()
                    action_msg.data = json.dumps({
                        "action_sequence": [action.dict() for action in action_sequence],
                        "confidence": confidence,
                        "timestamp": datetime.now().isoformat()
                    })
                    self.action_publisher.publish(action_msg)
                    
                    self.latest_action_sequence = action_sequence
                    self.get_logger().info(f"Published action sequence with {len(action_sequence)} steps")
            else:
                self.get_logger().info(f"Action rejected due to low confidence ({confidence:.2f})")
            
            # Publish fusion result
            fusion_msg = String()
            fusion_msg.data = json.dumps({
                "fusion_result": fused_result,
                "confidence": confidence,
                "should_execute": should_execute,
                "timestamp": datetime.now().isoformat()
            })
            self.fusion_result_publisher.publish(fusion_msg)
            
            self.get_logger().info("Multimodal fusion completed successfully")
            
        except Exception as e:
            self.get_logger().error(f'Error in multimodal fusion: {e}')
    
    def _create_action_sequence_from_result(self, fusion_result: Dict[str, Any]) -> list:
        """
        Create an action sequence from the fusion result.
        
        :param fusion_result: The result from multimodal fusion
        :return: List of action steps
        """
        actions = []
        
        # This is a simplified approach - in reality, you'd have more sophisticated logic
        # to convert fusion results to specific robot actions
        
        if isinstance(fusion_result, dict) and "intent" in fusion_result:
            intent = fusion_result["intent"]
            
            # Map intent to action type
            if intent in ["navigation", "move", "go", "navigate"]:
                action = ActionStep(
                    id=f"action_{int(datetime.now().timestamp())}",
                    action_sequence_id=f"seq_{int(datetime.now().timestamp())}",
                    action_type="navigation",
                    parameters=fusion_result.get("parameters", {}),
                    timeout=10,
                    order=0
                )
                actions.append(action)
            elif intent in ["manipulation", "grasp", "pick", "place"]:
                action = ActionStep(
                    id=f"action_{int(datetime.now().timestamp())}",
                    action_sequence_id=f"seq_{int(datetime.now().timestamp())}",
                    action_type="manipulation",
                    parameters=fusion_result.get("parameters", {}),
                    timeout=15,
                    order=0
                )
                actions.append(action)
            elif intent in ["perception", "detect", "find", "see"]:
                action = ActionStep(
                    id=f"action_{int(datetime.now().timestamp())}",
                    action_sequence_id=f"seq_{int(datetime.now().timestamp())}",
                    action_type="perception",
                    parameters=fusion_result.get("parameters", {}),
                    timeout=5,
                    order=0
                )
                actions.append(action)
        
        return actions


def main(args=None):
    """
    Main function to run the Multimodal Fusion Node.
    """
    rclpy.init(args=args)
    
    multimodal_fusion_node = MultimodalFusionNode()
    
    try:
        rclpy.spin(multimodal_fusion_node)
    except KeyboardInterrupt:
        pass
    finally:
        multimodal_fusion_node.destroy_node()
        rclpy.shutdown()


# If you want to run this as a standalone script for testing
if __name__ == '__main__':
    main()