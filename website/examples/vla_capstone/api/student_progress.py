from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import uuid
from pydantic import BaseModel
from datetime import datetime
from ..models.student_learning_path import StudentLearningPath
from ..models.action_sequence import ActionSequence
from ..models.vla_system_state import VLASystemState
from ..config import settings


# Initialize router
router = APIRouter()


class StudentProgressRequest(BaseModel):
    """Request model for updating student progress."""
    student_id: str
    module_name: str
    chapter_name: str
    progress_percentage: float
    activity_type: str  # e.g., "exercise", "quiz", "simulation", "project"
    score: Optional[float] = None
    completion_time: Optional[float] = None
    additional_data: Optional[Dict[str, Any]] = {}


class StudentProgressResponse(BaseModel):
    """Response model for student progress."""
    student_id: str
    module_name: str
    chapter_name: str
    progress_percentage: float
    status: str
    message: str
    timestamp: datetime


class StudentProgressQuery(BaseModel):
    """Query model for retrieving student progress."""
    student_id: str
    module_name: Optional[str] = None
    chapter_name: Optional[str] = None


class StudentProgressListResponse(BaseModel):
    """Response model for list of student progress records."""
    student_id: str
    progress_records: List[Dict[str, Any]]
    total_modules: int
    total_completed: int
    overall_progress: float
    timestamp: datetime


# Global student progress storage (in a real implementation, this would use a database)
student_progress_storage = {}


@router.post("/", response_model=StudentProgressResponse)
async def update_student_progress(request: StudentProgressRequest):
    """
    Update the progress of a student for a specific module/chapter.
    """
    try:
        student_id = request.student_id
        module_name = request.module_name
        chapter_name = request.chapter_name
        progress = request.progress_percentage
        
        # Validate progress percentage
        if not 0 <= progress <= 100:
            raise HTTPException(
                status_code=400,
                detail="Progress percentage must be between 0 and 100"
            )
        
        # Initialize or get existing student record
        if student_id not in student_progress_storage:
            student_progress_storage[student_id] = StudentLearningPath(
                id=str(uuid.uuid4()),
                student_id=student_id,
                module_progress={},
                completed_chapters=[],
                assessment_scores=[],
                start_date=datetime.now()
            )
        
        student_record = student_progress_storage[student_id]
        
        # Update module progress
        module_key = f"{module_name}:{chapter_name}"
        student_record.module_progress[module_key] = progress
        
        # If progress is 100%, add to completed chapters
        if progress >= 100.0:
            completed_key = f"{module_name}:{chapter_name}"
            if completed_key not in student_record.completed_chapters:
                student_record.completed_chapters.append(completed_key)
        
        # Record score if provided
        if request.score is not None:
            student_record.assessment_scores.append(request.score)
        
        # Update completion date if all modules are completed
        if progress >= 100.0:
            # In a real implementation, check if all required modules are completed
            pass
        
        response = StudentProgressResponse(
            student_id=student_id,
            module_name=module_name,
            chapter_name=chapter_name,
            progress_percentage=progress,
            status="success",
            message=f"Progress updated for student {student_id}",
            timestamp=datetime.now()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating student progress: {str(e)}"
        )


