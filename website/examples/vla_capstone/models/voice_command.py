from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class VoiceCommandStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    ACTION_GENERATED = "action_generated"


class VoiceCommand(BaseModel):
    """
    Represents a voice command captured from the user and processed by the system.
    """
    id: str
    audio_data: Optional[bytes] = None  # Raw audio data in base64 encoded string
    transcribed_text: str = Field(..., min_length=1)
    intent: str = Field(..., min_length=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    status: VoiceCommandStatus = VoiceCommandStatus.PENDING
    student_id: Optional[str] = None

    @validator('confidence')
    def validate_confidence(cls, value):
        if not 0 <= value <= 1:
            raise ValueError('Confidence must be between 0 and 1')
        return value

    @validator('transcribed_text')
    def validate_transcribed_text(cls, value):
        if not value.strip():
            raise ValueError('Transcribed text must not be empty')
        return value

    class Config:
        json_encoders = {
            bytes: lambda v: v.decode('utf-8') if isinstance(v, bytes) else v
        }


# Example usage:
if __name__ == "__main__":
    import uuid
    
    voice_cmd = VoiceCommand(
        id=str(uuid.uuid4()),
        transcribed_text="Move forward 2 meters",
        intent="navigation",
        parameters={"distance": 2.0, "unit": "meters"},
        confidence=0.92
    )
    
    print(voice_cmd.json(indent=2))