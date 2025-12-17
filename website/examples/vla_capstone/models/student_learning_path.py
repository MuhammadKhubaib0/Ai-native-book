from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional
from datetime import datetime


class StudentLearningPath(BaseModel):
    """
    Tracks the student's progress through the VLA module.
    """
    id: str
    student_id: str = Field(..., min_length=1)
    module_progress: Dict[str, float] = Field(default_factory=dict)  # chapter_name: percentage
    completed_chapters: List[str] = Field(default_factory=list)
    assessment_scores: List[float] = Field(default_factory=list)  # Scores between 0-100
    start_date: datetime = Field(default_factory=datetime.now)
    completion_date: Optional[datetime] = None

    @validator('student_id')
    def validate_student_id(cls, value):
        if not value.strip():
            raise ValueError('Student ID must not be empty')
        return value

    @validator('module_progress')
    def validate_module_progress(cls, value):
        for chapter, progress in value.items():
            if not 0 <= progress <= 100:
                raise ValueError(f'Progress for {chapter} must be between 0 and 100')
        return value

    @validator('assessment_scores')
    def validate_assessment_scores(cls, value):
        for score in value:
            if not 0 <= score <= 100:
                raise ValueError(f'Assessment score must be between 0 and 100, got {score}')
        return value


# Example usage:
if __name__ == "__main__":
    import uuid

    student_path = StudentLearningPath(
        id=str(uuid.uuid4()),
        student_id="student_123",
        module_progress={
            "voice_to_action": 75.0,
            "llm_planning": 50.0,
            "multimodal_fusion": 25.0
        },
        completed_chapters=["introduction"],
        assessment_scores=[85.5, 92.0]
    )

    print(student_path.json(indent=2))