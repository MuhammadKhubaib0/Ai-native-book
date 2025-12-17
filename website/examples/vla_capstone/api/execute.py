from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
import uuid
import asyncio
from pydantic import BaseModel
from datetime import datetime
from ..models.action_sequence import ActionSequence, ActionSequenceStatus
from ..models.action_step import ActionStep, ActionType
from ..models.vla_system_state import VLASystemState
from ..services.action_validator import ActionValidator
from ..services.error_recovery import ErrorRecoveryService, ErrorType, RecoveryStrategy
from ..services.confidence_manager import ConfidenceManager
from ..simulation.gazebo_integration import GazeboIntegrationService
from ..config import settings


# Initialize router
router = APIRouter()


class ExecutionRequest(BaseModel):
    """Request model for executing action sequences."""
    action_sequence_id: str
    action_sequence: Optional[ActionSequence] = None
    execution_context: Optional[Dict[str, Any]] = {}
    timeout: Optional[float] = 30.0  # Default timeout of 30 seconds


class ExecutionResponse(BaseModel):
    """Response model for action execution."""
    execution_id: str
    action_sequence_id: str
    status: str
    message: str
    timestamp: datetime
    execution_time: Optional[float] = None


class ExecutionStatusResponse(BaseModel):
    """Response model for execution status."""
    execution_id: str
    action_sequence_id: str
    current_step: Optional[int] = None
    total_steps: int
    status: str
    progress: float
    timestamp: datetime


# Global execution tracking (in a real implementation, this would use a database or Redis)
active_executions = {}


