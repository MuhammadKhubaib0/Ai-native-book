"""
Service for handling and recovering from errors in LLM-generated action sequences.
"""
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from ..models.action_step import ActionStep, ActionType
from ..models.action_sequence import ActionSequence, ActionSequenceStatus
from ..models.voice_command import VoiceCommand
import uuid
from datetime import datetime


class ErrorType(Enum):
    """Enumeration of different error types."""
    VALIDATION_ERROR = "validation_error"
    EXECUTION_ERROR = "execution_error"
    LLM_GENERATION_ERROR = "llm_generation_error"
    ROBOT_CAPABILITY_ERROR = "robot_capability_error"
    ENVIRONMENT_ERROR = "environment_error"
    TIMEOUT_ERROR = "timeout_error"
    SAFETY_ERROR = "safety_error"


class RecoveryStrategy(Enum):
    """Enumeration of different recovery strategies."""
    RETRY = "retry"
    SKIP = "skip"
    REPLAN = "replan"
    FALLBACK = "fallback"
    ABORT = "abort"
    HUMAN_INTERVENTION = "human_intervention"


class ErrorRecoveryService:
    """
    Service for handling and recovering from errors in LLM-generated action sequences.
    """
    
    def __init__(self, default_strategy: RecoveryStrategy = RecoveryStrategy.REPLAN):
        """
        Initialize the error recovery service.
        
        :param default_strategy: Default strategy to use when no specific recovery is defined
        """
        self.default_strategy = default_strategy
        self.recovery_strategies = self._initialize_strategies()
        self.error_history = []  # Keep track of errors for learning
    
    def _initialize_strategies(self) -> Dict[ErrorType, RecoveryStrategy]:
        """
        Initialize default recovery strategies for each error type.
        
        :return: Dictionary mapping error types to recovery strategies
        """
        return {
            ErrorType.VALIDATION_ERROR: RecoveryStrategy.REPLAN,
            ErrorType.EXECUTION_ERROR: RecoveryStrategy.SKIP,
            ErrorType.LLM_GENERATION_ERROR: RecoveryStrategy.RETRY,
            ErrorType.ROBOT_CAPABILITY_ERROR: RecoveryStrategy.REPLAN,
            ErrorType.ENVIRONMENT_ERROR: RecoveryStrategy.REPLAN,
            ErrorType.TIMEOUT_ERROR: RecoveryStrategy.SKIP,
            ErrorType.SAFETY_ERROR: RecoveryStrategy.ABORT
        }
    
    def handle_error(
        self, 
        error_type: ErrorType, 
        action_sequence: ActionSequence,
        failed_step: Optional[ActionStep] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle an error in an action sequence and provide recovery guidance.
        
        :param error_type: Type of error that occurred
        :param action_sequence: The action sequence where the error occurred
        :param failed_step: The specific step that failed (optional)
        :param error_details: Additional details about the error (optional)
        :return: Dictionary with recovery guidance
        """
        # Record the error in history
        self._record_error(error_type, action_sequence, failed_step, error_details)
        
        # Determine the appropriate recovery strategy
        strategy = self._get_recovery_strategy(error_type)
        
        # Apply the recovery strategy
        recovery_result = self._apply_recovery_strategy(
            strategy, 
            action_sequence, 
            failed_step, 
            error_details
        )
        
        return {
            "strategy": strategy.value,
            "action_sequence": action_sequence,
            "recovery_result": recovery_result,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_recovery_strategy(self, error_type: ErrorType) -> RecoveryStrategy:
        """
        Get the appropriate recovery strategy for a given error type.
        
        :param error_type: Type of error
        :return: Recommended recovery strategy
        """
        return self.recovery_strategies.get(error_type, self.default_strategy)
    
    def _apply_recovery_strategy(
        self,
        strategy: RecoveryStrategy,
        action_sequence: ActionSequence,
        failed_step: Optional[ActionStep] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Apply a specific recovery strategy.
        
        :param strategy: The recovery strategy to apply
        :param action_sequence: The action sequence being recovered
        :param failed_step: The step that failed (optional)
        :param error_details: Additional error details (optional)
        :return: Result of the recovery attempt
        """
        if strategy == RecoveryStrategy.RETRY:
            return self._handle_retry(action_sequence, failed_step)
        elif strategy == RecoveryStrategy.SKIP:
            return self._handle_skip(action_sequence, failed_step)
        elif strategy == RecoveryStrategy.REPLAN:
            return self._handle_replan(action_sequence, failed_step, error_details)
        elif strategy == RecoveryStrategy.FALLBACK:
            return self._handle_fallback(action_sequence, failed_step)
        elif strategy == RecoveryStrategy.ABORT:
            return self._handle_abort(action_sequence)
        elif strategy == RecoveryStrategy.HUMAN_INTERVENTION:
            return self._handle_human_intervention(action_sequence, failed_step)
        else:
            # Default to abort if unknown strategy
            return self._handle_abort(action_sequence)
    
    def _handle_retry(
        self, 
        action_sequence: ActionSequence, 
        failed_step: Optional[ActionStep] = None
    ) -> Dict[str, Any]:
        """
        Handle retrying a failed action.
        
        :param action_sequence: The action sequence
        :param failed_step: The step that failed (optional)
        :return: Retry result
        """
        return {
            "action": "retry",
            "target_step": failed_step.id if failed_step else None,
            "message": f"Retrying {'specific step' if failed_step else 'entire sequence'}"
        }
    
    def _handle_skip(
        self, 
        action_sequence: ActionSequence, 
        failed_step: Optional[ActionStep] = None
    ) -> Dict[str, Any]:
        """
        Handle skipping a failed action.
        
        :param action_sequence: The action sequence
        :param failed_step: The step that failed (optional)
        :return: Skip result
        """
        if failed_step:
            # Mark the step as skipped in the sequence
            for step in action_sequence.sequence:
                if step.id == failed_step.id:
                    step.parameters["_skipped"] = True
                    break
        
        return {
            "action": "skip",
            "target_step": failed_step.id if failed_step else None,
            "message": f"Skipping {'specific step' if failed_step else 'current action'} and continuing"
        }
    
    def _handle_replan(
        self,
        action_sequence: ActionSequence,
        failed_step: Optional[ActionStep] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle replanning the action sequence around the failure.
        
        :param action_sequence: The action sequence
        :param failed_step: The step that failed (optional)
        :param error_details: Additional error details (optional)
        :return: Replan result
        """
        # In a real implementation, this would call the LLM to generate a new plan
        # For this example, we'll return a placeholder result
        return {
            "action": "replan",
            "new_sequence_id": str(uuid.uuid4()),
            "message": f"Generating new plan to achieve goal while avoiding {'the failure at step ' + str(failed_step.id) if failed_step else 'the previous failure'}",
            "error_context": error_details
        }
    
    def _handle_fallback(
        self, 
        action_sequence: ActionSequence, 
        failed_step: Optional[ActionStep] = None
    ) -> Dict[str, Any]:
        """
        Handle falling back to a simpler or safer action.
        
        :param action_sequence: The action sequence
        :param failed_step: The step that failed (optional)
        :return: Fallback result
        """
        fallback_action = None
        
        if failed_step:
            # Create a fallback action based on the failed action type
            if failed_step.action_type == ActionType.NAVIGATION:
                fallback_action = ActionStep(
                    id=str(uuid.uuid4()),
                    action_sequence_id=action_sequence.id,
                    action_type=ActionType.OTHER,
                    parameters={"action": "return_to_home", "reason": "navigation_failed"},
                    timeout=30,
                    order=failed_step.order
                )
            elif failed_step.action_type == ActionType.MANIPULATION:
                fallback_action = ActionStep(
                    id=str(uuid.uuid4()),
                    action_sequence_id=action_sequence.id,
                    action_type=ActionType.OTHER,
                    parameters={"action": "safe_position", "reason": "manipulation_failed"},
                    timeout=10,
                    order=failed_step.order
                )
        
        return {
            "action": "fallback",
            "fallback_action": fallback_action,
            "message": f"Falling back to safer operation after {'step ' + str(failed_step.id) if failed_step else 'failure'}"
        }
    
    def _handle_abort(self, action_sequence: ActionSequence) -> Dict[str, Any]:
        """
        Handle aborting the action sequence.
        
        :param action_sequence: The action sequence to abort
        :return: Abort result
        """
        # Update the sequence status to failed
        action_sequence.status = ActionSequenceStatus.FAILED
        
        return {
            "action": "abort",
            "message": "Aborting action sequence due to unrecoverable error"
        }
    
    def _handle_human_intervention(
        self, 
        action_sequence: ActionSequence, 
        failed_step: Optional[ActionStep] = None
    ) -> Dict[str, Any]:
        """
        Handle requesting human intervention.
        
        :param action_sequence: The action sequence
        :param failed_step: The step that failed (optional)
        :return: Human intervention result
        """
        return {
            "action": "human_intervention",
            "message": f"Requesting human assistance for {'step ' + str(failed_step.id) if failed_step else 'current situation'}",
            "sequence_state": action_sequence.status.value
        }
    
    def _record_error(
        self, 
        error_type: ErrorType, 
        action_sequence: ActionSequence,
        failed_step: Optional[ActionStep],
        error_details: Optional[Dict[str, Any]]
    ):
        """
        Record error information for future learning.
        
        :param error_type: Type of error
        :param action_sequence: The action sequence where error occurred
        :param failed_step: The step that failed (optional)
        :param error_details: Additional error details (optional)
        """
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type.value,
            "action_sequence_id": action_sequence.id,
            "failed_step_id": failed_step.id if failed_step else None,
            "error_details": error_details or {},
            "context": {
                "voice_command_id": action_sequence.voice_command_id,
                "sequence_description": action_sequence.description
            }
        }
        
        self.error_history.append(error_record)
    
    def update_recovery_strategy(self, error_type: ErrorType, strategy: RecoveryStrategy):
        """
        Update the recovery strategy for a specific error type.
        
        :param error_type: The error type to update
        :param strategy: The new recovery strategy
        """
        self.recovery_strategies[error_type] = strategy
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about errors handled by this service.
        
        :return: Dictionary with error statistics
        """
        if not self.error_history:
            return {"message": "No errors recorded yet"}
        
        error_counts = {}
        for record in self.error_history:
            error_type = record["error_type"]
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "error_counts": error_counts,
            "most_common_error": max(error_counts, key=error_counts.get)
        }


class AdvancedErrorRecoveryService(ErrorRecoveryService):
    """
    Advanced error recovery service with machine learning-based strategy selection.
    """
    
    def __init__(self, default_strategy: RecoveryStrategy = RecoveryStrategy.REPLAN):
        super().__init__(default_strategy)
        self.learning_enabled = True
        self.successful_recoveries = []
    
    def handle_error_with_learning(
        self, 
        error_type: ErrorType, 
        action_sequence: ActionSequence,
        failed_step: Optional[ActionStep] = None,
        error_details: Optional[Dict[str, Any]] = None,
        previous_strategy: Optional[RecoveryStrategy] = None,
        recovery_successful: bool = False
    ) -> Dict[str, Any]:
        """
        Handle an error with the option to learn from the recovery outcome.
        
        :param error_type: Type of error that occurred
        :param action_sequence: The action sequence where the error occurred
        :param failed_step: The specific step that failed (optional)
        :param error_details: Additional details about the error (optional)
        :param previous_strategy: The strategy used in a previous recovery attempt (optional)
        :param recovery_successful: Whether the previous recovery was successful (optional)
        :return: Dictionary with recovery guidance
        """
        # If a previous recovery attempt was made, update our learning
        if previous_strategy is not None and recovery_successful is not None:
            self._record_recovery_outcome(error_type, previous_strategy, recovery_successful)
        
        # Determine the most effective strategy based on past performance
        strategy = self._get_adaptive_strategy(error_type, action_sequence, failed_step)
        
        # Apply the recovery strategy
        recovery_result = self._apply_recovery_strategy(
            strategy, 
            action_sequence, 
            failed_step, 
            error_details
        )
        
        return {
            "strategy": strategy.value,
            "action_sequence": action_sequence,
            "recovery_result": recovery_result,
            "timestamp": datetime.now().isoformat(),
            "learning_updated": previous_strategy is not None
        }
    
    def _get_adaptive_strategy(self, error_type: ErrorType, action_sequence: ActionSequence, failed_step: Optional[ActionStep]) -> RecoveryStrategy:
        """
        Get the most effective strategy based on past performance for this error type.
        
        :param error_type: Type of error
        :param action_sequence: The action sequence in context
        :param failed_step: The step that failed
        :return: Most effective recovery strategy
        """
        if not self.learning_enabled:
            return self._get_recovery_strategy(error_type)
        
        # For this implementation, we'll return the default strategy for the error type
        # In a full implementation, this would analyze recovery statistics and select
        # the strategy with the highest success rate for this error type
        return self._get_recovery_strategy(error_type)
    
    def _record_recovery_outcome(
        self, 
        error_type: ErrorType, 
        strategy: RecoveryStrategy, 
        successful: bool
    ):
        """
        Record the outcome of a recovery attempt for learning purposes.
        
        :param error_type: Type of error
        :param strategy: Strategy that was used
        :param successful: Whether the recovery was successful
        """
        recovery_record = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type.value,
            "strategy": strategy.value,
            "successful": successful
        }
        
        self.successful_recoveries.append(recovery_record)
    
    def get_recovery_effectiveness(self) -> Dict[str, Any]:
        """
        Get statistics about the effectiveness of different recovery strategies.
        
        :return: Dictionary with recovery effectiveness statistics
        """
        if not self.successful_recoveries:
            return {"message": "No recovery outcomes recorded yet"}
        
        # Group outcomes by strategy and error type
        strategy_stats = {}
        error_stats = {}
        
        for record in self.successful_recoveries:
            strategy = record["strategy"]
            error_type = record["error_type"]
            successful = record["successful"]
            
            # Update strategy stats
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {"attempts": 0, "successes": 0}
            strategy_stats[strategy]["attempts"] += 1
            if successful:
                strategy_stats[strategy]["successes"] += 1
            
            # Update error type stats
            if error_type not in error_stats:
                error_stats[error_type] = {"attempts": 0, "successes": 0}
            error_stats[error_type]["attempts"] += 1
            if successful:
                error_stats[error_type]["successes"] += 1
        
        # Calculate success rates
        for stats in [strategy_stats, error_stats]:
            for key in stats:
                attempts = stats[key]["attempts"]
                successes = stats[key]["successes"]
                stats[key]["success_rate"] = round(successes / attempts * 100, 2) if attempts > 0 else 0
        
        return {
            "total_recovery_attempts": len(self.successful_recoveries),
            "strategy_effectiveness": strategy_stats,
            "error_type_resolutions": error_stats
        }


