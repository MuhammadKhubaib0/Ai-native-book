from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import uuid
from pydantic import BaseModel
from datetime import datetime
from ..models.vla_system_state import VLASystemState, Pose
from ..models.multimodal_input import MultimodalInput
from ..services.vision_integration import VisionIntegrationService
from ..services.multimodal_fusion import MultimodalFusionService
from ..services.conflict_resolver import ConflictResolver
from ..services.confidence_manager import ConfidenceManager
from ..config import settings


# Initialize router
router = APIRouter()


class VLAStateUpdateRequest(BaseModel):
    """Request model for updating VLA system state."""
    robot_pose: Optional[Pose] = None
    current_voice_command: Optional[str] = None
    current_action_sequence: Optional[str] = None
    perception_data: Optional[Dict[str, Any]] = None
    system_status: Optional[str] = None


class VLAStateResponse(BaseModel):
    """Response model for VLA system state."""
    system_state: VLASystemState
    timestamp: datetime
    processing_time: float


class VLAStateUpdateResponse(BaseModel):
    """Response model for VLA system state update."""
    updated_state: VLASystemState
    success: bool
    message: str
    timestamp: datetime


# Global state storage (in a real implementation, this would use a database or Redis)
vla_system_state = VLASystemState(
    id=f"state_{int(datetime.now().timestamp())}",
    current_voice_command="",
    current_action_sequence="",
    system_status="idle",
    perception_data={},
    last_update=datetime.now()
)


@router.get("/", response_model=VLAStateResponse)
async def get_vla_system_state():
    """
    Get the current state of the VLA (Vision-Language-Action) system.
    """
    start_time = datetime.now()
    
    # In a real implementation, this would fetch the actual system state
    # from the running VLA system. For this example, we'll return the global state.
    global vla_system_state
    
    # Update the response timestamp
    processing_time = (datetime.now() - start_time).total_seconds()
    
    response = VLAStateResponse(
        system_state=vla_system_state,
        timestamp=datetime.now(),
        processing_time=processing_time
    )
    
    return response


@router.put("/", response_model=VLAStateUpdateResponse)
async def update_vla_system_state(request: VLAStateUpdateRequest):
    """
    Update the state of the VLA (Vision-Language-Action) system.
    """
    global vla_system_state
    
    try:
        # Update the state based on the request
        if request.robot_pose:
            vla_system_state.robot_pose = request.robot_pose
        
        if request.current_voice_command is not None:
            vla_system_state.current_voice_command = request.current_voice_command
        
        if request.current_action_sequence is not None:
            vla_system_state.current_action_sequence = request.current_action_sequence
        
        if request.perception_data:
            vla_system_state.perception_data = request.perception_data
        
        if request.system_status:
            vla_system_state.system_status = request.system_status
        
        # Update the last update timestamp
        vla_system_state.last_update = datetime.now()
        
        response = VLAStateUpdateResponse(
            updated_state=vla_system_state,
            success=True,
            message="VLA system state updated successfully",
            timestamp=datetime.now()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating VLA system state: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, Any])
async def get_vla_system_health():
    """
    Get the health status of the VLA system components.
    """
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "system_id": vla_system_state.id,
        "status": vla_system_state.system_status,
        "components": {
            "voice_recognition": "healthy",  # Would check actual service status in real implementation
            "llm_processing": "healthy",
            "vision_processing": "healthy",
            "action_execution": "healthy",
            "multimodal_fusion": "healthy"
        },
        "robot_pose": vla_system_state.robot_pose.dict() if vla_system_state.robot_pose else None,
        "current_voice_command": vla_system_state.current_voice_command,
        "current_action_sequence": vla_system_state.current_action_sequence,
        "perception_data_summary": {
            "object_count": len(vla_system_state.perception_data.get("objects", [])) if vla_system_state.perception_data else 0,
            "last_update": vla_system_state.last_update.isoformat()
        }
    }
    
    return health_status


@router.post("/process_multimodal", response_model=VLAStateUpdateResponse)
async def process_multimodal_input(multimodal_input: MultimodalInput):
    """
    Process multimodal input and update the system state accordingly.
    """
    global vla_system_state
    start_time = datetime.now()
    
    try:
        # Initialize services
        fusion_service = MultimodalFusionService()
        conflict_resolver = ConflictResolver()
        confidence_manager = ConfidenceManager()
        vision_service = VisionIntegrationService()
        
        # Detect and resolve conflicts in the multimodal input
        voice_data = {"text": multimodal_input.voice_input_id} if multimodal_input.voice_input_id else None
        vision_data = multimodal_input.visual_data
        sensor_data = multimodal_input.sensor_data
        
        conflicts = conflict_resolver.detect_conflicts(voice_data, vision_data, sensor_data)
        
        if conflicts:
            # Resolve conflicts before processing
            resolution_results = conflict_resolver.resolve_conflicts(
                conflicts, voice_data, vision_data, sensor_data
            )
            # In a real implementation, resolution_results would be used to adjust the input
        
        # Perform multimodal fusion
        fusion_result, confidence = fusion_service.fuse_modalities(
            voice_data=voice_data,
            vision_data=vision_data,
            sensor_data=sensor_data
        )
        
        # Validate confidence
        if confidence < confidence_manager.minimum_confidence_threshold:
            return VLAStateUpdateResponse(
                updated_state=vla_system_state,
                success=False,
                message=f"Multimodal fusion confidence {confidence:.2f} below threshold {confidence_manager.minimum_confidence_threshold}",
                timestamp=datetime.now()
            )
        
        # Update the system state based on fusion result
        if fusion_result:
            # Update perception data with fusion result
            vla_system_state.perception_data = {
                **(vla_system_state.perception_data or {}),
                "last_fusion_result": fusion_result,
                "fusion_confidence": confidence
            }
            
            # Update status based on fusion result
            if "intent" in fusion_result:
                intent = fusion_result["intent"]
                if "navigation" in intent.lower():
                    vla_system_state.system_status = "executing"  # or appropriate status
                elif "idle" in intent.lower():
                    vla_system_state.system_status = "idle"
        
        # Update the last update timestamp
        vla_system_state.last_update = datetime.now()
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        response = VLAStateUpdateResponse(
            updated_state=vla_system_state,
            success=True,
            message=f"Processed multimodal input successfully, confidence: {confidence:.2f}, processing time: {processing_time:.3f}s",
            timestamp=datetime.now()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing multimodal input: {str(e)}"
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_vla_system_stats():
    """
    Get statistics about the VLA system operation.
    """
    stats = {
        "timestamp": datetime.now().isoformat(),
        "system_uptime": (datetime.now() - vla_system_state.last_update).total_seconds() if vla_system_state.last_update else 0,
        "total_commands_processed": getattr(vla_system_state, 'total_commands', 0),  # This would need to be added to the model
        "current_status": vla_system_state.system_status,
        "active_components": [
            "voice_recognition",
            "llm_processing", 
            "vision_processing",
            "action_execution"
        ],
        "performance_metrics": {
            "avg_fusion_time": getattr(vla_system_state, 'avg_fusion_time', 0.1),  # Would be tracked in real implementation
            "success_rate": getattr(vla_system_state, 'success_rate', 0.95)  # Would be tracked in real implementation
        }
    }
    
    return stats


# Example usage:
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router, prefix="/vla/system", tags=["vla-system"])
    
    # Run the API
    # uvicorn.run(app, host="0.0.0.0", port=8000)