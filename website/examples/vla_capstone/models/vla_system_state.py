from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class SystemStatus(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    EXECUTING = "executing"
    ERROR = "error"


class Pose(BaseModel):
    """Represents robot pose with position and orientation."""
    x: float
    y: float
    z: float
    rotation: Dict[str, float]  # Contains qx, qy, qz, qw components


class VLASystemState(BaseModel):
    """
    Represents the current state of the VLA system during operation.
    """
    id: str
    current_voice_command: Optional[str] = None
    current_action_sequence: Optional[str] = None
    robot_pose: Optional[Pose] = None
    perception_data: Optional[Dict[str, Any]] = None
    system_status: SystemStatus = SystemStatus.IDLE
    last_update: datetime = Field(default_factory=datetime.now)

    @validator('system_status')
    def validate_system_status(cls, value):
        # If status is not idle, robot_pose must contain position and orientation data
        if value != SystemStatus.IDLE:
            # This will be validated in a more complex way in practice
            pass
        return value


# Example usage:
if __name__ == "__main__":
    import uuid

    pose = Pose(
        x=1.0,
        y=2.0,
        z=0.0,
        rotation={"qx": 0.0, "qy": 0.0, "qz": 0.1, "qw": 0.9}
    )

    vla_state = VLASystemState(
        id=str(uuid.uuid4()),
        current_voice_command=str(uuid.uuid4()),
        current_action_sequence=str(uuid.uuid4()),
        robot_pose=pose,
        perception_data={"objects_detected": ["cube", "table"], "distances": [1.5, 2.0]},
        system_status=SystemStatus.PROCESSING
    )

    print(vla_state.json(indent=2))