# Example usage:
if __name__ == "__main__":
    # Create an error recovery service
    recovery_service = ErrorRecoveryService(default_strategy=RecoveryStrategy.REPLAN)
    
    # Create a sample action sequence with a failure
    from ..models.action_step import ActionStep, ActionType
    from ..models.action_sequence import ActionSequence, ActionSequenceStatus
    import uuid
    
    action_steps = [
        ActionStep(
            id=str(uuid.uuid4()),
            action_sequence_id="seq-123",
            action_type=ActionType.NAVIGATION,
            parameters={"x": 1.0, "y": 2.0},
            timeout=10,
            order=0
        ),
        ActionStep(
            id=str(uuid.uuid4()),
            action_sequence_id="seq-123",
            action_type=ActionType.MANIPULATION,
            parameters={"action": "grasp", "object": "cup"},
            timeout=15,
            order=1
        )
    ]
    
    action_seq = ActionSequence(
        id="seq-123",
        voice_command_id="cmd-456",
        sequence=action_steps,
        description="Test sequence with failure",
        status=ActionSequenceStatus.IN_PROGRESS
    )
    
    # Define a failed step
    failed_step = action_steps[1]  # The manipulation step fails
    
    # Simulate an execution error
    error_details = {
        "original_error": "Object not found at expected location",
        "recovery_context": "Object detection failed, possibly moved"
    }
    
    # Handle the error
    recovery_result = recovery_service.handle_error(
        error_type=ErrorType.EXECUTION_ERROR,
        action_sequence=action_seq,
        failed_step=failed_step,
        error_details=error_details
    )
    
    print("Error Recovery Result:")
    print(f"Strategy: {recovery_result['strategy']}")
    print(f"Action: {recovery_result['recovery_result']['action']}")
    print(f"Message: {recovery_result['recovery_result']['message']}")
    
    # Update strategy for a specific error type
    recovery_service.update_recovery_strategy(
        ErrorType.EXECUTION_ERROR,
        RecoveryStrategy.REPLAN
    )
    
    print(f"\nError Statistics: {recovery_service.get_error_statistics()}")
    
    # Example with advanced recovery service
    advanced_service = AdvancedErrorRecoveryService(default_strategy=RecoveryStrategy.REPLAN)
    
    # Record some sample recovery outcomes for learning
    advanced_service._record_recovery_outcome(ErrorType.EXECUTION_ERROR, RecoveryStrategy.RETRY, True)
    advanced_service._record_recovery_outcome(ErrorType.EXECUTION_ERROR, RecoveryStrategy.RETRY, False)
    advanced_service._record_recovery_outcome(ErrorType.EXECUTION_ERROR, RecoveryStrategy.REPLAN, True)
    advanced_service._record_recovery_outcome(ErrorType.EXECUTION_ERROR, RecoveryStrategy.REPLAN, True)
    
    # Get recovery effectiveness
    effectiveness = advanced_service.get_recovery_effectiveness()
    print(f"\nRecovery Effectiveness: {effectiveness}")