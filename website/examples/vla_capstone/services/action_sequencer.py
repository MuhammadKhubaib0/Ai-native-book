"""
Service for sequencing LLM-generated actions into executable robot command sequences.
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
from ..models.action_step import ActionStep, ActionType
from ..models.action_sequence import ActionSequence, ActionSequenceStatus
from ..models.voice_command import VoiceCommand
from ..validation.voice_command_validation import validate_action_step_compatibility
import uuid


class ActionSequencingStrategy(Enum):
    """Enumeration of different action sequencing strategies."""
    LINEAR = "linear"
    PARALLELIZABLE = "parallelizable"
    CONDITIONAL = "conditional"
    HIERARCHICAL = "hierarchical"


class ActionSequencer:
    """
    Service for sequencing LLM-generated actions into well-formed, executable action sequences.
    """
    
    def __init__(self, robot_capabilities: List[str] = None):
        """
        Initialize the action sequencer.
        
        :param robot_capabilities: List of capabilities the robot supports
        """
        self.robot_capabilities = robot_capabilities or [
            "navigation", "manipulation", "perception", "interaction"
        ]
    
    def sequence_actions(
        self, 
        actions: List[Dict[str, Any]], 
        voice_command: Optional[VoiceCommand] = None,
        strategy: ActionSequencingStrategy = ActionSequencingStrategy.LINEAR
    ) -> ActionSequence:
        """
        Sequence a list of actions into an executable action sequence.
        
        :param actions: List of action dictionaries from LLM
        :param voice_command: Associated voice command (optional)
        :param strategy: Strategy to use for sequencing
        :return: Sequenced ActionSequence object
        """
        # Convert action dictionaries to ActionStep objects
        action_steps = self._convert_to_action_steps(actions)
        
        # Validate steps for robot compatibility
        if voice_command:
            validation_result = validate_action_step_compatibility(
                ActionSequence(
                    id="temp",
                    voice_command_id=voice_command.id,
                    sequence=action_steps,
                    description=""
                ),
                self.robot_capabilities
            )
            
            if not validation_result.is_valid:
                # Filter out incompatible actions or raise an exception
                # For this implementation, we'll just log the errors
                print(f"Warning: Some actions may not be compatible: {validation_result.errors}")
        
        # Apply sequencing strategy
        if strategy == ActionSequencingStrategy.LINEAR:
            sequenced_steps = self._apply_linear_strategy(action_steps)
        elif strategy == ActionSequencingStrategy.PARALLELIZABLE:
            sequenced_steps = self._apply_parallelizable_strategy(action_steps)
        elif strategy == ActionSequencingStrategy.CONDITIONAL:
            sequenced_steps = self._apply_conditional_strategy(action_steps)
        elif strategy == ActionSequencingStrategy.HIERARCHICAL:
            sequenced_steps = self._apply_hierarchical_strategy(action_steps)
        else:
            sequenced_steps = action_steps  # Default to no special strategy
        
        # Create action sequence
        sequence_id = str(uuid.uuid4())
        voice_command_id = voice_command.id if voice_command else ""
        
        action_sequence = ActionSequence(
            id=sequence_id,
            voice_command_id=voice_command_id,
            sequence=sequenced_steps,
            description=self._create_description(actions, voice_command),
            status=ActionSequenceStatus.PENDING
        )
        
        return action_sequence
    
    def _convert_to_action_steps(self, actions: List[Dict[str, Any]]) -> List[ActionStep]:
        """
        Convert a list of action dictionaries to ActionStep objects.
        
        :param actions: List of action dictionaries
        :return: List of ActionStep objects
        """
        action_steps = []
        
        for i, action_dict in enumerate(actions):
            # Extract required fields with defaults
            action_id = action_dict.get('id', str(uuid.uuid4()))
            action_type_str = action_dict.get('action_type', 'other').upper()
            
            # Handle different possible formats for action_type
            try:
                action_type = ActionType[action_type_str]
            except KeyError:
                # If the action type is not in our enum, default to OTHER
                action_type = ActionType.OTHER
            
            parameters = action_dict.get('parameters', {})
            timeout = action_dict.get('timeout', 10)  # Default timeout
            order = action_dict.get('order', i)  # Default to order of appearance
            
            action_step = ActionStep(
                id=action_id,
                action_sequence_id="",  # Will be set when added to sequence
                action_type=action_type,
                parameters=parameters,
                timeout=timeout,
                order=order
            )
            
            action_steps.append(action_step)
        
        # Sort by order to ensure correct sequence
        action_steps.sort(key=lambda x: x.order)
        
        return action_steps
    
    def _apply_linear_strategy(self, action_steps: List[ActionStep]) -> List[ActionStep]:
        """
        Apply linear sequencing strategy where actions are executed in order.
        
        :param action_steps: List of action steps to sequence
        :return: Sequenced action steps
        """
        # Linear strategy just ensures proper ordering
        # The ordering is already handled in _convert_to_action_steps
        return action_steps
    
    def _apply_parallelizable_strategy(self, action_steps: List[ActionStep]) -> List[ActionStep]:
        """
        Apply parallelizable strategy where possible independent actions are identified.
        
        :param action_steps: List of action steps to sequence
        :return: Sequenced action steps with parallelization hints
        """
        # For now, we'll just maintain the order but mark which could be parallelized
        # In a real implementation, you would identify independent actions that could run in parallel
        # and group them accordingly
        
        # This is a simplified version that doesn't actually implement parallel execution
        # but could be extended to do so
        return action_steps
    
    def _apply_conditional_strategy(self, action_steps: List[ActionStep]) -> List[ActionStep]:
        """
        Apply conditional strategy where actions may depend on outcomes of previous actions.
        
        :param action_steps: List of action steps to sequence
        :return: Sequenced action steps with conditional logic
        """
        # In a conditional strategy, we might add checks between steps
        # For this implementation, we'll just maintain the order but note it's conditional
        return action_steps
    
    def _apply_hierarchical_strategy(self, action_steps: List[ActionStep]) -> List[ActionStep]:
        """
        Apply hierarchical strategy where actions are grouped into sub-tasks.
        
        :param action_steps: List of action steps to sequence
        :return: Sequenced action steps with hierarchical grouping
        """
        # For hierarchical strategy, we might group related actions
        # This is a simplified implementation
        return action_steps
    
    def _create_description(self, actions: List[Dict[str, Any]], voice_command: Optional[VoiceCommand]) -> str:
        """
        Create a description for the action sequence.
        
        :param actions: List of action dictionaries
        :param voice_command: Associated voice command
        :return: Description string
        """
        if voice_command:
            base_text = voice_command.transcribed_text
        else:
            base_text = "Unspecified action sequence"
        
        return f"Action sequence for: {base_text}"
    
    def validate_sequence(self, action_sequence: ActionSequence) -> bool:
        """
        Validate that the action sequence is properly formed.
        
        :param action_sequence: The action sequence to validate
        :return: True if valid, False otherwise
        """
        # Check if sequence has any steps
        if not action_sequence.sequence:
            return False
        
        # Check if each step has required fields
        for step in action_sequence.sequence:
            if not step.id or not step.action_type or step.timeout <= 0:
                return False
        
        # Additional validation could be added here
        
        return True
    
    def optimize_sequence(self, action_sequence: ActionSequence) -> ActionSequence:
        """
        Optimize an action sequence for efficiency.
        
        :param action_sequence: The action sequence to optimize
        :return: Optimized action sequence
        """
        # This is a placeholder for optimization logic
        # In a real implementation, this could:
        # - Combine similar actions
        # - Reorder for efficiency (while respecting dependencies)
        # - Remove redundant actions
        # - Adjust timeouts based on action complexity
        
        # For now, return the sequence as-is
        return action_sequence


class AdvancedActionSequencer(ActionSequencer):
    """
    Advanced action sequencer with additional optimization and validation features.
    """
    
    def __init__(self, robot_capabilities: List[str] = None, enable_optimization: bool = True):
        super().__init__(robot_capabilities)
        self.enable_optimization = enable_optimization
        
        # Define action compatibility rules
        self.compatibility_rules = {
            # Actions that can be performed in parallel
            "parallelizable_pairs": [
                ("perception", "navigation"),  # Robot can navigate while perceiving
                ("perception", "interaction")  # Robot can interact while perceiving
            ],
            # Actions that should not be performed simultaneously
            "conflicting_pairs": [
                ("navigation", "manipulation"),  # Difficult to manipulate while moving
            ],
            # Actions that require specific preceding actions
            "dependency_rules": {
                "manipulation": ["perception"],  # Should perceive before manipulation
                "navigation": ["perception"]     # Should perceive surroundings before navigating
            }
        }
    
    def sequence_with_optimization(
        self, 
        actions: List[Dict[str, Any]], 
        voice_command: Optional[VoiceCommand] = None,
        strategy: ActionSequencingStrategy = ActionSequencingStrategy.LINEAR
    ) -> ActionSequence:
        """
        Sequence actions with additional optimization.
        
        :param actions: List of action dictionaries from LLM
        :param voice_command: Associated voice command (optional)
        :param strategy: Strategy to use for sequencing
        :return: Optimized sequenced ActionSequence object
        """
        # First, perform basic sequencing
        sequence = self.sequence_actions(actions, voice_command, strategy)
        
        # Apply optimizations if enabled
        if self.enable_optimization:
            sequence = self._optimize_with_rules(sequence)
        
        return sequence
    
    def _optimize_with_rules(self, action_sequence: ActionSequence) -> ActionSequence:
        """
        Apply optimization rules to the action sequence.
        
        :param action_sequence: The action sequence to optimize
        :return: Optimized action sequence
        """
        # Apply dependency rules
        sequence = self._apply_dependency_rules(action_sequence)
        
        # Apply conflict resolution
        sequence = self._resolve_action_conflicts(sequence)
        
        # Apply efficiency optimizations
        sequence = self._apply_efficiency_optimizations(sequence)
        
        return sequence
    
    def _apply_dependency_rules(self, action_sequence: ActionSequence) -> ActionSequence:
        """
        Apply dependency rules to ensure required preceding actions are present.
        
        :param action_sequence: The action sequence to modify
        :return: Modified action sequence with dependencies respected
        """
        # For each action, check if its dependencies are met
        steps = action_sequence.sequence
        new_steps = []
        
        for step in steps:
            # Check if this action has dependencies
            step_type = step.action_type.value if hasattr(step.action_type, 'value') else str(step.action_type).lower()
            
            required_preceding = self.compatibility_rules["dependency_rules"].get(step_type, [])
            preceding_types = [s.action_type.value if hasattr(s.action_type, 'value') else str(s.action_type).lower() for s in new_steps]
            
            for required_type in required_preceding:
                if required_type not in preceding_types:
                    # Add a default perception action if perception is required
                    if required_type == "perception":
                        new_steps.append(ActionStep(
                            id=str(uuid.uuid4()),
                            action_sequence_id=action_sequence.id,
                            action_type=ActionType.PERCEPTION,
                            parameters={"action": "scan_environment", "target": "navigation"},
                            timeout=5,
                            order=0  # This will be adjusted later
                        ))
            
            # Add the original step
            new_steps.append(step)
        
        # Reorder and update orders
        for i, step in enumerate(new_steps):
            step.order = i
        
        action_sequence.sequence = new_steps
        return action_sequence
    
    def _resolve_action_conflicts(self, action_sequence: ActionSequence) -> ActionSequence:
        """
        Resolve conflicts between actions that should not be performed simultaneously.
        
        :param action_sequence: The action sequence to modify
        :return: Modified action sequence with conflicts resolved
        """
        # For now, we'll just ensure conflicting actions are not adjacent
        # In a real implementation, we might need more sophisticated conflict resolution
        steps = action_sequence.sequence
        new_steps = []
        
        for step in steps:
            step_type = step.action_type.value if hasattr(step.action_type, 'value') else str(step.action_type).lower()
            if new_steps:
                prev_step = new_steps[-1]
                prev_type = prev_step.action_type.value if hasattr(prev_step.action_type, 'value') else str(prev_step.action_type).lower()
                
                # Check if this step conflicts with the previous one
                conflict = False
                for conflict_pair in self.compatibility_rules["conflicting_pairs"]:
                    if step_type in conflict_pair and prev_type in conflict_pair:
                        conflict = True
                        break
                
                if conflict:
                    # Add a pause or transition action between conflicting actions
                    new_steps.append(ActionStep(
                        id=str(uuid.uuid4()),
                        action_sequence_id=action_sequence.id,
                        action_type=ActionType.OTHER,
                        parameters={"action": "pause", "duration": 0.5},
                        timeout=1,
                        order=0  # Will be updated later
                    ))
            
            new_steps.append(step)
        
        # Update orders
        for i, step in enumerate(new_steps):
            step.order = i
        
        action_sequence.sequence = new_steps
        return action_sequence
    
    def _apply_efficiency_optimizations(self, action_sequence: ActionSequence) -> ActionSequence:
        """
        Apply efficiency optimizations to the action sequence.
        
        :param action_sequence: The action sequence to optimize
        :return: Optimized action sequence
        """
        # Look for similar consecutive actions that can be combined
        steps = action_sequence.sequence
        if not steps:
            return action_sequence
        
        optimized_steps = [steps[0]]  # Start with the first step
        
        for i in range(1, len(steps)):
            current = steps[i]
            previous = optimized_steps[-1]
            
            # Check if current action can be combined with the previous one
            if (current.action_type == previous.action_type and 
                self._actions_are_combinable(current, previous)):
                # Combine the actions
                combined_params = self._combine_parameters(current.parameters, previous.parameters)
                previous.parameters = combined_params
                # Increase timeout proportionally to account for the combined action
                previous.timeout = max(previous.timeout, current.timeout)
            else:
                # Add as a separate step
                optimized_steps.append(current)
        
        # Update orders
        for i, step in enumerate(optimized_steps):
            step.order = i
        
        action_sequence.sequence = optimized_steps
        return action_sequence
    
    def _actions_are_combinable(self, action1: ActionStep, action2: ActionStep) -> bool:
        """
        Determine if two actions can be combined for efficiency.
        
        :param action1: First action
        :param action2: Second action
        :return: True if actions can be combined, False otherwise
        """
        # Define which action types can potentially be combined
        combinable_types = {ActionType.NAVIGATION, ActionType.INTERACTION}
        
        if action1.action_type not in combinable_types or action2.action_type not in combinable_types:
            return False
        
        # For navigation, check if they're similar movements
        if action1.action_type == ActionType.NAVIGATION and action2.action_type == ActionType.NAVIGATION:
            # Navigation actions might be combinable if they're part of a multi-step path
            return True
        
        # For now, just return false for other comparisons
        # More complex logic can be added based on specific requirements
        return False
    
    def _combine_parameters(self, params1: Dict[str, Any], params2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine parameters from two similar actions.
        
        :param params1: Parameters from first action
        :param params2: Parameters from second action
        :return: Combined parameters
        """
        # This is a simple implementation that just updates params1 with params2
        # More sophisticated combination logic can be added as needed
        combined = params1.copy()
        combined.update(params2)
        return combined


