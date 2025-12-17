from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import uuid
from pydantic import BaseModel
from datetime import datetime
from ..models.multimodal_input import MultimodalInput
from ..models.vla_system_state import VLASystemState
from ..services.multimodal_fusion import MultimodalFusionService
from ..services.vision_integration import VisionIntegrationService
from ..config import settings
from ..validation.multimodal_validation import validate_multimodal_input


# Initialize router
router = APIRouter()


class MultimodalFusionRequest(BaseModel):
    """Request model for multimodal fusion."""
    voice_input: Optional[Dict[str, Any]] = None
    vision_data: Optional[Dict[str, Any]] = None
    sensor_data: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = {}  # Additional contextual information


class MultimodalFusionResponse(BaseModel):
    """Response model for multimodal fusion."""
    fusion_result_id: str
    voice_input_id: Optional[str] = None
    vision_input_id: Optional[str] = None
    sensor_input_id: Optional[str] = None
    fused_result: Dict[str, Any]
    confidence: float
    processing_time: float


@router.post("/", response_model=MultimodalFusionResponse)
async def process_multimodal_input(request: MultimodalFusionRequest):
    """
    Process multimodal inputs (voice, vision, sensors) and produce a fused result.
    """
    start_time = datetime.now()
    
    try:
        # Create a MultimodalInput object
        fusion_input = MultimodalInput(
            id=str(uuid.uuid4()),
            voice_input_id=request.voice_input.get("id") if request.voice_input else None,
            visual_data=request.vision_data,
            sensor_data=request.sensor_data
        )
        
        # Validate the multimodal input
        validation_result = validate_multimodal_input(fusion_input)
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid multimodal input: {validation_result.errors}"
            )
        
        # Initialize the fusion service
        fusion_service = MultimodalFusionService()
        
        # Perform multimodal fusion
        fused_result, confidence = fusion_service.fuse_modalities(
            voice_data=request.voice_input,
            vision_data=request.vision_data,
            sensor_data=request.sensor_data,
            context=request.context
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create and return the response
        response = MultimodalFusionResponse(
            fusion_result_id=fusion_input.id,
            voice_input_id=request.voice_input.get("id") if request.voice_input else None,
            vision_input_id=None,  # Would be filled if vision processing was done separately
            sensor_input_id=None,  # Would be filled if sensor processing was done separately
            fused_result=fused_result,
            confidence=confidence,
            processing_time=processing_time
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing multimodal input: {str(e)}"
        )


@router.post("/integrate_with_vision", response_model=MultimodalFusionResponse)
async def process_with_vision_integration(request: MultimodalFusionRequest):
    """
    Process multimodal inputs with optional vision integration from Isaac Sim.
    """
    start_time = datetime.now()
    
    try:
        # Initialize vision integration service
        vision_service = VisionIntegrationService()
        
        # Process vision data if provided
        processed_vision_data = None
        if request.vision_data:
            processed_vision_data = await vision_service.process_isaac_sim_data(request.vision_data)
        
        # Create a MultimodalInput object
        fusion_input = MultimodalInput(
            id=str(uuid.uuid4()),
            voice_input_id=request.voice_input.get("id") if request.voice_input else None,
            visual_data=processed_vision_data or request.vision_data,
            sensor_data=request.sensor_data
        )
        
        # Validate the multimodal input
        validation_result = validate_multimodal_input(fusion_input)
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid multimodal input: {validation_result.errors}"
            )
        
        # Initialize the fusion service
        fusion_service = MultimodalFusionService()
        
        # Perform multimodal fusion
        fused_result, confidence = fusion_service.fuse_modalities(
            voice_data=request.voice_input,
            vision_data=processed_vision_data or request.vision_data,
            sensor_data=request.sensor_data,
            context=request.context
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create and return the response
        response = MultimodalFusionResponse(
            fusion_result_id=fusion_input.id,
            voice_input_id=request.voice_input.get("id") if request.voice_input else None,
            vision_input_id=None,
            sensor_input_id=None,
            fused_result=fused_result,
            confidence=confidence,
            processing_time=processing_time
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing multimodal input with vision integration: {str(e)}"
        )


@router.get("/system_state", response_model=VLASystemState)
async def get_system_state():
    """
    Get the current state of the VLA system with multimodal information.
    """
    # In a real implementation, this would fetch the actual system state
    # For this example, we'll return a mock state
    state = VLASystemState(
        id=str(uuid.uuid4()),
        current_voice_command="",
        current_action_sequence="",
        system_status="idle"  # Should come from the actual system
    )
    
    return state


# Example usage:
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router, prefix="/multimodal/fusion", tags=["multimodal-fusion"])
    
    # Run the API
    # uvicorn.run(app, host="0.0.0.0", port=8000)