@router.post("/", response_model=ExecutionResponse)
async def execute_action_sequence(
    request: ExecutionRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute an action sequence in the VLA system.
    """
    execution_id = str(uuid.uuid4())
    
    try:
        # Validate the request
        if not request.action_sequence and not request.action_sequence_id:
            raise HTTPException(
                status_code=400,
                detail="Either action_sequence or action_sequence_id must be provided"
            )
        
        # Get or load the action sequence
        action_sequence = request.action_sequence
        if not action_sequence:
            # In a real implementation, this would fetch the sequence from storage
            # For this example, we'll raise an error since we don't have persistence
            raise HTTPException(
                status_code=404,
                detail=f"Action sequence {request.action_sequence_id} not found, must be provided in request"
            )
        
        # Validate the action sequence
        validator = ActionValidator()
        validation_issues = validator.validate_action_sequence(action_sequence)
        
        if validation_issues:
            issue_descriptions = [str(issue) for issue in validation_issues]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action sequence: {issue_descriptions}"
            )
        
        # Check if the sequence is executable
        if not validator.validate_for_execution(action_sequence):
            raise HTTPException(
                status_code=400,
                detail="Action sequence is not valid for execution"
            )
        
        # Initialize execution tracking
        active_executions[execution_id] = {
            "action_sequence": action_sequence,
            "status": ActionSequenceStatus.IN_PROGRESS,
            "current_step": 0,
            "execution_start": datetime.now(),
            "execution_context": request.execution_context
        }
        
        # Start background execution
        background_tasks.add_task(
            _execute_action_sequence_background,
            execution_id,
            action_sequence,
            request.timeout,
            request.execution_context
        )
        
        response = ExecutionResponse(
            execution_id=execution_id,
            action_sequence_id=action_sequence.id,
            status="started",
            message=f"Execution of action sequence {action_sequence.id} started",
            timestamp=datetime.now()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting action sequence execution: {str(e)}"
        )


@router.get("/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(execution_id: str):
    """
    Get the status of an action sequence execution.
    """
    if execution_id not in active_executions:
        raise HTTPException(
            status_code=404,
            detail=f"Execution with ID {execution_id} not found"
        )
    
    execution_data = active_executions[execution_id]
    action_sequence = execution_data["action_sequence"]
    
    progress = 0.0
    total_steps = len(action_sequence.sequence)
    current_step_index = execution_data.get("current_step", 0)
    
    if total_steps > 0:
        progress = current_step_index / total_steps * 100.0 if current_step_index <= total_steps else 100.0
    
    status = execution_data["status"]
    if isinstance(status, ActionSequenceStatus):
        status = status.value
    
    response = ExecutionStatusResponse(
        execution_id=execution_id,
        action_sequence_id=action_sequence.id,
        current_step=current_step_index,
        total_steps=total_steps,
        status=status,
        progress=progress,
        timestamp=datetime.now()
    )
    
    return response


@router.post("/cancel/{execution_id}", response_model=ExecutionResponse)
async def cancel_execution(execution_id: str):
    """
    Cancel an in-progress action sequence execution.
    """
    if execution_id not in active_executions:
        raise HTTPException(
            status_code=404,
            detail=f"Execution with ID {execution_id} not found"
        )
    
    execution_data = active_executions[execution_id]
    
    # Update status to cancelled
    execution_data["status"] = ActionSequenceStatus.FAILED  # Using FAILED to indicate cancellation
    execution_data["message"] = "Execution cancelled by user request"
    
    response = ExecutionResponse(
        execution_id=execution_id,
        action_sequence_id=execution_data["action_sequence"].id,
        status="cancelled",
        message="Execution cancelled successfully",
        timestamp=datetime.now()
    )
    
    return response


async def _execute_action_sequence_background(
    execution_id: str,
    action_sequence: ActionSequence,
    timeout: float,
    execution_context: Dict[str, Any]
):
    """
    Execute an action sequence in the background.
    
    :param execution_id: ID of the execution
    :param action_sequence: The action sequence to execute
    :param timeout: Maximum time for the sequence execution
    :param execution_context: Context for execution
    """
    try:
        # Update status to in progress
        active_executions[execution_id]["status"] = ActionSequenceStatus.IN_PROGRESS
        active_executions[execution_id]["start_time"] = datetime.now()
        
        # Initialize services for execution
        error_recovery = ErrorRecoveryService()
        confidence_manager = ConfidenceManager()
        gazebo_service = GazeboIntegrationService()
        
        # Connect to simulation if needed
        simulation_connected = await gazebo_service.connect_to_gazebo()
        
        # Execute each action step in sequence
        for i, action_step in enumerate(action_sequence.sequence):
            # Update current step
            active_executions[execution_id]["current_step"] = i
            
            try:
                # Check for timeout
                start_time = active_executions[execution_id]["start_time"]
                elapsed_time = (datetime.now() - start_time).total_seconds()
                if elapsed_time > timeout:
                    raise asyncio.TimeoutError(f"Execution timeout after {elapsed_time}s")
                
                # Execute the action step based on its type
                success = await _execute_action_step(
                    action_step, 
                    gazebo_service, 
                    execution_context,
                    error_recovery
                )
                
                if not success:
                    # Action failed, try recovery
                    recovery_result = error_recovery.handle_error(
                        ErrorType.EXECUTION_ERROR,
                        action_sequence,
                        action_step,
                        {"error": "Action execution failed", "step": i}
                    )
                    
                    if recovery_result["strategy"] == RecoveryStrategy.ABORT.value:
                        active_executions[execution_id]["status"] = ActionSequenceStatus.FAILED
                        active_executions[execution_id]["message"] = f"Execution failed at step {i}, recovery aborted"
                        return
                    elif recovery_result["strategy"] == RecoveryStrategy.SKIP.value:
                        continue  # Skip to next step
                    elif recovery_result["strategy"] == RecoveryStrategy.RETRY.value:
                        # Retry the action
                        success = await _execute_action_step(
                            action_step, 
                            gazebo_service, 
                            execution_context,
                            error_recovery
                        )
                        if not success:
                            # Retry failed
                            active_executions[execution_id]["status"] = ActionSequenceStatus.FAILED
                            active_executions[execution_id]["message"] = f"Execution failed after retry at step {i}"
                            return
                    elif recovery_result["strategy"] == RecoveryStrategy.REPLAN.value:
                        # For this example, replanning would require a more complex implementation
                        # For simplicity, we'll treat it as a failure
                        active_executions[execution_id]["status"] = ActionSequenceStatus.FAILED
                        active_executions[execution_id]["message"] = f"Execution failed at step {i}, replanning required"
                        return
            except asyncio.TimeoutError:
                active_executions[execution_id]["status"] = ActionSequenceStatus.FAILED
                active_executions[execution_id]["message"] = f"Execution timed out after {elapsed_time}s"
                return
            except Exception as step_error:
                active_executions[execution_id]["status"] = ActionSequenceStatus.FAILED
                active_executions[execution_id]["message"] = f"Error executing step {i}: {str(step_error)}"
                return
        
        # If we get here, all steps completed successfully
        active_executions[execution_id]["status"] = ActionSequenceStatus.COMPLETED
        active_executions[execution_id]["message"] = "Action sequence executed successfully"
        active_executions[execution_id]["current_step"] = len(action_sequence.sequence)
        
    except Exception as e:
        active_executions[execution_id]["status"] = ActionSequenceStatus.FAILED
        active_executions[execution_id]["message"] = f"Unexpected error during execution: {str(e)}"
    finally:
        # Disconnect from simulation if connected
        if "gazebo_service" in locals():
            try:
                await gazebo_service.disconnect_from_gazebo()
            except:
                pass  # Ignore disconnection errors


async def _execute_action_step(
    action_step: ActionStep,
    gazebo_service: GazeboIntegrationService,
    execution_context: Dict[str, Any],
    error_recovery: ErrorRecoveryService
) -> bool:
    """
    Execute a single action step in simulation.
    
    :param action_step: The action step to execute
    :param gazebo_service: Gazebo integration service
    :param execution_context: Context for execution
    :param error_recovery: Error recovery service
    :return: True if successful, False otherwise
    """
    try:
        # Execute the action based on its type
        if action_step.action_type == ActionType.NAVIGATION:
            return await gazebo_service._execute_navigation_action(action_step.parameters)
        elif action_step.action_type == ActionType.MANIPULATION:
            return await gazebo_service._execute_manipulation_action(action_step.parameters)
        elif action_step.action_type == ActionType.PERCEPTION:
            return await gazebo_service._execute_perception_action(action_step.parameters)
        else:
            # For other action types, execute using a generic method
            return await gazebo_service._execute_other_action(action_step.action_type, action_step.parameters)
    except Exception as e:
        print(f"Error executing action step {action_step.id}: {str(e)}")
        return False


class ExecuteWithFeedbackRequest(BaseModel):
    """Request model for executing with real-time feedback."""
    action_sequence: ActionSequence
    enable_feedback: bool = True
    feedback_frequency: float = 1.0  # seconds between feedback updates
    execution_context: Optional[Dict[str, Any]] = {}


@router.post("/with_feedback", response_model=ExecutionResponse)
async def execute_with_feedback(
    request: ExecuteWithFeedbackRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute an action sequence with real-time feedback.
    """
    execution_id = str(uuid.uuid4())
    
    try:
        # Validate the action sequence
        validator = ActionValidator()
        validation_issues = validator.validate_action_sequence(request.action_sequence)
        
        if validation_issues:
            issue_descriptions = [str(issue) for issue in validation_issues]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action sequence: {issue_descriptions}"
            )
        
        # Initialize execution tracking
        active_executions[execution_id] = {
            "action_sequence": request.action_sequence,
            "status": ActionSequenceStatus.PENDING,
            "current_step": 0,
            "execution_start": datetime.now(),
            "execution_context": request.execution_context,
            "feedback_enabled": request.enable_feedback
        }
        
        # Start background execution with feedback
        background_tasks.add_task(
            _execute_action_sequence_with_feedback,
            execution_id,
            request.action_sequence,
            request.execution_context,
            request.feedback_frequency if request.enable_feedback else None
        )
        
        response = ExecutionResponse(
            execution_id=execution_id,
            action_sequence_id=request.action_sequence.id,
            status="started_with_feedback",
            message=f"Execution of action sequence {request.action_sequence.id} started with feedback enabled",
            timestamp=datetime.now()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting action sequence execution with feedback: {str(e)}"
        )


