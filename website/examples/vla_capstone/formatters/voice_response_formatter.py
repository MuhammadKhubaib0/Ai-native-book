"""
Formatter for voice command responses to ensure consistent output format.
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ..models.voice_command import VoiceCommand, VoiceCommandStatus
from ..models.action_sequence import ActionSequence


class VoiceCommandResponse(BaseModel):
    """
    Model for the voice command processing response.
    """
    voice_command_id: str
    transcribed_text: str
    intent: str
    parameters: Dict[str, Any]
    action_sequence: Optional[ActionSequence] = None
    processing_time: float
    timestamp: datetime = datetime.now()


class VoiceResponseFormatter:
    """
    Formatter for voice command responses.
    """
    
    @staticmethod
    def format_response(
        voice_command: VoiceCommand,
        action_sequence: Optional[ActionSequence] = None,
        processing_time: float = 0.0
    ) -> VoiceCommandResponse:
        """
        Format the response for a processed voice command.
        
        :param voice_command: The processed voice command
        :param action_sequence: The generated action sequence (optional)
        :param processing_time: Time taken to process the command
        :return: Formatted response
        """
        return VoiceCommandResponse(
            voice_command_id=voice_command.id,
            transcribed_text=voice_command.transcribed_text,
            intent=voice_command.intent,
            parameters=voice_command.parameters,
            action_sequence=action_sequence,
            processing_time=processing_time
        )
    
    @staticmethod
    def format_success_response(
        voice_command: VoiceCommand,
        action_sequence: Optional[ActionSequence] = None,
        processing_time: float = 0.0
    ) -> Dict[str, Any]:
        """
        Format a success response in dictionary format.
        
        :param voice_command: The processed voice command
        :param action_sequence: The generated action sequence (optional)
        :param processing_time: Time taken to process the command
        :return: Dictionary with success response
        """
        response = {
            "status": "success",
            "voice_command_id": voice_command.id,
            "transcribed_text": voice_command.transcribed_text,
            "intent": voice_command.intent,
            "parameters": voice_command.parameters,
            "confidence": voice_command.confidence,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
        if action_sequence:
            response["action_sequence"] = {
                "id": action_sequence.id,
                "description": action_sequence.description,
                "status": action_sequence.status.value if hasattr(action_sequence.status, 'value') else action_sequence.status,
                "steps": [
                    {
                        "id": step.id,
                        "action_type": step.action_type.value if hasattr(step.action_type, 'value') else step.action_type,
                        "parameters": step.parameters,
                        "timeout": step.timeout,
                        "order": step.order
                    }
                    for step in action_sequence.sequence
                ]
            }
        
        return response
    
    @staticmethod
    def format_error_response(error_message: str, error_code: str = "VOICE_PROCESSING_ERROR") -> Dict[str, Any]:
        """
        Format an error response in dictionary format.
        
        :param error_message: Error message to include
        :param error_code: Error code to identify the type of error
        :return: Dictionary with error response
        """
        return {
            "status": "error",
            "error_code": error_code,
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def format_voice_status_response(voice_command: VoiceCommand) -> Dict[str, Any]:
        """
        Format a response with just the status of a voice command.
        
        :param voice_command: The voice command to report status for
        :return: Dictionary with status information
        """
        return {
            "voice_command_id": voice_command.id,
            "status": voice_command.status.value if hasattr(voice_command.status, 'value') else voice_command.status,
            "intent": voice_command.intent,
            "timestamp": voice_command.timestamp.isoformat(),
            "confidence": voice_command.confidence
        }
    
    @staticmethod
    def format_for_api(response: VoiceCommandResponse) -> Dict[str, Any]:
        """
        Format response specifically for API output, converting Pydantic models to dicts.
        
        :param response: The response object to format
        :return: Dictionary ready for JSON serialization
        """
        result = {
            "voice_command_id": response.voice_command_id,
            "transcribed_text": response.transcribed_text,
            "intent": response.intent,
            "parameters": response.parameters,
            "processing_time": response.processing_time,
            "timestamp": response.timestamp.isoformat()
        }
        
        if response.action_sequence:
            result["action_sequence"] = {
                "id": response.action_sequence.id,
                "voice_command_id": response.action_sequence.voice_command_id,
                "description": response.action_sequence.description,
                "status": response.action_sequence.status.value if hasattr(response.action_sequence.status, 'value') else response.action_sequence.status,
                "steps": [
                    {
                        "id": step.id,
                        "action_sequence_id": step.action_sequence_id,
                        "action_type": step.action_type.value if hasattr(step.action_type, 'value') else step.action_type,
                        "parameters": step.parameters,
                        "timeout": step.timeout,
                        "order": step.order
                    }
                    for step in response.action_sequence.sequence
                ]
            }
        
        return result
    
    @staticmethod
    def format_for_logging(voice_command: VoiceCommand) -> str:
        """
        Format a voice command for logging purposes.
        
        :param voice_command: The voice command to format for logging
        :return: Formatted string for logging
        """
        return (
            f"VoiceCommand(id={voice_command.id}, "
            f"text='{voice_command.transcribed_text}', "
            f"intent='{voice_command.intent}', "
            f"confidence={voice_command.confidence:.2f}, "
            f"status={voice_command.status})"
        )


class CompactVoiceResponseFormatter(VoiceResponseFormatter):
    """
    A more compact formatter for voice command responses, with minimal data.
    """
    
    @staticmethod
    def format_response(
        voice_command: VoiceCommand,
        action_sequence: Optional[ActionSequence] = None,
        processing_time: float = 0.0
    ) -> Dict[str, Any]:
        """
        Format a compact response with essential information only.
        
        :param voice_command: The processed voice command
        :param action_sequence: The generated action sequence (optional)
        :param processing_time: Time taken to process the command
        :return: Compact response dictionary
        """
        response = {
            "id": voice_command.id,
            "intent": voice_command.intent,
            "params": voice_command.parameters,
            "conf": voice_command.confidence,
            "time": processing_time
        }
        
        # Only include action sequence if it exists and has steps
        if action_sequence and action_sequence.sequence:
            response["actions"] = [
                {
                    "type": step.action_type.value if hasattr(step.action_type, 'value') else step.action_type,
                    "params": step.parameters,
                    "timeout": step.timeout
                }
                for step in action_sequence.sequence
            ]
        
        return response


# Example usage:
if __name__ == "__main__":
    from ..models.voice_command import VoiceCommand
    from ..models.action_sequence import ActionSequence, ActionSequenceStatus
    from ..models.action_step import ActionStep, ActionType
    import uuid
    
    # Create a sample voice command
    voice_cmd = VoiceCommand(
        id=str(uuid.uuid4()),
        transcribed_text="Move forward 2 meters",
        intent="navigation",
        parameters={"distance": 2.0, "unit": "meters"},
        confidence=0.92,
        status=VoiceCommandStatus.PROCESSED
    )
    
    # Create a sample action sequence
    action_step = ActionStep(
        id=str(uuid.uuid4()),
        action_sequence_id=str(uuid.uuid4()),
        action_type=ActionType.NAVIGATION,
        parameters={"x": 2.0, "y": 0.0, "theta": 0.0},
        timeout=10,
        order=0
    )
    
    action_seq = ActionSequence(
        id=str(uuid.uuid4()),
        voice_command_id=voice_cmd.id,
        sequence=[action_step],
        description="Move robot forward by 2 meters",
        status=ActionSequenceStatus.PENDING
    )
    
    # Format using the standard formatter
    formatter = VoiceResponseFormatter()
    formatted_response = formatter.format_response(voice_cmd, action_seq, 1.23)
    print("Standard formatted response:")
    print(json.dumps(formatter.format_for_api(formatted_response), indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Format using the compact formatter
    compact_formatter = CompactVoiceResponseFormatter()
    compact_response = compact_formatter.format_response(voice_cmd, action_seq, 1.23)
    print("Compact formatted response:")
    print(json.dumps(compact_response, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Format success response
    success_response = formatter.format_success_response(voice_cmd, action_seq, 1.23)
    print("Success response:")
    print(json.dumps(success_response, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Format error response
    error_response = formatter.format_error_response("Confidence too low", "LOW_CONFIDENCE")
    print("Error response:")
    print(json.dumps(error_response, indent=2))