# Example usage:
if __name__ == "__main__":
    # Create an action sequencer
    sequencer = ActionSequencer(robot_capabilities=["navigation", "manipulation", "perception"])
    
    # Example action list from LLM (simulated)
    llm_actions = [
        {
            "id": "step_1",
            "action_type": "navigation",
            "parameters": {"x": 1.0, "y": 2.0, "theta": 0.0},
            "timeout": 10,
            "order": 0
        },
        {
            "id": "step_2",
            "action_type": "perception",
            "parameters": {"object_type": "cup", "action": "detect"},
            "timeout": 5,
            "order": 1
        },
        {
            "id": "step_3",
            "action_type": "manipulation",
            "parameters": {"object_id": "detected_cup", "action": "grasp"},
            "timeout": 15,
            "order": 2
        }
    ]
    
    # Sequence the actions
    sequence = sequencer.sequence_actions(
        actions=llm_actions,
        strategy=ActionSequencingStrategy.LINEAR
    )
    
    print("Action Sequence:")
    print(f"ID: {sequence.id}")
    print(f"Description: {sequence.description}")
    print(f"Status: {sequence.status}")
    print("Steps:")
    for step in sequence.sequence:
        print(f"  - {step.action_type.value}: {step.parameters} (timeout: {step.timeout}s)")
    
    # Validate the sequence
    is_valid = sequencer.validate_sequence(sequence)
    print(f"Sequence is valid: {is_valid}")
    
    # Example with advanced sequencer
    advanced_sequencer = AdvancedActionSequencer(
        robot_capabilities=["navigation", "manipulation", "perception"],
        enable_optimization=True
    )
    
    optimized_sequence = advanced_sequencer.sequence_with_optimization(
        actions=llm_actions,
        strategy=ActionSequencingStrategy.LINEAR
    )
    
    print("\nOptimized Action Sequence:")
    print(f"ID: {optimized_sequence.id}")
    print(f"Description: {optimized_sequence.description}")
    print(f"Status: {optimized_sequence.status}")
    print("Steps:")
    for step in optimized_sequence.sequence:
        print(f"  - {step.action_type.value}: {step.parameters} (timeout: {step.timeout}s)")