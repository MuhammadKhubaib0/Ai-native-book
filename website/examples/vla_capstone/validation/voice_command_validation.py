from pydantic import BaseModel
from typing import List
from ..models.voice_command import VoiceCommand, VoiceCommandStatus
from ..models.action_sequence import ActionSequence


class ValidationResult(BaseModel):
    """Result of validation process."""
    is_valid: bool
    errors: List[str] = []


def validate_voice_command(voice_command: VoiceCommand) -> ValidationResult:
    """
    Validate a VoiceCommand object.
    
    :param voice_command: The VoiceCommand to validate
    :return: ValidationResult indicating if the command is valid
    """
    errors = []
    
    # Validate transcribed text
    if not voice_command.transcribed_text or len(voice_command.transcribed_text.strip()) == 0:
        errors.append("Transcribed text cannot be empty")
    
    # Validate confidence
    if not (0.0 <= voice_command.confidence <= 1.0):
        errors.append("Confidence must be between 0.0 and 1.0")
    
    # Validate intent
    if not voice_command.intent or len(voice_command.intent.strip()) == 0:
        errors.append("Intent cannot be empty")
    
    # Check if confidence meets minimum threshold
    from ..config import settings
    if voice_command.confidence < settings.minimum_confidence_score:
        errors.append(f"Confidence {voice_command.confidence} is below minimum threshold {settings.minimum_confidence_score}")
    
    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def validate_action_sequence(action_sequence: ActionSequence) -> ValidationResult:
    """
    Validate an ActionSequence object.
    
    :param action_sequence: The ActionSequence to validate
    :return: ValidationResult indicating if the sequence is valid
    """
    errors = []
    
    # Check if it has steps
    if not action_sequence.sequence or len(action_sequence.sequence) == 0:
        errors.append("Action sequence must contain at least one action step")
    
    # Check if each step is properly formed
    for i, step in enumerate(action_sequence.sequence):
        if not step.action_type:
            errors.append(f"Action step {i} must have an action_type")
        if step.parameters is None:
            errors.append(f"Action step {i} must have parameters")
        if step.timeout <= 0:
            errors.append(f"Action step {i} timeout must be positive")
    
    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def validate_voice_command_for_execution(voice_command: VoiceCommand) -> ValidationResult:
    """
    Validate a voice command specifically for execution.
    
    :param voice_command: The VoiceCommand to validate for execution
    :return: ValidationResult indicating if the command is valid for execution
    """
    # First run general validation
    result = validate_voice_command(voice_command)
    if not result.is_valid:
        return result
    
    errors = result.errors.copy()
    
    # Additional checks specific for execution
    if voice_command.status not in [VoiceCommandStatus.PROCESSED, VoiceCommandStatus.ACTION_GENERATED]:
        errors.append(f"Command status {voice_command.status} is not valid for execution")
    
    # Check if required parameters for the intent are present
    if voice_command.intent == "navigation":
        required_params = {"x", "y"}
        if not required_params.issubset(voice_command.parameters.keys()):
            errors.append(f"Navigation command missing required parameters: {required_params - set(voice_command.parameters.keys())}")
    
    elif voice_command.intent == "manipulation":
        if "object" not in voice_command.parameters:
            errors.append("Manipulation command missing required 'object' parameter")
    
    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def validate_action_step_compatibility(action_sequence: ActionSequence, robot_capabilities: List[str]) -> ValidationResult:
    """
    Validate if the action sequence is compatible with robot capabilities.
    
    :param action_sequence: The ActionSequence to validate
    :param robot_capabilities: List of capabilities the robot supports
    :return: ValidationResult indicating compatibility
    """
    errors = []
    
    # Check if all action types in the sequence are supported by the robot
    for i, step in enumerate(action_sequence.sequence):
        action_type = step.action_type.value if hasattr(step.action_type, 'value') else step.action_type
        if action_type not in robot_capabilities:
            errors.append(f"Action step {i} ({action_type}) is not supported by the robot")
    
    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


# Example usage:
if __name__ == "__main__":
    from ..models.voice_command import VoiceCommand
    from ..models.action_sequence import ActionSequence, ActionSequenceStatus
    from ..models.action_step import ActionStep, ActionType
    import uuid
    
    # Test valid voice command
    valid_command = VoiceCommand(
        id=str(uuid.uuid4()),
        transcribed_text="Move forward 2 meters",
        intent="navigation",
        parameters={"distance": 2.0, "unit": "meters"},
        confidence=0.92
    )
    
    result = validate_voice_command(valid_command)
    print(f"Valid command validation: {result.is_valid}, Errors: {result.errors}")
    
    # Test invalid voice command
    invalid_command = VoiceCommand(
        id=str(uuid.uuid4()),
        transcribed_text="",
        intent="",
        parameters={},
        confidence=1.5  # Invalid confidence
    )
    
    result = validate_voice_command(invalid_command)
    print(f"Invalid command validation: {result.is_valid}, Errors: {result.errors}")
    
    # Test action sequence validation
    action_step = ActionStep(
        id=str(uuid.uuid4()),
        action_sequence_id=str(uuid.uuid4()),
        action_type=ActionType.NAVIGATION,
        parameters={"x": 1.0, "y": 2.0, "theta": 0.0},
        timeout=10,
        order=0
    )
    
    action_seq = ActionSequence(
        id=str(uuid.uuid4()),
        voice_command_id=str(uuid.uuid4()),
        sequence=[action_step],
        description="Move robot to specified coordinates",
        status=ActionSequenceStatus.PENDING
    )
    
    result = validate_action_sequence(action_seq)
    print(f"Action sequence validation: {result.is_valid}, Errors: {result.errors}")
    
    # Test execution validation
    valid_command.status = VoiceCommandStatus.PROCESSED
    valid_command.parameters = {"x": 1.0, "y": 2.0}
    result = validate_voice_command_for_execution(valid_command)
    print(f"Execution validation: {result.is_valid}, Errors: {result.errors}")