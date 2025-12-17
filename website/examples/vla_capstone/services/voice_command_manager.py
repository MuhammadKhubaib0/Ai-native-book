"""
Service for managing the state of voice commands during processing.
"""
import asyncio
import uuid
from typing import Dict, Optional, List
from datetime import datetime
from ..models.voice_command import VoiceCommand, VoiceCommandStatus
from ..models.action_sequence import ActionSequence


class VoiceCommandManager:
    """
    Service for managing the state of voice commands throughout their lifecycle.
    """
    
    def __init__(self):
        # In-memory storage for voice commands during this session
        # In a production system, you'd use a database
        self._voice_commands: Dict[str, VoiceCommand] = {}
        self._action_sequences: Dict[str, ActionSequence] = {}
    
    async def create_voice_command(self, transcribed_text: str, confidence: float = 1.0, 
                                   student_id: Optional[str] = None) -> VoiceCommand:
        """
        Create a new voice command with initial state.
        
        :param transcribed_text: The transcribed voice command text
        :param confidence: Confidence in the transcription (0-1)
        :param student_id: ID of the student issuing the command
        :return: Created VoiceCommand object
        """
        voice_command_id = str(uuid.uuid4())
        
        voice_command = VoiceCommand(
            id=voice_command_id,
            transcribed_text=transcribed_text,
            intent="",  # Will be set later
            parameters={},  # Will be set later
            confidence=confidence,
            timestamp=datetime.now(),
            status=VoiceCommandStatus.PENDING,
            student_id=student_id
        )
        
        self._voice_commands[voice_command_id] = voice_command
        
        return voice_command
    
    async def update_voice_command_status(self, command_id: str, status: VoiceCommandStatus) -> bool:
        """
        Update the status of a voice command.
        
        :param command_id: ID of the voice command
        :param status: New status for the command
        :return: True if update was successful, False otherwise
        """
        if command_id not in self._voice_commands:
            return False
        
        command = self._voice_commands[command_id]
        command.status = status
        
        return True
    
    async def get_voice_command(self, command_id: str) -> Optional[VoiceCommand]:
        """
        Retrieve a voice command by ID.
        
        :param command_id: ID of the voice command
        :return: VoiceCommand object if found, None otherwise
        """
        return self._voice_commands.get(command_id)
    
    async def set_voice_command_intent(self, command_id: str, intent: str, parameters: dict) -> bool:
        """
        Set the intent and parameters for a voice command.
        
        :param command_id: ID of the voice command
        :param intent: Extracted intent from the command
        :param parameters: Extracted parameters from the command
        :return: True if update was successful, False otherwise
        """
        if command_id not in self._voice_commands:
            return False
        
        command = self._voice_commands[command_id]
        command.intent = intent
        command.parameters = parameters
        
        return True
    
    async def get_voice_commands_by_student(self, student_id: str) -> List[VoiceCommand]:
        """
        Retrieve all voice commands for a specific student.
        
        :param student_id: ID of the student
        :return: List of VoiceCommand objects for the student
        """
        return [
            cmd for cmd in self._voice_commands.values()
            if cmd.student_id == student_id
        ]
    
    async def get_pending_commands(self) -> List[VoiceCommand]:
        """
        Retrieve all voice commands with status PENDING.
        
        :return: List of pending VoiceCommand objects
        """
        return [
            cmd for cmd in self._voice_commands.values()
            if cmd.status == VoiceCommandStatus.PENDING
        ]
    
    async def create_action_sequence(self, voice_command_id: str, action_steps: List, 
                                     description: str) -> Optional[ActionSequence]:
        """
        Create an action sequence associated with a voice command.
        
        :param voice_command_id: ID of the associated voice command
        :param action_steps: List of action steps to execute
        :param description: Description of the action sequence
        :return: Created ActionSequence object if successful, None otherwise
        """
        if voice_command_id not in self._voice_commands:
            return None
        
        sequence_id = str(uuid.uuid4())
        
        action_sequence = ActionSequence(
            id=sequence_id,
            voice_command_id=voice_command_id,
            sequence=action_steps,
            description=description,
        )
        
        self._action_sequences[sequence_id] = action_sequence
        
        # Update the voice command status to indicate action generation
        voice_command = self._voice_commands[voice_command_id]
        voice_command.status = VoiceCommandStatus.ACTION_GENERATED
        
        return action_sequence
    
    async def get_action_sequence(self, sequence_id: str) -> Optional[ActionSequence]:
        """
        Retrieve an action sequence by ID.
        
        :param sequence_id: ID of the action sequence
        :return: ActionSequence object if found, None otherwise
        """
        return self._action_sequences.get(sequence_id)
    
    async def get_action_sequence_by_voice_command(self, voice_command_id: str) -> Optional[ActionSequence]:
        """
        Retrieve an action sequence by its associated voice command ID.
        
        :param voice_command_id: ID of the associated voice command
        :return: ActionSequence object if found, None otherwise
        """
        for sequence in self._action_sequences.values():
            if sequence.voice_command_id == voice_command_id:
                return sequence
        return None
    
    async def update_action_sequence_status(self, sequence_id: str, status) -> bool:
        """
        Update the status of an action sequence.
        
        :param sequence_id: ID of the action sequence
        :param status: New status for the sequence
        :return: True if update was successful, False otherwise
        """
        if sequence_id not in self._action_sequences:
            return False
        
        sequence = self._action_sequences[sequence_id]
        # Note: Using string here because we can't import ActionSequenceStatus due to circular import
        # In a real implementation, we'd handle this differently
        sequence.status = status
        
        return True
    
    async def mark_command_as_processed(self, command_id: str) -> bool:
        """
        Mark a voice command as processed.
        
        :param command_id: ID of the voice command
        :return: True if update was successful, False otherwise
        """
        if command_id not in self._voice_commands:
            return False
        
        command = self._voice_commands[command_id]
        command.status = VoiceCommandStatus.PROCESSED
        
        return True


