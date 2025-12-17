from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import uuid
from pydantic import BaseModel
from datetime import datetime
from ..models.action_sequence import ActionSequence
from ..services.llm_service import LLMService, LLMConfig
from ..config import settings
from ..validation.voice_command_validation import validate_action_sequence


# Initialize router
router = APIRouter()


class LLMActionRequest(BaseModel):
    """Request model for LLM-based action generation."""
    intent: str
    parameters: Dict[str, Any]
    context: Dict[str, Any] = {}  # Additional context for the action generation
    student_id: str = None


class LLMActionResponse(BaseModel):
    """Response model for LLM-based action generation."""
    action_sequence_id: str
    intent: str
    parameters: Dict[str, Any]
    action_sequence: ActionSequence
    processing_time: float


@router.post("/", response_model=LLMActionResponse)
async def generate_action_sequence(request: LLMActionRequest):
    """
    Generate an action sequence based on natural language command using an LLM.
    """
    start_time = datetime.now()
    
    try:
        # Initialize the LLM service with configuration
        llm_config = LLMConfig(
            model_name=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        llm_service = LLMService(llm_config)
        
        # Generate action sequence using LLM
        action_steps = await llm_service.generate_action_sequence(
            intent=request.intent,
            parameters=request.parameters,
            context=request.context
        )
        
        if not action_steps or len(action_steps) == 0:
            raise HTTPException(
                status_code=400,
                detail="LLM failed to generate valid action steps for the given command"
            )
        
        # Create an action sequence
        action_sequence_id = str(uuid.uuid4())
        action_sequence = ActionSequence(
            id=action_sequence_id,
            voice_command_id="",  # Will be set when associated with a voice command
            sequence=action_steps,
            description=f"Action sequence for intent: {request.intent}",
        )
        
        # Validate the generated action sequence
        validation_result = validate_action_sequence(action_sequence)
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=500,
                detail=f"Generated action sequence is invalid: {validation_result.errors}"
            )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create and return the response
        response = LLMActionResponse(
            action_sequence_id=action_sequence.id,
            intent=request.intent,
            parameters=request.parameters,
            action_sequence=action_sequence,
            processing_time=processing_time
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating action sequence: {str(e)}"
        )


@router.post("/from_text", response_model=LLMActionResponse)
async def generate_action_sequence_from_text(request: LLMActionRequest):
    """
    Generate an action sequence directly from natural language text.
    This endpoint takes a text command and processes it through intent extraction and LLM processing.
    """
    start_time = datetime.now()
    
    try:
        # For this endpoint, we'll use the LLM to both extract intent and generate actions
        # In a real implementation, you might want to separate these functions
        
        # Initialize the LLM service
        llm_config = LLMConfig(
            model_name=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        llm_service = LLMService(llm_config)
        
        # Create a natural language command from the request
        command_text = f"{request.intent} "
        if request.parameters:
            param_str = ", ".join([f"{k}={v}" for k, v in request.parameters.items()])
            command_text += f"with parameters: {param_str}"
        
        # Extract intent and parameters using the LLM
        # This would require a more sophisticated approach in practice
        intent = request.intent
        parameters = request.parameters
        
        # Generate action sequence
        action_steps = await llm_service.generate_action_sequence(
            intent=intent,
            parameters=parameters,
            context=request.context
        )
        
        if not action_steps or len(action_steps) == 0:
            raise HTTPException(
                status_code=400,
                detail="LLM failed to generate valid action steps for the given command"
            )
        
        # Create an action sequence
        action_sequence_id = str(uuid.uuid4())
        action_sequence = ActionSequence(
            id=action_sequence_id,
            voice_command_id="",  # Will be set when associated with a voice command
            sequence=action_steps,
            description=f"Action sequence for: {command_text}",
        )
        
        # Validate the generated action sequence
        validation_result = validate_action_sequence(action_sequence)
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=500,
                detail=f"Generated action sequence is invalid: {validation_result.errors}"
            )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create and return the response
        response = LLMActionResponse(
            action_sequence_id=action_sequence.id,
            intent=request.intent,
            parameters=request.parameters,
            action_sequence=action_sequence,
            processing_time=processing_time
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating action sequence from text: {str(e)}"
        )


# Example usage:
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router, prefix="/llm/actions", tags=["llm-actions"])
    
    # Run the API
    # uvicorn.run(app, host="0.0.0.0", port=8000)