async def _execute_action_sequence_with_feedback(
    execution_id: str,
    action_sequence: ActionSequence,
    execution_context: Dict[str, Any],
    feedback_frequency: Optional[float]
):
    """
    Execute an action sequence with real-time feedback.
    
    :param execution_id: ID of the execution
    :param action_sequence: The action sequence to execute
    :param execution_context: Context for execution
    :param feedback_frequency: Frequency of feedback updates (None to disable)
    """
    try:
        # Update status
        active_executions[execution_id]["status"] = ActionSequenceStatus.IN_PROGRESS
        active_executions[execution_id]["start_time"] = datetime.now()
        
        # Initialize services
        gazebo_service = GazeboIntegrationService()
        await gazebo_service.connect_to_gazebo()
        
        # Execute each action step in sequence
        for i, action_step in enumerate(action_sequence.sequence):
            # Update current step
            active_executions[execution_id]["current_step"] = i
            
            # Provide feedback if enabled
            if feedback_frequency is not None:
                await asyncio.sleep(feedback_frequency)
            
            # Execute the action step
            success = await _execute_action_step(
                action_step,
                gazebo_service,
                execution_context,
                ErrorRecoveryService()  # Temporary recovery service
            )
            
            if not success:
                active_executions[execution_id]["status"] = ActionSequenceStatus.FAILED
                active_executions[execution_id]["message"] = f"Execution failed at step {i}"
                return
        
        # All steps completed successfully
        active_executions[execution_id]["status"] = ActionSequenceStatus.COMPLETED
        active_executions[execution_id]["message"] = "Action sequence executed successfully with feedback"
        active_executions[execution_id]["current_step"] = len(action_sequence.sequence)
        
    except Exception as e:
        active_executions[execution_id]["status"] = ActionSequenceStatus.FAILED
        active_executions[execution_id]["message"] = f"Error during execution with feedback: {str(e)}"
    finally:
        # Disconnect from simulation
        try:
            await gazebo_service.disconnect_from_gazebo()
        except:
            pass


# Example usage:
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router, prefix="/vla/execute", tags=["vla-execute"])
    
    # Run the API
    # uvicorn.run(app, host="0.0.0.0", port=8000)