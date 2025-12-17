"""
Service for executing multi-step commands in the VLA system.
"""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
import traceback

from ..models.action_step import ActionStep, ActionType
from ..models.action_sequence import ActionSequence, ActionSequenceStatus
from ..models.multimodal_input import MultimodalInput
from ..models.vla_system_state import VLASystemState
from ..services.vision_integration import VisionIntegrationService
from ..services.object_manipulation import ObjectManipulationService
from ..services.navigation_service import NavigationService
from ..services.action_validator import ActionValidator
from ..services.error_recovery import ErrorRecoveryService, ErrorType, RecoveryStrategy
from ..simulation.gazebo_integration import GazeboIntegrationService
from ..integrations.isaac_integration import IsaacSimIntegrationService
from ..config import settings


class MultiStepExecutionService:
    """
    Service for executing multi-step commands consisting of multiple action steps.
    """
    
    def __init__(self):
        """Initialize the multi-step execution service."""
        self.vision_service = VisionIntegrationService()
        self.manipulation_service = ObjectManipulationService()
        self.navigation_service = NavigationService()
        self.action_validator = ActionValidator()
        self.error_recovery = ErrorRecoveryService()
        self.gazebo_service = GazeboIntegrationService()
        self.isaac_integration = IsaacSimIntegrationService()
        
        # Execution state tracking
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.max_history_entries = 1000
        
        # Execution parameters
        self.continue_on_failure = False
        self.enable_verification = True
        self.default_timeout = 30.0  # seconds
        self.inter_step_delay = 0.5  # seconds between steps
    
    async def execute_action_sequence(
        self,
        action_sequence: ActionSequence,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a complete action sequence.
        
        :param action_sequence: The sequence of actions to execute
        :param context: Context for execution (optional)
        :return: Execution results
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        # Validate the action sequence
        validation_issues = self.action_validator.validate_action_sequence(action_sequence)
        if validation_issues:
            return {
                "execution_id": execution_id,
                "success": False,
                "error": "Action sequence validation failed",
                "validation_issues": [str(issue) for issue in validation_issues],
                "timestamp": start_time,
                "execution_time": 0.0
            }
        
        # Initialize execution tracking
        execution_info = {
            "id": execution_id,
            "sequence_id": action_sequence.id,
            "status": ActionSequenceStatus.IN_PROGRESS,
            "steps_total": len(action_sequence.sequence),
            "steps_completed": 0,
            "steps_failed": 0,
            "current_step": 0,
            "start_time": start_time,
            "results": [],
            "errors": [],
            "context": context or {}
        }
        
        self.active_executions[execution_id] = execution_info
        
        try:
            # Execute each step in the sequence
            success = await self._execute_step_sequence(action_sequence, execution_info, context)
            
            # Update execution info
            execution_info["status"] = ActionSequenceStatus.COMPLETED if success else ActionSequenceStatus.FAILED
            execution_info["end_time"] = datetime.now()
            execution_info["execution_time"] = (execution_info["end_time"] - start_time).total_seconds()
            
            # Add to execution history
            self._add_to_execution_history(execution_info)
            
            # Return execution results
            return {
                "execution_id": execution_id,
                "success": success,
                "steps_executed": len(execution_info["results"]),
                "steps_failed": execution_info["steps_failed"],
                "results": execution_info["results"],
                "errors": execution_info["errors"],
                "timestamp": execution_info["end_time"],
                "execution_time": execution_info["execution_time"]
            }
            
        except Exception as e:
            error_msg = f"Error executing action sequence: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            
            # Update execution info for error
            execution_info["status"] = ActionSequenceStatus.FAILED
            execution_info["end_time"] = datetime.now()
            execution_info["execution_time"] = (execution_info["end_time"] - start_time).total_seconds()
            execution_info["errors"].append(error_msg)
            
            # Add to execution history
            self._add_to_execution_history(execution_info)
            
            return {
                "execution_id": execution_id,
                "success": False,
                "error": error_msg,
                "timestamp": execution_info["end_time"],
                "execution_time": execution_info["execution_time"]
            }
        finally:
            # Clean up active execution
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
    
    async def _execute_step_sequence(
        self,
        action_sequence: ActionSequence,
        execution_info: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Execute the sequence of steps.
        
        :param action_sequence: The sequence of actions to execute
        :param execution_info: Information about the current execution
        :param context: Execution context
        :return: True if all steps completed successfully, False otherwise
        """
        all_successful = True
        
        for i, action_step in enumerate(action_sequence.sequence):
            execution_info["current_step"] = i
            
            # Execute the step
            step_result = await self._execute_single_step(action_step, execution_info, context)
            execution_info["results"].append(step_result)
            
            if step_result["success"]:
                execution_info["steps_completed"] += 1
                print(f"Step {i+1}/{len(action_sequence.sequence)} completed successfully: {action_step.action_type.value}")
            else:
                execution_info["steps_failed"] += 1
                all_successful = False
                
                print(f"Step {i+1}/{len(action_sequence.sequence)} failed: {action_step.action_type.value}")
                
                # Handle error based on configuration
                if not self.continue_on_failure:
                    print("Stopping execution after failure")
                    break
                else:
                    print("Continuing execution despite failure")
        
        return all_successful
    
    async def _execute_single_step(
        self,
        action_step: ActionStep,
        execution_info: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute a single action step.
        
        :param action_step: The action step to execute
        :param execution_info: Information about the current execution
        :param context: Execution context
        :return: Result of the step execution
        """
        step_start_time = datetime.now()
        timeout = action_step.timeout or self.default_timeout
        
        try:
            # Determine which service to use based on action type
            if action_step.action_type == ActionType.NAVIGATION:
                result = await self._execute_navigation_step(action_step, context, timeout)
            elif action_step.action_type == ActionType.MANIPULATION:
                result = await self._execute_manipulation_step(action_step, context, timeout)
            elif action_step.action_type == ActionType.PERCEPTION:
                result = await self._execute_perception_step(action_step, context, timeout)
            else:
                result = await self._execute_other_step(action_step, context, timeout)
            
            # Calculate execution time
            execution_time = (datetime.now() - step_start_time).total_seconds()
            result["execution_time"] = execution_time
            
            # Verify results if verification is enabled
            if self.enable_verification:
                verification_result = await self._verify_step_execution(action_step, result, context)
                result["verification"] = verification_result
            
            # Add to context for future steps
            if context is not None:
                context[f"step_{action_step.order}_result"] = result
            
            return result
            
        except Exception as e:
            error_msg = f"Error executing step: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            
            return {
                "step_id": action_step.id,
                "action_type": action_step.action_type.value,
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now(),
                "execution_time": (datetime.now() - step_start_time).total_seconds()
            }
    
    async def _execute_navigation_step(
        self,
        action_step: ActionStep,
        context: Optional[Dict[str, Any]],
        timeout: float
    ) -> Dict[str, Any]:
        """
        Execute a navigation action step.
        
        :param action_step: The navigation action step to execute
        :param context: Execution context
        :param timeout: Timeout for execution
        :return: Result of the navigation step execution
        """
        try:
            # Extract navigation parameters
            target_x = action_step.parameters.get("x", 0.0)
            target_y = action_step.parameters.get("y", 0.0)
            target_z = action_step.parameters.get("z", 0.0)
            
            target_pose = {
                "x": target_x,
                "y": target_y,
                "z": target_z,
                "rotation": action_step.parameters.get("rotation", {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0})
            }
            
            # Execute navigation
            success = await self.navigation_service.navigate_to_location(
                target_x, target_y, target_z
            )
            
            return {
                "step_id": action_step.id,
                "action_type": action_step.action_type.value,
                "success": success,
                "target_pose": target_pose,
                "timestamp": datetime.now(),
                "parameters_used": action_step.parameters
            }
            
        except Exception as e:
            return {
                "step_id": action_step.id,
                "action_type": action_step.action_type.value,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now()
            }
    
    async def _execute_manipulation_step(
        self,
        action_step: ActionStep,
        context: Optional[Dict[str, Any]],
        timeout: float
    ) -> Dict[str, Any]:
        """
        Execute a manipulation action step.
        
        :param action_step: The manipulation action step to execute
        :param context: Execution context
        :param timeout: Timeout for execution
        :return: Result of the manipulation step execution
        """
        try:
            action = action_step.parameters.get("action", "grasp")
            object_id = action_step.parameters.get("object_id", "")
            
            if action == "grasp" or action == "pick":
                # Get current robot pose for context
                robot_pose = context.get("robot_pose") if context else None
                
                result = await self.manipulation_service.grasp_object(object_id, robot_pose)
                
                return {
                    "step_id": action_step.id,
                    "action_type": action_step.action_type.value,
                    "success": result.get("result") == "success",
                    "action": action,
                    "object_id": object_id,
                    "details": result,
                    "timestamp": datetime.now()
                }
            elif action == "place" or action == "set":
                # Get target pose
                target_pose = action_step.parameters.get("target_pose")
                robot_pose = context.get("robot_pose") if context else None
                
                if target_pose:
                    result = await self.manipulation_service.place_object(object_id, target_pose, robot_pose)
                    
                    return {
                        "step_id": action_step.id,
                        "action_type": action_step.action_type.value,
                        "success": result.get("result") == "success",
                        "action": action,
                        "object_id": object_id,
                        "target_pose": target_pose,
                        "details": result,
                        "timestamp": datetime.now()
                    }
                else:
                    return {
                        "step_id": action_step.id,
                        "action_type": action_step.action_type.value,
                        "success": False,
                        "error": "Target pose not specified for place action",
                        "timestamp": datetime.now()
                    }
            else:
                return {
                    "step_id": action_step.id,
                    "action_type": action_step.action_type.value,
                    "success": False,
                    "error": f"Unsupported manipulation action: {action}",
                    "timestamp": datetime.now()
                }
                
        except Exception as e:
            return {
                "step_id": action_step.id,
                "action_type": action_step.action_type.value,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now()
            }
    
    async def _execute_perception_step(
        self,
        action_step: ActionStep,
        context: Optional[Dict[str, Any]],
        timeout: float
    ) -> Dict[str, Any]:
        """
        Execute a perception action step.
        
        :param action_step: The perception action step to execute
        :param context: Execution context
        :param timeout: Timeout for execution
        :return: Result of the perception step execution
        """
        try:
            action = action_step.parameters.get("action", "detect")
            
            # Capture current perception data
            sim_data = await self.vision_service.capture_scene()
            
            # Process the perception data based on the action
            if action == "detect" or action == "find":
                target = action_step.parameters.get("target", "")
                
                # In a real implementation, this would search for the target object
                # For this simulation, we'll just return the current objects
                objects_found = [obj for obj in sim_data.get("objects", []) 
                                if target.lower() in obj.get("class", "").lower()]
                
                return {
                    "step_id": action_step.id,
                    "action_type": action_step.action_type.value,
                    "success": len(objects_found) > 0,
                    "action": action,
                    "target": target,
                    "objects_found": objects_found,
                    "timestamp": datetime.now()
                }
            elif action == "observe" or action == "scan":
                # Return scene information
                return {
                    "step_id": action_step.id,
                    "action_type": action_step.action_type.value,
                    "success": True,
                    "action": action,
                    "scene_description": sim_data.get("description", ""),
                    "objects_in_scene": sim_data.get("objects", []),
                    "timestamp": datetime.now()
                }
            else:
                return {
                    "step_id": action_step.id,
                    "action_type": action_step.action_type.value,
                    "success": False,
                    "error": f"Unsupported perception action: {action}",
                    "timestamp": datetime.now()
                }
                
        except Exception as e:
            return {
                "step_id": action_step.id,
                "action_type": action_step.action_type.value,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now()
            }
    
    async def _execute_other_step(
        self,
        action_step: ActionStep,
        context: Optional[Dict[str, Any]],
        timeout: float
    ) -> Dict[str, Any]:
        """
        Execute an 'other' type action step.
        
        :param action_step: The action step to execute
        :param context: Execution context
        :param timeout: Timeout for execution
        :return: Result of the step execution
        """
        # For this example, we'll just log the action and return success
        print(f"Executing other action: {action_step.action_type.value} with parameters: {action_step.parameters}")
        
        return {
            "step_id": action_step.id,
            "action_type": action_step.action_type.value,
            "success": True,
            "action": action_step.action_type.value,
            "parameters": action_step.parameters,
            "timestamp": datetime.now()
        }
    
    async def _verify_step_execution(
        self,
        action_step: ActionStep,
        result: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verify that the step was executed successfully.
        
        :param action_step: The action step that was executed
        :param result: Result of the execution
        :param context: Execution context
        :return: Verification result
        """
        try:
            verification = {
                "verified": result["success"],
                "confidence": 0.9 if result["success"] else 0.1,
                "details": f"Step executed with status: {'OK' if result['success'] else 'ERROR'}"
            }
            
            # Additional verification based on action type
            if action_step.action_type == ActionType.NAVIGATION:
                # Check if we are close to the target
                if result["success"]:
                    target_pose = result.get("target_pose", {})
                    # In a real implementation, check robot's actual position
                    verification["position_accuracy"] = "verified"  # Simulated verification
                
            elif action_step.action_type == ActionType.MANIPULATION:
                # Check if the object was actually grasped/placed
                if result["success"]:
                    details = result.get("details", {})
                    verification["grasp_success"] = details.get("result") == "success"
            
            return verification
            
        except Exception as e:
            return {
                "verified": False,
                "confidence": 0.0,
                "error": f"Verification error: {str(e)}",
                "details": "Could not verify step execution"
            }
    
    def _add_to_execution_history(self, execution_info: Dict[str, Any]):
        """
        Add execution info to history, limiting the number of entries.
        
        :param execution_info: Information about the completed execution
        """
        self.execution_history.append(execution_info)
        
        # Limit history size
        if len(self.execution_history) > self.max_history_entries:
            self.execution_history = self.execution_history[-self.max_history_entries:]
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a currently running execution.
        
        :param execution_id: ID of the execution to cancel
        :return: True if cancellation was successful, False otherwise
        """
        if execution_id in self.active_executions:
            execution_info = self.active_executions[execution_id]
            execution_info["status"] = ActionSequenceStatus.FAILED
            execution_info["errors"].append("Execution cancelled by user request")
            
            # Add to history
            self._add_to_execution_history(execution_info)
            
            # Remove from active executions
            del self.active_executions[execution_id]
            
            print(f"Execution {execution_id} cancelled")
            return True
        
        return False
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a currently running execution.
        
        :param execution_id: ID of the execution to check
        :return: Status information or None if execution not found
        """
        if execution_id in self.active_executions:
            execution_info = self.active_executions[execution_id]
            return {
                "execution_id": execution_id,
                "status": execution_info["status"].value,
                "steps_total": execution_info["steps_total"],
                "steps_completed": execution_info["steps_completed"],
                "steps_failed": execution_info["steps_failed"],
                "current_step": execution_info["current_step"] + 1,  # 1-indexed for user
                "start_time": execution_info["start_time"],
                "estimated_completion": "Calculating..."  # Would calculate based on progress
            }
        
        return None
    
    async def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the execution history.
        
        :param limit: Maximum number of results to return
        :return: List of execution history entries
        """
        return self.execution_history[-limit:]
    
    async def retry_failed_execution(
        self,
        execution_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retry a failed execution from the last failed step.
        
        :param execution_id: ID of the failed execution to retry
        :param context: New context for the retry
        :return: Result of the retry
        """
        # In a real implementation, this would find the failed execution
        # and retry from the point of failure
        # For this example, we'll just return a simulated retry result
        return {
            "execution_id": execution_id,
            "success": False,
            "message": "Retry functionality not fully implemented in this example",
            "timestamp": datetime.now()
        }
    
    async def get_execution_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics about execution performance.
        
        :return: Execution statistics
        """
        if not self.execution_history:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "success_rate": 0.0,
                "average_execution_time": 0.0,
                "timestamp": datetime.now()
            }
        
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for exec_info in self.execution_history 
                                  if exec_info["status"] == ActionSequenceStatus.COMPLETED)
        failed_executions = total_executions - successful_executions
        
        execution_times = [exec_info.get("execution_time", 0) for exec_info in self.execution_history]
        average_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0.0,
            "average_execution_time": average_execution_time,
            "timestamp": datetime.now()
        }


class AdvancedMultiStepExecutionService(MultiStepExecutionService):
    """
    Advanced multi-step execution service with error recovery and optimization capabilities.
    """
    
    def __init__(self):
        super().__init__()
        
        # Enable advanced features
        self.enable_error_recovery = True
        self.enable_optimization = True
        self.enable_learning = True
        self.enable_parallel_execution = False  # For compatible actions only
        
        # Optimizer parameters
        self.optimizer_enabled = True
        self.optimization_window = 3  # Number of steps to look ahead when optimizing
        
        # Learning parameters
        self.execution_experience = []
        self.performance_metrics = {}
    
    async def execute_action_sequence_with_recovery(
        self,
        action_sequence: ActionStep,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an action sequence with error recovery capabilities.
        
        :param action_sequence: The sequence of actions to execute
        :param context: Context for execution (optional)
        :return: Execution results with recovery information
        """
        if not self.enable_error_recovery:
            return await self.execute_action_sequence(action_sequence, context)
        
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        # Validate the action sequence
        validation_issues = self.action_validator.validate_action_sequence(action_sequence)
        if validation_issues:
            return {
                "execution_id": execution_id,
                "success": False,
                "error": "Action sequence validation failed",
                "validation_issues": [str(issue) for issue in validation_issues],
                "timestamp": start_time,
                "execution_time": 0.0,
                "recovery_attempts": []
            }
        
        execution_info = {
            "id": execution_id,
            "sequence_id": action_sequence.id,
            "status": ActionSequenceStatus.IN_PROGRESS,
            "steps_total": len(action_sequence.sequence),
            "steps_completed": 0,
            "steps_failed": 0,
            "current_step": 0,
            "start_time": start_time,
            "results": [],
            "errors": [],
            "recovery_attempts": [],
            "context": context or {}
        }
        
        self.active_executions[execution_id] = execution_info
        
        try:
            # Execute sequence with potential recovery
            success = await self._execute_with_recovery(action_sequence, execution_info, context)
            
            execution_info["status"] = ActionSequenceStatus.COMPLETED if success else ActionSequenceStatus.FAILED
            execution_info["end_time"] = datetime.now()
            execution_info["execution_time"] = (execution_info["end_time"] - start_time).total_seconds()
            
            self._add_to_execution_history(execution_info)
            
            return {
                "execution_id": execution_id,
                "success": success,
                "steps_executed": len(execution_info["results"]),
                "steps_failed": execution_info["steps_failed"],
                "results": execution_info["results"],
                "errors": execution_info["errors"],
                "recovery_attempts": execution_info["recovery_attempts"],
                "timestamp": execution_info["end_time"],
                "execution_time": execution_info["execution_time"]
            }
            
        except Exception as e:
            error_msg = f"Error executing action sequence: {str(e)}"
            execution_info["status"] = ActionSequenceStatus.FAILED
            execution_info["end_time"] = datetime.now()
            execution_info["execution_time"] = (execution_info["end_time"] - start_time).total_seconds()
            execution_info["errors"].append(error_msg)
            
            self._add_to_execution_history(execution_info)
            
            return {
                "execution_id": execution_id,
                "success": False,
                "error": error_msg,
                "recovery_attempts": execution_info["recovery_attempts"],
                "timestamp": execution_info["end_time"],
                "execution_time": execution_info["execution_time"]
            }
        finally:
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
    
    async def _execute_with_recovery(
        self,
        action_sequence: ActionSequence,
        execution_info: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Execute the sequence with potential error recovery.
        
        :param action_sequence: The sequence of actions to execute
        :param execution_info: Information about the current execution
        :param context: Execution context
        :return: True if successful, False otherwise
        """
        all_successful = True
        
        for i, action_step in enumerate(action_sequence.sequence):
            execution_info["current_step"] = i
            
            # Execute the step
            step_result = await self._execute_single_step(action_step, execution_info, context)
            execution_info["results"].append(step_result)
            
            if step_result["success"]:
                execution_info["steps_completed"] += 1
                print(f"Step {i+1}/{len(action_sequence.sequence)} completed successfully: {action_step.action_type.value}")
            else:
                execution_info["steps_failed"] += 1
                all_successful = False
                
                print(f"Step {i+1}/{len(action_sequence.sequence)} failed: {action_step.action_type.value}")
                
                if self.enable_error_recovery:
                    recovery_result = await self._attempt_recovery(
                        action_step, step_result, execution_info, i, action_sequence
                    )
                    
                    if recovery_result["recovered"]:
                        execution_info["recovery_attempts"].append(recovery_result)
                        # After recovery, we may or may not retry the failed step
                        if recovery_result.get("re_execute_step", False):
                            # Retry the step after recovery
                            re_step_result = await self._execute_single_step(action_step, execution_info, context)
                            execution_info["results"][-1] = re_step_result  # Replace the failed result
                            
                            if re_step_result["success"]:
                                execution_info["steps_completed"] += 1
                                execution_info["steps_failed"] -= 1
                                all_successful = all(
                                    res["success"] for res in execution_info["results"]
                                )
                
                if not self.continue_on_failure:
                    print("Stopping execution after failure and potential recovery")
                    break
                else:
                    print("Continuing execution despite failure and potential recovery")
        
        return all_successful
    
    async def _attempt_recovery(
        self,
        failed_step: ActionStep,
        step_result: Dict[str, Any],
        execution_info: Dict[str, Any],
        step_index: int,
        sequence: ActionSequence
    ) -> Dict[str, Any]:
        """
        Attempt to recover from a failed step.
        
        :param failed_step: The step that failed
        :param step_result: Result of the failed step
        :param execution_info: Information about the current execution
        :param step_index: Index of the failed step
        :param sequence: The full action sequence
        :return: Recovery attempt result
        """
        error_details = step_result.get("error", "Unknown error")
        
        # Determine the appropriate recovery strategy
        recovery_strategy = self.error_recovery.determine_recovery_strategy(
            ErrorType.EXECUTION_ERROR,
            failed_step.action_type.value,
            error_details
        )
        
        try:
            if recovery_strategy == RecoveryStrategy.RETRY.value:
                # For RETRY, we'll just re-execute the next time around
                return {
                    "recovered": True,
                    "strategy": "retry",
                    "re_execute_step": True,
                    "message": "Planned to retry failed step"
                }
            elif recovery_strategy == RecoveryStrategy.SKIP.value:
                # For SKIP, we just continue to the next step
                return {
                    "recovered": True,
                    "strategy": "skip",
                    "re_execute_step": False,
                    "message": "Skipped failed step"
                }
            elif recovery_strategy == RecoveryStrategy.REPLAN.value:
                # For REPLAN, we might modify the remaining plan
                recovery_result = await self._replan_remaining_steps(
                    step_index, sequence, execution_info
                )
                
                return {
                    "recovered": recovery_result["success"],
                    "strategy": "replan",
                    "re_execute_step": False,
                    "message": f"Replanning from step {step_index}: {recovery_result.get('message', '')}",
                    "new_plan": recovery_result.get("new_plan")
                }
            elif recovery_strategy == RecoveryStrategy.FALLBACK.value:
                # Execute a fallback action
                fallback_result = await self._execute_fallback_action(failed_step, execution_info)
                
                return {
                    "recovered": fallback_result["success"],
                    "strategy": "fallback",
                    "re_execute_step": False,
                    "message": f"Fallback action executed: {fallback_result.get('message', '')}"
                }
            else:
                # Default: no recovery
                return {
                    "recovered": False,
                    "strategy": "none",
                    "re_execute_step": False,
                    "message": "No applicable recovery strategy found"
                }
                
        except Exception as e:
            print(f"Error during recovery attempt: {str(e)}")
            return {
                "recovered": False,
                "strategy": "error",
                "message": f"Error during recovery: {str(e)}"
            }
    
    async def _replan_remaining_steps(
        self,
        failed_at_index: int,
        original_sequence: ActionSequence,
        execution_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Replan the remaining steps after a failure.
        
        :param failed_at_index: Index where the failure occurred
        :param original_sequence: Original action sequence
        :param execution_info: Information about the current execution
        :return: Result of replanning attempt
        """
        # In a real implementation, this would use a planner to create a new sequence
        # that accounts for the failure and achieves the remaining goals
        # For this example, we'll just return a success indicator
        
        return {
            "success": True,
            "message": f"Replanning conceptually applied from step {failed_at_index}",
            "new_plan": original_sequence.sequence[failed_at_index+1:]  # Conceptual remaining steps
        }
    
    async def _execute_fallback_action(
        self,
        failed_step: ActionStep,
        execution_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a fallback action based on the failed step.
        
        :param failed_step: The step that failed
        :param execution_info: Information about the current execution
        :return: Result of fallback action execution
        """
        # Determine a fallback action based on the failed step's type
        fallback_action_type = failed_step.action_type
        fallback_params = failed_step.parameters
        
        # For navigation failures, could try an alternative path
        if failed_step.action_type == ActionType.NAVIGATION:
            # In a real implementation, calculate an alternative route
            fallback_params = {**failed_step.parameters, "use_alternative_route": True}
        # For manipulation failures, could try different grasp
        elif failed_step.action_type == ActionType.MANIPULATION:
            # In a real implementation, try a different grasp approach
            fallback_params = {**failed_step.parameters, "grasp_type": "alternative"}
        # For perception failures, could try different sensor
        elif failed_step.action_type == ActionType.PERCEPTION:
            # In a real implementation, try with different sensor or settings
            fallback_params = {**failed_step.parameters, "sensor_mode": "alternative"}
        
        try:
            fallback_step = ActionStep(
                id=f"fb_{failed_step.id}",
                action_sequence_id=failed_step.action_sequence_id,
                action_type=fallback_action_type,
                parameters=fallback_params,
                timeout=failed_step.timeout,
                order=failed_step.order
            )
            
            # Execute the fallback step
            fallback_result = await self._execute_single_step(fallback_step, execution_info, execution_info.get("context"))
            
            return {
                "success": fallback_result["success"],
                "message": f"Fallback action {fallback_action_type.value} executed",
                "result": fallback_result
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error in fallback action: {str(e)}"
            }
    
    async def optimize_action_sequence(
        self,
        action_sequence: ActionSequence
    ) -> ActionSequence:
        """
        Optimize an action sequence for better execution.
        
        :param action_sequence: Original action sequence to optimize
        :return: Optimized action sequence
        """
        if not self.enable_optimization or not self.optimizer_enabled:
            return action_sequence
        
        try:
            # Apply optimizations based on learned patterns or rules
            optimized_steps = list(action_sequence.sequence)
            
            # Example optimization: combine similar sequential actions
            optimized_steps = self._combine_similar_actions(optimized_steps)
            
            # Example optimization: reorder steps where possible
            optimized_steps = await self._reorder_for_efficiency(optimized_steps)
            
            # Create new optimized sequence
            optimized_sequence = ActionSequence(
                id=f"opt_{action_sequence.id}",
                voice_command_id=action_sequence.voice_command_id,
                sequence=optimized_steps,
                description=f"Optimized: {action_sequence.description}",
                status=ActionSequenceStatus.PENDING
            )
            
            return optimized_sequence
            
        except Exception as e:
            print(f"Error optimizing action sequence: {str(e)}")
            # Return original if optimization fails
            return action_sequence
    
    def _combine_similar_actions(self, steps: List[ActionStep]) -> List[ActionStep]:
        """
        Combine similar sequential actions to reduce execution time.
        
        :param steps: Original list of action steps
        :return: Optimized list of action steps
        """
        if not steps:
            return []
        
        optimized = [steps[0]]  # Start with first step
        
        for step in steps[1:]:
            last_optimized = optimized[-1]
            
            # Check if current step can be combined with the last optimized step
            if (step.action_type == last_optimized.action_type and 
                self._are_actions_combinable(last_optimized, step)):
                
                # Combine the actions
                combined_step = self._combine_two_actions(last_optimized, step)
                optimized[-1] = combined_step
            else:
                # Add as a new separate step
                optimized.append(step)
        
        # Update step orders
        for i, step in enumerate(optimized):
            step.order = i
        
        return optimized
    
    def _are_actions_combinable(self, step1: ActionStep, step2: ActionStep) -> bool:
        """
        Determine if two actions can be combined.
        
        :param step1: First action step
        :param step2: Second action step
        :return: True if combinable, False otherwise
        """
        # In a real implementation, this would have more sophisticated logic
        # For now, we'll say navigation steps with similar parameters can be combined
        if step1.action_type == ActionType.NAVIGATION and step2.action_type == ActionType.NAVIGATION:
            # Two navigation steps can be combined if they're part of a path
            # This is a simplified check
            return True
        
        return False
    
    def _combine_two_actions(self, step1: ActionStep, step2: ActionStep) -> ActionStep:
        """
        Combine two actions into a single action.
        
        :param step1: First action step
        :param step2: Second action step
        :return: Combined action step
        """
        # For this example, we'll return the second step with adjusted parameters
        # In a real implementation, this would create a truly combined action
        combined_params = {**step1.parameters, **step2.parameters}
        
        return ActionStep(
            id=f"cmb_{step1.id}_{step2.id}",
            action_sequence_id=step1.action_sequence_id,
            action_type=step1.action_type,
            parameters=combined_params,
            timeout=max(step1.timeout, step2.timeout),
            order=step1.order
        )
    
    async def _reorder_for_efficiency(self, steps: List[ActionStep]) -> List[ActionStep]:
        """
        Reorder actions to improve efficiency where dependencies allow.
        
        :param steps: Original list of action steps
        :return: Reordered list of action steps
        """
        # In a real implementation, this would analyze dependencies
        # and try to run independent actions in parallel or reorder for efficiency
        # For this example, we'll just return the original order
        return steps


# Example usage:
if __name__ == "__main__":
    import asyncio
    
    async def example():
        # Create the multi-step execution service
        executor = MultiStepExecutionService()
        
        # Create an example action sequence
        from ..models.action_step import ActionStep, ActionType
        
        action_sequence = ActionSequence(
            id="seq_123",
            voice_command_id="cmd_456",
            sequence=[
                ActionStep(
                    id="step_1",
                    action_sequence_id="seq_123",
                    action_type=ActionType.NAVIGATION,
                    parameters={"x": 1.0, "y": 1.0, "z": 0.0},
                    timeout=10,
                    order=0
                ),
                ActionStep(
                    id="step_2",
                    action_sequence_id="seq_123",
                    action_type=ActionType.PERCEPTION,
                    parameters={"action": "detect", "target": "cup"},
                    timeout=5,
                    order=1
                ),
                ActionStep(
                    id="step_3",
                    action_sequence_id="seq_123",
                    action_type=ActionType.MANIPULATION,
                    parameters={"action": "grasp", "object_id": "cup_1"},
                    timeout=15,
                    order=2
                )
            ],
            description="Example sequence: navigate, detect, grasp",
            status=ActionSequenceStatus.PENDING
        )
        
        print("Executing action sequence...")
        result = await executor.execute_action_sequence(action_sequence)
        
        print(f"Execution result: {result}")
        
        # Get execution statistics
        stats = await executor.get_execution_statistics()
        print(f"Execution statistics: {stats}")
    
    # Run the example
    # asyncio.run(example())
    
    # Example with advanced service
    async def advanced_example():
        advanced_executor = AdvancedMultiStepExecutionService()
        
        # Create an example action sequence
        action_sequence = ActionSequence(
            id="adv_seq_123",
            voice_command_id="cmd_456",
            sequence=[
                ActionStep(
                    id="step_1",
                    action_sequence_id="adv_seq_123",
                    action_type=ActionType.NAVIGATION,
                    parameters={"x": 1.0, "y": 1.0, "z": 0.0},
                    timeout=10,
                    order=0
                ),
                ActionStep(
                    id="step_2",
                    action_sequence_id="adv_seq_123",
                    action_type=ActionType.MANIPULATION,
                    parameters={"action": "grasp", "object_id": "cup_1"},
                    timeout=15,
                    order=1
                )
            ],
            description="Advanced example sequence",
            status=ActionSequenceStatus.PENDING
        )
        
        # Optimize the sequence first
        optimized_sequence = await advanced_executor.optimize_action_sequence(action_sequence)
        print(f"Original sequence had {len(action_sequence.sequence)} steps")
        print(f"Optimized sequence has {len(optimized_sequence.sequence)} steps")
        
        # Execute with recovery capabilities
        result = await advanced_executor.execute_action_sequence_with_recovery(optimized_sequence)
        print(f"Advanced execution result: {result}")
    
    # Run the advanced example
    # asyncio.run(advanced_example())