@router.get("/{student_id}", response_model=StudentProgressListResponse)
async def get_student_progress(student_id: str, module_name: Optional[str] = None, chapter_name: Optional[str] = None):
    """
    Get the progress of a student across modules/chapters.
    """
    if student_id not in student_progress_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        )
    
    student_record = student_progress_storage[student_id]
    
    # Filter records if module or chapter specified
    filtered_progress = {}
    if module_name and chapter_name:
        key = f"{module_name}:{chapter_name}"
        if key in student_record.module_progress:
            filtered_progress[key] = student_record.module_progress[key]
    elif module_name:
        for key, progress in student_record.module_progress.items():
            if key.startswith(module_name + ":"):
                filtered_progress[key] = progress
    else:
        filtered_progress = student_record.module_progress
    
    # Calculate overall progress
    total_modules = len(filtered_progress)
    total_completed = 0
    progress_sum = 0.0
    
    for progress in filtered_progress.values():
        progress_sum += progress
        if progress >= 100.0:
            total_completed += 1
    
    overall_progress = progress_sum / total_modules if total_modules > 0 else 0.0
    
    progress_records = []
    for module_chapter, progress in filtered_progress.items():
        module, chapter = module_chapter.split(":", 1)
        progress_records.append({
            "module_name": module,
            "chapter_name": chapter,
            "progress_percentage": progress
        })
    
    response = StudentProgressListResponse(
        student_id=student_id,
        progress_records=progress_records,
        total_modules=total_modules,
        total_completed=total_completed,
        overall_progress=overall_progress,
        timestamp=datetime.now()
    )
    
    return response


@router.get("/{student_id}/summary", response_model=Dict[str, Any])
async def get_student_progress_summary(student_id: str):
    """
    Get a summary of the student's progress across all modules.
    """
    if student_id not in student_progress_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        )
    
    student_record = student_progress_storage[student_id]
    
    # Calculate summary statistics
    total_modules = len(student_record.module_progress)
    completed_modules = len(student_record.completed_chapters)
    avg_score = sum(student_record.assessment_scores) / len(student_record.assessment_scores) if student_record.assessment_scores else 0.0
    
    # Group progress by module
    module_progress = {}
    for module_chapter, progress in student_record.module_progress.items():
        module_name, chapter_name = module_chapter.split(":", 1)
        if module_name not in module_progress:
            module_progress[module_name] = {"chapters": [], "avg_progress": 0.0}
        module_progress[module_name]["chapters"].append({
            "chapter": chapter_name,
            "progress": progress
        })
    
    # Calculate average progress per module
    for module_name, data in module_progress.items():
        total_progress = sum(chapter["progress"] for chapter in data["chapters"])
        data["avg_progress"] = total_progress / len(data["chapters"])
    
    summary = {
        "student_id": student_id,
        "start_date": student_record.start_date.isoformat(),
        "completion_date": student_record.completion_date.isoformat() if student_record.completion_date else None,
        "total_modules": total_modules,
        "completed_modules": completed_modules,
        "total_chapters": len(student_record.completed_chapters),
        "average_score": avg_score,
        "module_progress": module_progress,
        "overall_completion": (completed_modules / total_modules * 100) if total_modules > 0 else 0,
        "timestamp": datetime.now().isoformat()
    }
    
    return summary


@router.get("/{student_id}/recommendations", response_model=Dict[str, Any])
async def get_learning_recommendations(student_id: str):
    """
    Get personalized learning recommendations based on student progress.
    """
    if student_id not in student_progress_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        )
    
    student_record = student_progress_storage[student_id]
    
    # Analyze progress to generate recommendations
    low_progress_modules = []
    for module_chapter, progress in student_record.module_progress.items():
        if progress < 50:  # Modules with less than 50% progress
            low_progress_modules.append({
                "module_chapter": module_chapter,
                "progress": progress
            })
    
    # Suggest next modules based on curriculum flow
    # In a real implementation, this would use a curriculum graph
    suggested_next = []
    if not student_record.completed_chapters:
        # If no chapters completed yet, suggest starting modules
        suggested_next = ["Introduction to VLA", "Voice Command Recognition"]
    else:
        # Otherwise, suggest next logical modules
        last_completed = student_record.completed_chapters[-1] if student_record.completed_chapters else ""
        # This is a simplified example - in reality, curriculum dependencies would be considered
        if "Voice Command Recognition" in last_completed:
            suggested_next = ["LLM-Based Action Sequencing", "Multimodal Fusion"]
        elif "LLM-Based Action Sequencing" in last_completed:
            suggested_next = ["Multimodal Fusion", "Capstone Project"]
        else:
            suggested_next = ["Capstone Project"]
    
    # Identify areas needing improvement
    improvement_areas = []
    if student_record.assessment_scores:
        avg_score = sum(student_record.assessment_scores) / len(student_record.assessment_scores)
        if avg_score < 70:  # Low average score
            improvement_areas.append("General assessment performance")
        
        # Identify specific low scores
        for i, score in enumerate(student_record.assessment_scores):
            if score < 60:  # Low score
                improvement_areas.append(f"Assessment #{i+1} - needs improvement")
    
    recommendations = {
        "student_id": student_id,
        "low_progress_modules": low_progress_modules,
        "suggested_next_modules": suggested_next,
        "improvement_areas": improvement_areas,
        "study_time_suggestions": "Consider spending more time on modules with low progress",
        "timestamp": datetime.now().isoformat()
    }
    
    return recommendations