# Example usage with a simulated state store
class StateStore:
    """
    A simple state store that maintains voice command state across the system.
    """
    
    def __init__(self):
        self.voice_command_manager = VoiceCommandManager()
        self.active_commands = {}
        self.command_history = []
    
    async def process_new_command(self, transcribed_text: str, confidence: float = 1.0) -> str:
        """
        Process a new command and return the command ID.
        
        :param transcribed_text: The transcribed command text
        :param confidence: Confidence in the transcription
        :return: ID of the created command
        """
        command = await self.voice_command_manager.create_voice_command(
            transcribed_text, confidence
        )
        
        # Add to active commands
        self.active_commands[command.id] = command
        
        return command.id
    
    async def finalize_command(self, command_id: str) -> bool:
        """
        Finalize a command after processing is complete.
        
        :param command_id: ID of the command to finalize
        :return: True if successful, False otherwise
        """
        command = await self.voice_command_manager.get_voice_command(command_id)
        if not command:
            return False
        
        # Move from active to history
        if command_id in self.active_commands:
            del self.active_commands[command_id]
        
        self.command_history.append(command)
        
        return True


# Example usage:
if __name__ == "__main__":
    import asyncio
    
    async def example():
        manager = VoiceCommandManager()
        
        # Create a new voice command
        command = await manager.create_voice_command(
            "Move forward 2 meters",
            confidence=0.91
        )
        print(f"Created command: {command.id}")
        
        # Update its intent and parameters
        await manager.set_voice_command_intent(
            command.id,
            "navigation",
            {"direction": "forward", "distance": 2.0, "unit": "meters"}
        )
        
        # Mark as processed
        await manager.mark_command_as_processed(command.id)
        
        # Retrieve the command
        retrieved = await manager.get_voice_command(command.id)
        print(f"Retrieved command: {retrieved.transcribed_text}")
        print(f"Intent: {retrieved.intent}")
        print(f"Parameters: {retrieved.parameters}")
        print(f"Status: {retrieved.status}")
    
    # Run the example
    # asyncio.run(example())