"""
ROS 2 node for processing LLM-based action generation in the VLA system.
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import JointState
from geometry_msgs.msg import PoseStamped
from ..models.action_sequence import ActionSequence
from ..models.voice_command import VoiceCommand
from ..services.llm_service import LLMService, LLMConfig
from ..services.task_decomposition import TaskDecompositionService
from ..services.action_sequencer import ActionSequencer
from ..services.action_validator import ActionValidator
from ..services.error_recovery import ErrorRecoveryService, ErrorType, RecoveryStrategy
from ..config import settings
from ..validation.voice_command_validation import validate_voice_command_for_execution
from ..formatters.voice_response_formatter import VoiceResponseFormatter
import json
import asyncio
from threading import Thread


class LLMActionNode(Node):
    """
    ROS 2 node that processes natural language commands using LLMs and generates action sequences.
    """
    
    def __init__(self):
        super().__init__('llm_action_node')
        
        # Initialize services
        self.llm_service = LLMService(LLMConfig(
            model_name=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        ))
        self.task_decomposer = TaskDecompositionService()
        self.action_sequencer = ActionSequencer(robot_capabilities=[
            "navigation", "manipulation", "perception", "interaction"
        ])
        self.action_validator = ActionValidator(
            robot_capabilities=["navigation", "manipulation", "perception", "interaction"],
            ros_action_list=[
                "nav2_msgs/action/NavigateToPose",
                "control_msgs/action/FollowJointTrajectory",
                "moveit_msgs/action/MoveGroup"
            ]
        )
        self.error_recovery = ErrorRecoveryService()
        self.response_formatter = VoiceResponseFormatter()
        
        # Create subscribers
        self.command_subscription = self.create_subscription(
            String,
            'natural_language_command',
            self.command_callback,
            10
        )
        
        # Create publishers
        self.action_sequence_publisher = self.create_publisher(
            String,  # In a real implementation, this would be a custom message type
            'action_sequence',
            10
        )
        
        self.error_publisher = self.create_publisher(
            String,
            'llm_error',
            10
        )
        
        # Timer for asynchronous processing
        self.processing_timer = self.create_timer(0.1, self.process_pending_commands)
        
        self.pending_commands = []
        
        self.get_logger().info('LLM Action Node started')
    
    def command_callback(self, msg: String):
        """
        Handle incoming natural language commands.
        
        :param msg: String message containing the natural language command
        """
        self.get_logger().info(f'Received natural language command: {msg.data}')
        
        # Add to pending commands for processing
        voice_cmd = VoiceCommand(
            id=f"cmd_{len(self.pending_commands)}",
            transcribed_text=msg.data,
            intent="unknown",  # Will be filled by LLM
            parameters={},
            confidence=1.0,  # Text input is fully confident
        )
        
        self.pending_commands.append(voice_cmd)
    
    def process_pending_commands(self):
        """
        Process any pending commands in the queue.
        This runs periodically via timer.
        """
        if not self.pending_commands:
            return
        
        # Process the first pending command
        voice_command = self.pending_commands.pop(0)
        
        # Process command in a separate thread to avoid blocking
        command_thread = Thread(target=self.process_command, args=(voice_command,))
        command_thread.start()
    
    def process_command(self, voice_command: VoiceCommand):
        """
        Process a single voice command to generate an action sequence.
        
        :param voice_command: The voice command to process
        """
        try:
            self.get_logger().info(f'Processing command: {voice_command.transcribed_text}')
            
            # Validate the voice command first
            validation_result = validate_voice_command_for_execution(voice_command)
            if not validation_result.is_valid:
                self.get_logger().error(f"Invalid voice command: {validation_result.errors}")
                self.publish_error(f"Invalid command: {validation_result.errors}")
                return
            
            # Generate action sequence using LLM
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Use the LLM to generate a sequence of actions
            # This involves decomposing the task and sequencing the actions
            task_decomposition = loop.run_until_complete(
                self.task_decomposer.decompose_task(
                    command=voice_command.transcribed_text,
                    robot_capabilities=self.action_sequencer.robot_capabilities
                )
            )
            
            # Convert task decomposition to actions for LLM generation
            action_descriptions = [f"{task.description} with {task.parameters}" for task in task_decomposition]
            combined_command = f"Perform the following actions: {', '.join(action_descriptions)}"
            
            # Generate action steps using LLM
            action_steps = loop.run_until_complete(
                self.llm_service.generate_action_sequence(
                    intent="task_execution",
                    parameters={"command": combined_command, "tasks": [task.dict() for task in task_decomposition]},
                    context={"capabilities": self.action_sequencer.robot_capabilities}
                )
            )
            
            # Sequence the actions into a proper sequence
            action_sequence = self.action_sequencer.sequence_actions(
                actions=[{
                    "id": step.id,
                    "action_type": step.action_type,
                    "parameters": step.parameters,
                    "timeout": step.timeout,
                    "order": step.order
                } for step in action_steps] if action_steps else [],
                voice_command=voice_command
            )
            
            # Validate the generated action sequence
            validation_issues = self.action_validator.validate_action_sequence(action_sequence, voice_command)
            if validation_issues:
                self.get_logger().warning(f"Validation issues found: {[str(issue) for issue in validation_issues]}")
                
                # Check if the sequence is valid for execution despite warnings
                if not self.action_validator.validate_for_execution(action_sequence, voice_command):
                    self.get_logger().error("Action sequence is invalid for execution")
                    
                    # Try recovery
                    recovery_result = self.error_recovery.handle_error(
                        error_type=ErrorType.VALIDATION_ERROR,
                        action_sequence=action_sequence,
                        error_details={"validation_issues": [str(issue) for issue in validation_issues]}
                    )
                    
                    if recovery_result["strategy"] == RecoveryStrategy.ABORT.value:
                        self.publish_error(f"Recovery failed: {recovery_result}")
                        loop.close()
                        return
            
            # Publish the action sequence
            self.publish_action_sequence(action_sequence)
            
            loop.close()
            
            self.get_logger().info(f"Published action sequence with {len(action_sequence.sequence)} steps")
            
        except Exception as e:
            self.get_logger().error(f'Error processing command: {str(e)}')
            self.publish_error(f"Processing error: {str(e)}")
    
    def publish_action_sequence(self, action_sequence: ActionSequence):
        """
        Publish an action sequence to the appropriate topic.
        
        :param action_sequence: Action sequence to publish
        """
        # Convert action sequence to a string representation
        # In a real implementation, this would be a custom ROS message type
        sequence_data = {
            "id": action_sequence.id,
            "voice_command_id": action_sequence.voice_command_id,
            "description": action_sequence.description,
            "status": action_sequence.status,
            "steps": [
                {
                    "id": step.id,
                    "action_type": step.action_type.value if hasattr(step.action_type, 'value') else str(step.action_type),
                    "parameters": step.parameters,
                    "timeout": step.timeout,
                    "order": step.order
                }
                for step in action_sequence.sequence
            ]
        }
        
        msg = String()
        msg.data = json.dumps(sequence_data)
        
        self.action_sequence_publisher.publish(msg)
    
    def publish_error(self, error_msg: str):
        """
        Publish an error message.
        
        :param error_msg: Error message to publish
        """
        error_msg_ros = String()
        error_msg_ros.data = error_msg
        self.error_publisher.publish(error_msg_ros)


def main(args=None):
    """
    Main function to run the LLM Action Node.
    """
    rclpy.init(args=args)
    
    llm_action_node = LLMActionNode()
    
    try:
        rclpy.spin(llm_action_node)
    except KeyboardInterrupt:
        pass
    finally:
        llm_action_node.destroy_node()
        rclpy.shutdown()


# If you want to run this as a standalone script for testing
if __name__ == '__main__':
    main()