@router.delete("/{student_id}", response_model=Dict[str, str])
async def delete_student_progress(student_id: str):
    """
    Delete a student's progress record.
    """
    if student_id not in student_progress_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        )
    
    del student_progress_storage[student_id]
    
    return {
        "status": "deleted",
        "message": f"Student progress for {student_id} has been deleted",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/{student_id}/analytics", response_model=Dict[str, Any])
async def get_student_analytics(student_id: str):
    """
    Get detailed analytics for a student's learning progress.
    """
    if student_id not in student_progress_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        )
    
    student_record = student_progress_storage[student_id]
    
    # Calculate analytics
    progress_values = list(student_record.module_progress.values())
    if progress_values:
        analytics = {
            "student_id": student_id,
            "progress_stats": {
                "mean_progress": sum(progress_values) / len(progress_values),
                "median_progress": sorted(progress_values)[len(progress_values) // 2],
                "min_progress": min(progress_values),
                "max_progress": max(progress_values),
                "std_deviation": (sum((x - sum(progress_values) / len(progress_values))**2 for x in progress_values) / len(progress_values))**0.5 if len(progress_values) > 1 else 0
            }
        }
        
        if student_record.assessment_scores:
            score_values = student_record.assessment_scores
            analytics["assessment_stats"] = {
                "mean_score": sum(score_values) / len(score_values),
                "median_score": sorted(score_values)[len(score_values) // 2],
                "min_score": min(score_values),
                "max_score": max(score_values),
                "std_deviation": (sum((x - sum(score_values) / len(score_values))**2 for x in score_values) / len(score_values))**0.5 if len(score_values) > 1 else 0
            }
        
        # Time-based analytics
        if student_record.start_date:
            time_elapsed = (datetime.now() - student_record.start_date).days
            analytics["timeline_stats"] = {
                "days_since_start": time_elapsed,
                "chapters_completed": len(student_record.completed_chapters),
                "avg_progress_per_day": (len(student_record.completed_chapters) / time_elapsed) if time_elapsed > 0 else 0
            }
    else:
        analytics = {
            "student_id": student_id,
            "progress_stats": {
                "mean_progress": 0,
                "median_progress": 0,
                "min_progress": 0,
                "max_progress": 0,
                "std_deviation": 0
            },
            "message": "No progress data available"
        }
    
    analytics["timestamp"] = datetime.now().isoformat()
    
    return analytics


# Example usage:
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    # Add a sample student record for testing
    sample_student = StudentLearningPath(
        id=str(uuid.uuid4()),
        student_id="student_123",
        module_progress={
            "VLA:Introduction": 100.0,
            "VLA:Voice Command Recognition": 85.0,
            "VLA:LLM Action Sequencing": 60.0
        },
        completed_chapters=["VLA:Introduction"],
        assessment_scores=[88.0, 76.0],
        start_date=datetime.now()
    )
    student_progress_storage["student_123"] = sample_student
    
    app = FastAPI()
    app.include_router(router, prefix="/vla/learning", tags=["student-progress"])
    
    # Run the API
    # uvicorn.run(app, host="0.0.0.0", port=8000)