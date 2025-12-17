from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import uuid
from pydantic import BaseModel
from ..models.voice_command import VoiceCommand, VoiceCommandStatus
from ..models.action_sequence import ActionSequence
from ..services.whisper_service import WhisperService
from ..services.llm_service import LLMService
from ..config import settings
from ..services.intent_extraction import extract_intent
from ..validation.voice_command_validation import validate_voice_command
import base64
from datetime import datetime


# Initialize router
router = APIRouter()


class VoiceCommandResponse(BaseModel):
    voice_command_id: str
    transcribed_text: str
    intent: str
    parameters: dict
    action_sequence: Optional[ActionSequence] = None
    processing_time: float


@router.post("/", response_model=VoiceCommandResponse)
async def process_voice_command(
    audio: UploadFile = File(None),
    transcribed_text: str = Form(None),
    student_id: str = Form(None)
):
    """
    Submit a voice command for processing.
    Accepts either an audio file or pre-transcribed text.
    """
    start_time = datetime.now()
    
    # Validate input
    if not audio and not transcribed_text:
        raise HTTPException(
            status_code=400,
            detail="Either audio file or transcribed text must be provided"
        )
    
    # Generate a unique ID for this voice command
    voice_command_id = str(uuid.uuid4())
    
    # Transcribe audio if provided, otherwise use the transcribed text
    if audio:
        # Read the audio file
        audio_data = await audio.read()
        
        # Encode audio data to base64 for the model
        audio_data_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Initialize Whisper service
        from ..config import settings
        from ..services.whisper_service import WhisperConfig
        whisper_config = WhisperConfig(model_name=settings.whisper_model)
        whisper_service = WhisperService(whisper_config)

        # Transcribe the audio
        transcribed_text, confidence = await whisper_service.transcribe_with_confidence(audio_data)
        
        # Create a VoiceCommand object
        voice_command = VoiceCommand(
            id=voice_command_id,
            audio_data=audio_data_b64,
            transcribed_text=transcribed_text,
            intent="",  # Will be set after intent extraction
            parameters={},
            confidence=confidence,
            student_id=student_id
        )
    else:
        # Use the provided transcribed text
        voice_command = VoiceCommand(
            id=voice_command_id,
            transcribed_text=transcribed_text,
            intent="",  # Will be set after intent extraction
            parameters={},
            confidence=1.0,  # Assume 100% confidence if text is pre-transcribed
            student_id=student_id
        )
    
    # Validate the voice command
    validation_result = validate_voice_command(voice_command)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid voice command: {validation_result.errors}"
        )
    
    # Extract intent and parameters from the transcribed text
    intent, parameters = extract_intent(voice_command.transcribed_text)
    voice_command.intent = intent
    voice_command.parameters = parameters
    
    # Update status to processed
    voice_command.status = VoiceCommandStatus.PROCESSED
    
    # Generate action sequence using LLM if confidence is high enough
    action_sequence = None
    if voice_command.confidence >= settings.minimum_confidence_score:
        try:
            from ..config import settings
            from ..services.llm_service import LLMConfig
            llm_config = LLMConfig(
                model_name=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens
            )
            llm_service = LLMService(llm_config)

            # Generate an action sequence based on the intent and parameters
            action_steps = await llm_service.generate_action_sequence(
                intent=voice_command.intent,
                parameters=voice_command.parameters
            )

            if action_steps:
                # Create an action sequence
                action_sequence = ActionSequence(
                    id=str(uuid.uuid4()),
                    voice_command_id=voice_command.id,
                    sequence=action_steps,
                    description=f"Action sequence for: {voice_command.transcribed_text}",
                )

                # Update voice command status to indicate action generated
                voice_command.status = VoiceCommandStatus.ACTION_GENERATED
        except Exception as e:
            print(f"Error generating action sequence: {e}")
            # Don't raise an exception, just continue without an action sequence
            action_sequence = None
    
    # Calculate processing time
    processing_time = (datetime.now() - start_time).total_seconds()
    
    # Create and return the response
    response = VoiceCommandResponse(
        voice_command_id=voice_command.id,
        transcribed_text=voice_command.transcribed_text,
        intent=voice_command.intent,
        parameters=voice_command.parameters,
        action_sequence=action_sequence,
        processing_time=processing_time
    )
    
    return response


# Additional endpoint to get voice command by ID
@router.get("/{voice_command_id}", response_model=VoiceCommand)
async def get_voice_command(voice_command_id: str):
    """
    Get a specific voice command by its ID.
    In a real implementation, this would fetch from a database.
    For this example, we'll return a mock voice command.
    """
    # In a real implementation, fetch from database
    # For now, return a mock object
    mock_command = VoiceCommand(
        id=voice_command_id,
        transcribed_text="Mock voice command for demonstration",
        intent="mock_intent",
        parameters={"mock": True},
        confidence=0.9,
        status=VoiceCommandStatus.PROCESSED
    )
    return mock_command


# Additional endpoint to get all voice commands for a student
@router.get("/", response_model=list[VoiceCommand])
async def get_voice_commands(student_id: Optional[str] = None):
    """
    Get all voice commands, optionally filtered by student ID.
    In a real implementation, this would fetch from a database.
    For this example, we'll return mock voice commands.
    """
    # In a real implementation, fetch from database
    # For now, return mock objects
    mock_commands = [
        VoiceCommand(
            id=str(uuid.uuid4()),
            transcribed_text="Move forward 2 meters",
            intent="navigation",
            parameters={"distance": 2.0, "unit": "meters"},
            confidence=0.92,
            status=VoiceCommandStatus.ACTION_GENERATED
        )
    ]
    return mock_commands


# Example usage:
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router, prefix="/voice/commands", tags=["voice-commands"])
    
    # Run the API
    # uvicorn.run(app, host="0.0.0.0", port=8000)