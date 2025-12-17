from pydantic import BaseModel, Field
from typing import Dict, Any
from enum import Enum


class ActionType(str, Enum):
    NAVIGATION = "navigation"
    MANIPULATION = "manipulation"
    PERCEPTION = "perception"
    OTHER = "other"


class ActionStep(BaseModel):
    """
    Represents a single step within an action sequence.
    """
    id: str
    action_sequence_id: str
    action_type: ActionType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timeout: int = Field(..., gt=0)  # Must be positive
    order: int

    class Config:
        use_enum_values = True  # Store enum values instead of enum objects


# Example usage:
if __name__ == "__main__":
    import uuid

    action_step = ActionStep(
        id=str(uuid.uuid4()),
        action_sequence_id=str(uuid.uuid4()),
        action_type=ActionType.NAVIGATION,
        parameters={"x": 1.0, "y": 2.0, "theta": 0.0},
        timeout=10,
        order=0
    )

    print(action_step.json(indent=2))