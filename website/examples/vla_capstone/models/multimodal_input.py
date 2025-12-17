from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
from datetime import datetime


class MultimodalInput(BaseModel):
    """
    Represents combined input from multiple sensors (vision, voice, etc.).
    """
    id: str
    voice_input_id: Optional[str] = None
    visual_data: Optional[Dict[str, Any]] = None  # e.g., image, depth data
    sensor_data: Optional[Dict[str, Any]] = None  # other sensor inputs
    fusion_result: Optional[Dict[str, Any]] = None  # combined result of multimodal processing
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)

    @validator('confidence')
    def validate_confidence(cls, value):
        if not 0 <= value <= 1:
            raise ValueError('Confidence must be between 0 and 1')
        return value

    @validator('voice_input_id', 'visual_data', pre=True)
    def validate_input_sources(cls, value, values):
        # At least one of voice_input_id or visual_data must be present
        if not value and 'visual_data' not in values and not values.get('visual_data'):
            raise ValueError('Must have at least one of voice_input_id or visual_data')
        return value

    class Config:
        json_encoders = {
            bytes: lambda v: v.decode('utf-8') if isinstance(v, bytes) else v
        }


# Example usage:
if __name__ == "__main__":
    import uuid

    multimodal_input = MultimodalInput(
        id=str(uuid.uuid4()),
        voice_input_id=str(uuid.uuid4()),
        visual_data={"image": "image_data", "depth": "depth_data"},
        sensor_data={"imu": "imu_data", "lidar": "lidar_data"},
        fusion_result={"object_detected": "red_cube", "location": {"x": 1.0, "y": 2.0}},
        confidence=0.89
    )

    print(multimodal_input.json(indent=2))