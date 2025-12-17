"""
ROS 2 node for handling voice commands in the VLA system.
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import AudioData
from .msg import VoiceCommand, ActionSequence, VoiceCommandResponse
from ..services.whisper_processor import WhisperAudioProcessor
from ..services.intent_extraction import extract_intent
from ..services.voice_command_manager import VoiceCommandManager
from ..validation.voice_command_validation import validate_voice_command_for_execution
from ..formatters.voice_response_formatter import VoiceResponseFormatter
import base64
import asyncio
from threading import Thread


class VoiceCommandNode(Node):
    """
    ROS 2 node that processes voice commands and generates action sequences.
    """
    
    def __init__(self):
        super().__init__('voice_command_node')
        
        # Initialize services
        self.whisper_processor = WhisperAudioProcessor()
        self.command_manager = VoiceCommandManager()
        self.response_formatter = VoiceResponseFormatter()
        
        # Create subscribers
        self.audio_subscription = self.create_subscription(
            AudioData,
            'audio_input',
            self.audio_callback,
            10
        )
        
        self.text_subscription = self.create_subscription(
            String,
            'text_command',
            self.text_callback,
            10
        )
        
        # Create publishers
        self.response_publisher = self.create_publisher(
            VoiceCommandResponse,
            'voice_command_response',
            10
        )
        
        self.action_sequence_publisher = self.create_publisher(
            ActionSequence,
            'action_sequence',
            10
        )
        
        # Timer for asynchronous processing
        self.processing_timer = self.create_timer(0.1, self.process_pending_commands)
        
        self.get_logger().info('Voice Command Node started')
    
    def audio_callback(self, msg: AudioData):
        """
        Handle incoming audio data.
        
        :param msg: AudioData message containing raw audio
        """
        self.get_logger().info('Received audio data')
        
        # Process audio in a separate thread to avoid blocking
        audio_thread = Thread(target=self.process_audio_data, args=(msg,))
        audio_thread.start()
    
    def text_callback(self, msg: String):
        """
        Handle incoming text commands (for testing purposes).
        
        :param msg: String message containing transcribed text
        """
        self.get_logger().info(f'Received text command: {msg.data}')
        
        # Process text command
        command_thread = Thread(target=self.process_text_command, args=(msg.data,))
        command_thread.start()
    
    def process_audio_data(self, audio_msg: AudioData):
        """
        Process audio data through Whisper and generate action sequence.
        
        :param audio_msg: AudioData message containing raw audio
        """
        try:
            # Convert audio data to bytes
            audio_bytes = bytes(audio_msg.data)
            
            # Process audio with Whisper
            # Note: This requires running the async function from a thread
            # In practice, you'd need to handle this differently
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            transcribed_text, confidence = loop.run_until_complete(
                self.whisper_processor.process_audio_bytes(audio_bytes)
            )
            
            # Create voice command
            voice_command = loop.run_until_complete(
                self.command_manager.create_voice_command(transcribed_text, confidence)
            )
            
            # Extract intent and parameters
            intent, parameters = extract_intent(transcribed_text)
            loop.run_until_complete(
                self.command_manager.set_voice_command_intent(voice_command.id, intent, parameters)
            )
            
            # Validate the command
            validation_result = validate_voice_command_for_execution(voice_command)
            
            if validation_result.is_valid:
                # Mark as processed
                loop.run_until_complete(
                    self.command_manager.mark_command_as_processed(voice_command.id)
                )
                
                # Generate action sequence
                # This part would require integration with LLM service
                # For now, we'll create a placeholder action sequence
                from ..models.action_step import ActionStep, ActionType
                import uuid
                
                action_steps = [
                    ActionStep(
                        id=str(uuid.uuid4()),
                        action_sequence_id="",  # Will be set when creating sequence
                        action_type=ActionType.NAVIGATION,
                        parameters=parameters,
                        timeout=10,
                        order=0
                    )
                ]
                
                action_sequence = loop.run_until_complete(
                    self.command_manager.create_action_sequence(
                        voice_command.id,
                        action_steps,
                        f"Action sequence for: {transcribed_text}"
                    )
                )
                
                if action_sequence:
                    # Publish action sequence
                    self.publish_action_sequence(action_sequence)
                
                # Format and publish response
                response = self.response_formatter.format_response(
                    voice_command,
                    action_sequence,
                    processing_time=0.5  # Placeholder
                )
                
                self.publish_voice_response(response)
                
            else:
                # Publish error response
                error_response = self.response_formatter.format_error_response(
                    f"Invalid command: {', '.join(validation_result.errors)}"
                )
                
                self.get_logger().error(f'Invalid command: {error_response}')
            
            loop.close()
            
        except Exception as e:
            self.get_logger().error(f'Error processing audio: {str(e)}')
    
    def process_text_command(self, text: str):
        """
        Process a text command directly (for testing purposes).
        
        :param text: Text command to process
        """
        try:
            # Create voice command with high confidence since it's already transcribed
            import asyncio
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            voice_command = loop.run_until_complete(
                self.command_manager.create_voice_command(text, confidence=1.0)
            )
            
            # Extract intent and parameters
            intent, parameters = extract_intent(text)
            loop.run_until_complete(
                self.command_manager.set_voice_command_intent(voice_command.id, intent, parameters)
            )
            
            # Validate the command
            from ..validation.voice_command_validation import validate_voice_command_for_execution
            validation_result = validate_voice_command_for_execution(voice_command)
            
            if validation_result.is_valid:
                # Mark as processed
                loop.run_until_complete(
                    self.command_manager.mark_command_as_processed(voice_command.id)
                )
                
                # Generate action sequence
                # This part would require integration with LLM service
                # For now, we'll create a placeholder action sequence
                from ..models.action_step import ActionStep, ActionType
                import uuid
                
                action_steps = [
                    ActionStep(
                        id=str(uuid.uuid4()),
                        action_sequence_id="",  # Will be set when creating sequence
                        action_type=ActionType.NAVIGATION,
                        parameters=parameters,
                        timeout=10,
                        order=0
                    )
                ]
                
                action_sequence = loop.run_until_complete(
                    self.command_manager.create_action_sequence(
                        voice_command.id,
                        action_steps,
                        f"Action sequence for: {text}"
                    )
                )
                
                if action_sequence:
                    # Publish action sequence
                    self.publish_action_sequence(action_sequence)
                
                # Format and publish response
                response = self.response_formatter.format_response(
                    voice_command,
                    action_sequence,
                    processing_time=0.2  # Processing time for text is lower
                )
                
                self.publish_voice_response(response)
                
            else:
                # Publish error response
                error_response = self.response_formatter.format_error_response(
                    f"Invalid command: {', '.join(validation_result.errors)}"
                )
                
                self.get_logger().error(f'Invalid command: {error_response}')
            
            loop.close()
            
        except Exception as e:
            self.get_logger().error(f'Error processing text command: {str(e)}')
    
    def process_pending_commands(self):
        """
        Process any pending commands in the queue.
        This runs periodically via timer.
        """
        # In a real implementation, this would process commands that are queued for execution
        # For now, we'll just log that it's running
        pass
    
    def publish_voice_response(self, response):
        """
        Publish a voice command response to the appropriate topic.
        
        :param response: Formatted response to publish
        """
        # Convert the response to the ROS 2 message format
        response_msg = VoiceCommandResponse()
        response_msg.voice_command_id = response.voice_command_id
        response_msg.transcribed_text = response.transcribed_text
        response_msg.intent = response.intent
        response_msg.parameters = str(response.parameters)  # Convert dict to string for ROS msg
        response_msg.processing_time = response.processing_time
        response_msg.timestamp = self.get_clock().now().to_msg()
        
        # Publish the message
        self.response_publisher.publish(response_msg)
        self.get_logger().info(f'Published voice command response: {response.intent}')
    
    def publish_action_sequence(self, action_sequence):
        """
        Publish an action sequence to the appropriate topic.
        
        :param action_sequence: Action sequence to publish
        """
        # Convert the action sequence to the ROS 2 message format
        sequence_msg = ActionSequence()
        sequence_msg.id = action_sequence.id
        sequence_msg.voice_command_id = action_sequence.voice_command_id
        sequence_msg.description = action_sequence.description
        sequence_msg.status = action_sequence.status
        
        # Convert each action step to the message format
        # This assumes there is a corresponding ROS 2 message type for ActionStep
        # In practice, you would need to define this message type
        for step in action_sequence.sequence:
            # Create action step message and populate it
            # This assumes there is an ActionStep message defined in your ROS 2 package
            pass
        
        # Publish the message
        self.action_sequence_publisher.publish(sequence_msg)
        self.get_logger().info(f'Published action sequence: {action_sequence.id}')


def main(args=None):
    """
    Main function to run the Voice Command Node.
    """
    rclpy.init(args=args)
    
    voice_command_node = VoiceCommandNode()
    
    try:
        rclpy.spin(voice_command_node)
    except KeyboardInterrupt:
        pass
    finally:
        voice_command_node.destroy_node()
        rclpy.shutdown()


# If you want to run this as a standalone script for testing
if __name__ == '__main__':
    main()