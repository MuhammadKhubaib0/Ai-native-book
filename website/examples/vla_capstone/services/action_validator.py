"""
Service for validating action sequences against ROS 2 actions and robot capabilities.
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from ..models.action_step import ActionStep, ActionType
from ..models.action_sequence import ActionSequence
from ..models.voice_command import VoiceCommand


class ValidationResult(Enum):
    """Enumeration of validation results."""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    UNKNOWN = "unknown"


class ValidationIssue:
    """Class representing an issue found during validation."""
    def __init__(self, issue_type: str, message: str, severity: ValidationResult):
        self.issue_type = issue_type
        self.message = message
        self.severity = severity

    def __str__(self):
        return f"[{self.severity.value.upper()}] {self.issue_type}: {self.message}"


class ActionValidator:
    """
    Service for validating action sequences against ROS 2 actions and robot capabilities.
    """
    
    def __init__(self, robot_capabilities: List[str] = None, ros_action_list: List[str] = None):
        """
        Initialize the action validator.
        
        :param robot_capabilities: List of capabilities the robot supports
        :param ros_action_list: List of available ROS 2 actions
        """
        self.robot_capabilities = robot_capabilities or [
            "navigation", "manipulation", "perception", "interaction"
        ]
        self.ros_action_list = ros_action_list or [
            "nav2_msgs/action/NavigateToPose",
            "control_msgs/action/FollowJointTrajectory", 
            "moveit_msgs/action/MoveGroup",
            "sensor_msgs/action/Image"
        ]
        
        # Define parameter requirements for different action types
        self.parameter_requirements = {
            ActionType.NAVIGATION: {
                "required": ["x", "y"],  # Either x,y or target pose is required
                "optional": ["theta", "target_pose", "frame_id"]
            },
            ActionType.MANIPULATION: {
                "required": ["action"],  # At least an action type
                "optional": ["object_id", "position", "orientation", "gripper_position"]
            },
            ActionType.PERCEPTION: {
                "required": ["action"],  # At least an action type
                "optional": ["object_type", "target", "sensor", "frame_id"]
            },
            ActionType.INTERACTION: {
                "required": ["text"],  # At least some text to speak or display
                "optional": ["recipient", "language", "modality"]
            }
        }
    
    def validate_action_sequence(
        self, 
        action_sequence: ActionSequence,
        voice_command: Optional[VoiceCommand] = None
    ) -> List[ValidationIssue]:
        """
        Validate an entire action sequence.
        
        :param action_sequence: The action sequence to validate
        :param voice_command: Associated voice command (optional)
        :return: List of validation issues found
        """
        issues = []
        
        # Validate each action step in the sequence
        for step in action_sequence.sequence:
            step_issues = self.validate_action_step(step)
            issues.extend(step_issues)
        
        # Validate sequence-specific issues
        sequence_issues = self._validate_sequence_properties(action_sequence, voice_command)
        issues.extend(sequence_issues)
        
        return issues
    
    def validate_action_step(self, action_step: ActionStep) -> List[ValidationIssue]:
        """
        Validate a single action step.
        
        :param action_step: The action step to validate
        :return: List of validation issues found
        """
        issues = []
        
        # Check if action type is supported
        action_type_str = action_step.action_type.value if hasattr(action_step.action_type, 'value') else str(action_step.action_type).lower()
        
        if action_type_str not in self.robot_capabilities:
            issues.append(ValidationIssue(
                "capability",
                f"Action type '{action_type_str}' not supported by robot capabilities",
                ValidationResult.INVALID
            ))
        
        # Validate parameters based on action type
        param_issues = self._validate_action_parameters(action_step)
        issues.extend(param_issues)
        
        # Validate timeout
        if action_step.timeout <= 0:
            issues.append(ValidationIssue(
                "timeout",
                f"Action timeout must be positive, got {action_step.timeout}",
                ValidationResult.INVALID
            ))
        
        # Validate parameters against ROS action requirements if applicable
        ros_issues = self._validate_against_ros_actions(action_step)
        issues.extend(ros_issues)
        
        return issues
    
    def _validate_action_parameters(self, action_step: ActionStep) -> List[ValidationIssue]:
        """
        Validate parameters for an action step based on its type.
        
        :param action_step: The action step to validate
        :return: List of validation issues found
        """
        issues = []
        
        # Get requirements for this action type
        if action_step.action_type in self.parameter_requirements:
            reqs = self.parameter_requirements[action_step.action_type]
            
            # Check required parameters
            for param in reqs["required"]:
                if param not in action_step.parameters:
                    issues.append(ValidationIssue(
                        "parameter",
                        f"Required parameter '{param}' missing for action type {action_step.action_type}",
                        ValidationResult.INVALID
                    ))
            
            # Check for invalid parameters (not in required or optional)
            valid_params = set(reqs["required"] + reqs["optional"])
            for param in action_step.parameters:
                if param not in valid_params:
                    issues.append(ValidationIssue(
                        "parameter",
                        f"Parameter '{param}' not valid for action type {action_step.action_type}",
                        ValidationResult.WARNING
                    ))
        
        return issues
    
    def _validate_against_ros_actions(self, action_step: ActionStep) -> List[ValidationIssue]:
        """
        Validate action parameters against specific ROS 2 action requirements.
        
        :param action_step: The action step to validate
        :return: List of validation issues found
        """
        issues = []
        
        # This is a simplified check - in a real implementation, you would
        # have more detailed information about each ROS action's requirements
        action_type_str = action_step.action_type.value if hasattr(action_step.action_type, 'value') else str(action_step.action_type).lower()
        
        if action_type_str == "navigation":
            # Check for basic navigation parameters
            if "x" in action_step.parameters and "y" in action_step.parameters:
                # Validate coordinate types
                try:
                    float(action_step.parameters["x"])
                    float(action_step.parameters["y"])
                except (ValueError, TypeError):
                    issues.append(ValidationIssue(
                        "parameter",
                        "Navigation coordinates must be numeric values",
                        ValidationResult.INVALID
                    ))
        
        elif action_type_str == "manipulation":
            # Check manipulation parameters
            action_param = action_step.parameters.get("action", "").lower()
            if action_param in ["grasp", "pick", "take"]:
                if "object_id" not in action_step.parameters and "position" not in action_step.parameters:
                    issues.append(ValidationIssue(
                        "parameter",
                        "Grasping actions require either 'object_id' or 'position' parameter",
                        ValidationResult.INVALID
                    ))
        
        # Add more specific validations for other action types as needed
        
        return issues
    
    def _validate_sequence_properties(
        self, 
        action_sequence: ActionSequence, 
        voice_command: Optional[VoiceCommand] = None
    ) -> List[ValidationIssue]:
        """
        Validate properties of the action sequence itself.
        
        :param action_sequence: The action sequence to validate
        :param voice_command: Associated voice command (optional)
        :return: List of validation issues found
        """
        issues = []
        
        # Check if sequence has any actions
        if not action_sequence.sequence:
            issues.append(ValidationIssue(
                "sequence",
                "Action sequence is empty",
                ValidationResult.INVALID
            ))
        
        # Check for duplicate action IDs
        seen_ids = set()
        for step in action_sequence.sequence:
            if step.id in seen_ids:
                issues.append(ValidationIssue(
                    "sequence",
                    f"Duplicate action ID found: {step.id}",
                    ValidationResult.INVALID
                ))
            seen_ids.add(step.id)
        
        # Check order consistency
        orders = [step.order for step in action_sequence.sequence]
        expected_orders = list(range(len(orders)))
        if sorted(orders) != expected_orders:
            issues.append(ValidationIssue(
                "sequence",
                f"Action orders should be sequential (0, 1, 2, ...) but got: {sorted(orders)}",
                ValidationResult.WARNING
            ))
        
        # If associated with a voice command, validate compatibility
        if voice_command:
            if action_sequence.voice_command_id != voice_command.id:
                issues.append(ValidationIssue(
                    "association",
                    f"Action sequence ID doesn't match voice command ID: {action_sequence.voice_command_id} vs {voice_command.id}",
                    ValidationResult.INVALID
                ))
        
        return issues
    
    def validate_for_execution(
        self, 
        action_sequence: ActionSequence, 
        voice_command: Optional[VoiceCommand] = None
    ) -> bool:
        """
        Validate if an action sequence is ready for execution.
        
        :param action_sequence: The action sequence to validate
        :param voice_command: Associated voice command (optional)
        :return: True if the sequence is valid for execution, False otherwise
        """
        issues = self.validate_action_sequence(action_sequence, voice_command)
        
        # Execution is possible if there are no invalid issues
        return not any(issue.severity == ValidationResult.INVALID for issue in issues)
    
    def get_validation_summary(self, issues: List[ValidationIssue]) -> Dict[str, Any]:
        """
        Get a summary of validation issues.
        
        :param issues: List of validation issues
        :return: Summary dictionary
        """
        summary = {
            "total_issues": len(issues),
            "valid": True,
            "invalid_count": 0,
            "warning_count": 0,
            "issues_by_severity": {
                "valid": 0,
                "invalid": 0,
                "warning": 0,
                "unknown": 0
            },
            "critical_issues": [],
            "warnings": []
        }
        
        for issue in issues:
            summary["issues_by_severity"][issue.severity.value] += 1
            
            if issue.severity == ValidationResult.INVALID:
                summary["valid"] = False
                summary["invalid_count"] += 1
                summary["critical_issues"].append(str(issue))
            elif issue.severity == ValidationResult.WARNING:
                summary["warning_count"] += 1
                summary["warnings"].append(str(issue))
        
        return summary


class AdvancedActionValidator(ActionValidator):
    """
    Advanced action validator with additional checks for complex scenarios.
    """
    
    def __init__(self, robot_capabilities: List[str] = None, ros_action_list: List[str] = None):
        super().__init__(robot_capabilities, ros_action_list)
        
        # Add time-based validation parameters
        self.max_sequence_duration = 300  # 5 minutes maximum
        self.min_action_duration = 0.1  # 0.1 second minimum
        
        # Add resource constraint validation parameters
        self.max_navigation_distance = 50.0  # meters
        self.max_manipulation_payload = 5.0  # kg
    
    def validate_with_context(
        self,
        action_sequence: ActionSequence,
        voice_command: Optional[VoiceCommand] = None,
        robot_state: Dict[str, Any] = None,
        environment_context: Dict[str, Any] = None
    ) -> List[ValidationIssue]:
        """
        Validate an action sequence with additional context information.
        
        :param action_sequence: The action sequence to validate
        :param voice_command: Associated voice command (optional)
        :param robot_state: Current state of the robot
        :param environment_context: Environmental context
        :return: List of validation issues found
        """
        # Perform basic validation first
        issues = self.validate_action_sequence(action_sequence, voice_command)
        
        # Add context-based validations
        context_issues = self._validate_with_robot_state(action_sequence, robot_state)
        issues.extend(context_issues)
        
        env_issues = self._validate_with_environment(action_sequence, environment_context)
        issues.extend(env_issues)
        
        # Check temporal constraints
        time_issues = self._validate_temporal_constraints(action_sequence)
        issues.extend(time_issues)
        
        # Check resource constraints
        resource_issues = self._validate_resource_constraints(action_sequence)
        issues.extend(resource_issues)
        
        return issues
    
    def _validate_with_robot_state(
        self, 
        action_sequence: ActionSequence, 
        robot_state: Optional[Dict[str, Any]]
    ) -> List[ValidationIssue]:
        """
        Validate action sequence based on current robot state.
        
        :param action_sequence: The action sequence to validate
        :param robot_state: Current state of the robot
        :return: List of validation issues found
        """
        issues = []
        
        if not robot_state:
            return issues
        
        # Check if robot has required resources for the sequence
        battery_level = robot_state.get("battery_level", 100.0)
        required_battery = self._estimate_battery_usage(action_sequence)
        
        if battery_level < required_battery:
            issues.append(ValidationIssue(
                "resource",
                f"Insufficient battery for sequence: {battery_level}% < {required_battery}% estimated required",
                ValidationResult.INVALID
            ))
        
        # Check if robot is in a safe state to execute navigation
        if any(step.action_type == ActionType.NAVIGATION for step in action_sequence.sequence):
            is_safe_to_nav = robot_state.get("safe_to_navigate", True)
            if not is_safe_to_nav:
                issues.append(ValidationIssue(
                    "safety",
                    "Robot is not in a safe state to perform navigation tasks",
                    ValidationResult.INVALID
                ))
        
        return issues
    
    def _validate_with_environment(
        self, 
        action_sequence: ActionSequence, 
        environment_context: Optional[Dict[str, Any]]
    ) -> List[ValidationIssue]:
        """
        Validate action sequence based on environmental context.
        
        :param action_sequence: The action sequence to validate
        :param environment_context: Environmental context
        :return: List of validation issues found
        """
        issues = []
        
        if not environment_context:
            return issues
        
        # Check if navigation destinations are in the environment map
        for step in action_sequence.sequence:
            if step.action_type == ActionType.NAVIGATION:
                target_x = step.parameters.get("x")
                target_y = step.parameters.get("y")
                
                if target_x is not None and target_y is not None:
                    # Check if the coordinates are within the known environment
                    env_bounds = environment_context.get("bounds", {})
                    if env_bounds:
                        if (target_x < env_bounds.get("min_x", float('-inf')) or 
                            target_x > env_bounds.get("max_x", float('inf')) or
                            target_y < env_bounds.get("min_y", float('-inf')) or 
                            target_y > env_bounds.get("max_y", float('inf'))):
                            issues.append(ValidationIssue(
                                "environment",
                                f"Navigation target ({target_x}, {target_y}) is outside environment bounds",
                                ValidationResult.INVALID
                            ))
        
        return issues
    
    def _validate_temporal_constraints(self, action_sequence: ActionSequence) -> List[ValidationIssue]:
        """
        Validate action sequence against temporal constraints.
        
        :param action_sequence: The action sequence to validate
        :return: List of validation issues found
        """
        issues = []
        
        # Estimate total duration of the sequence
        estimated_duration = self._estimate_sequence_duration(action_sequence)
        
        if estimated_duration > self.max_sequence_duration:
            issues.append(ValidationIssue(
                "temporal",
                f"Estimated sequence duration ({estimated_duration}s) exceeds maximum ({self.max_sequence_duration}s)",
                ValidationResult.INVALID
            ))
        
        # Check for actions that are too short
        for step in action_sequence.sequence:
            if step.timeout < self.min_action_duration:
                issues.append(ValidationIssue(
                    "temporal",
                    f"Action timeout ({step.timeout}s) is below minimum ({self.min_action_duration}s)",
                    ValidationResult.INVALID
                ))
        
        return issues
    
    def _validate_resource_constraints(self, action_sequence: ActionSequence) -> List[ValidationIssue]:
        """
        Validate action sequence against resource constraints.
        
        :param action_sequence: The action sequence to validate
        :return: List of validation issues found
        """
        issues = []
        
        # Check navigation distances
        nav_distance = self._estimate_navigation_distance(action_sequence)
        if nav_distance > self.max_navigation_distance:
            issues.append(ValidationIssue(
                "resource",
                f"Estimated navigation distance ({nav_distance}m) exceeds maximum ({self.max_navigation_distance}m)",
                ValidationResult.INVALID
            ))
        
        # Check manipulation payload
        payload = self._estimate_manipulation_payload(action_sequence)
        if payload > self.max_manipulation_payload:
            issues.append(ValidationIssue(
                "resource",
                f"Estimated manipulation payload ({payload}kg) exceeds maximum ({self.max_manipulation_payload}kg)",
                ValidationResult.INVALID
            ))
        
        return issues
    
    def _estimate_sequence_duration(self, action_sequence: ActionSequence) -> float:
        """
        Estimate the total duration of an action sequence.
        
        :param action_sequence: The action sequence to estimate
        :return: Estimated duration in seconds
        """
        total_duration = 0.0
        
        for step in action_sequence.sequence:
            # Add timeout as a basic estimate
            total_duration += step.timeout
        
        return total_duration
    
    def _estimate_navigation_distance(self, action_sequence: ActionSequence) -> float:
        """
        Estimate the total navigation distance in an action sequence.
        
        :param action_sequence: The action sequence to analyze
        :return: Estimated distance in meters
        """
        total_distance = 0.0
        
        # For each navigation action, extract coordinates and estimate distance
        for step in action_sequence.sequence:
            if step.action_type == ActionType.NAVIGATION:
                x = step.parameters.get("x", 0.0)
                y = step.parameters.get("y", 0.0)
                
                # Use Euclidean distance as a simple estimate
                distance = (x**2 + y**2)**0.5
                total_distance += distance
        
        return total_distance
    
    def _estimate_manipulation_payload(self, action_sequence: ActionSequence) -> float:
        """
        Estimate the total manipulation payload in an action sequence.
        
        :param action_sequence: The action sequence to analyze
        :return: Estimated payload in kg
        """
        total_payload = 0.0
        
        # For each manipulation action, estimate object weight
        for step in action_sequence.sequence:
            if step.action_type == ActionType.MANIPULATION:
                # In a real implementation, this would come from object recognition
                # For now, use a default weight or parameter if available
                weight = step.parameters.get("weight", 1.0)  # Default to 1kg if not specified
                total_payload += weight
        
        return total_payload
    
    def _estimate_battery_usage(self, action_sequence: ActionSequence) -> float:
        """
        Estimate the battery usage for an action sequence.
        
        :param action_sequence: The action sequence to analyze
        :return: Estimated battery usage in percentage points
        """
        # Simplified battery usage model (in a real implementation, this would be more complex)
        usage = 0.0
        
        for step in action_sequence.sequence:
            if step.action_type == ActionType.NAVIGATION:
                # Navigation might use ~0.1% battery per meter
                x = step.parameters.get("x", 0.0)
                y = step.parameters.get("y", 0.0)
                distance = (x**2 + y**2)**0.5
                usage += distance * 0.1
            elif step.action_type == ActionType.MANIPULATION:
                # Manipulation might use ~0.5% battery per action
                usage += 0.5
        
        return usage


# Example usage:
if __name__ == "__main__":
    # Create an action validator
    validator = ActionValidator(
        robot_capabilities=["navigation", "manipulation", "perception"],
        ros_action_list=["nav2_msgs/action/NavigateToPose", "control_msgs/action/FollowJointTrajectory"]
    )
    
    # Create a sample action sequence to validate
    from ..models.action_step import ActionStep, ActionType
    from ..models.action_sequence import ActionSequence, ActionSequenceStatus
    from ..models.voice_command import VoiceCommand, VoiceCommandStatus
    import uuid
    
    action_steps = [
        ActionStep(
            id=str(uuid.uuid4()),
            action_sequence_id="seq-123",
            action_type=ActionType.NAVIGATION,
            parameters={"x": 1.0, "y": 2.0, "theta": 0.0},
            timeout=10,
            order=0
        ),
        ActionStep(
            id=str(uuid.uuid4()),
            action_sequence_id="seq-123",
            action_type=ActionType.PERCEPTION,
            parameters={"action": "detect", "object_type": "cup"},
            timeout=5,
            order=1
        )
    ]
    
    action_seq = ActionSequence(
        id="seq-123",
        voice_command_id="cmd-456",
        sequence=action_steps,
        description="Test sequence",
        status=ActionSequenceStatus.PENDING
    )
    
    # Validate the sequence
    issues = validator.validate_action_sequence(action_seq)
    
    print("Validation Results:")
    for issue in issues:
        print(f"  {issue}")
    
    # Get summary
    summary = validator.get_validation_summary(issues)
    print(f"\nSummary: {summary}")
    
    # Check if sequence is valid for execution
    is_valid_for_exec = validator.validate_for_execution(action_seq)
    print(f"Valid for execution: {is_valid_for_exec}")
    
    # Example with advanced validator
    advanced_validator = AdvancedActionValidator(
        robot_capabilities=["navigation", "manipulation", "perception"],
        ros_action_list=["nav2_msgs/action/NavigateToPose", "control_msgs/action/FollowJointTrajectory"]
    )
    
    # Validate with context
    robot_state = {
        "battery_level": 85.0,
        "safe_to_navigate": True
    }
    
    env_context = {
        "bounds": {
            "min_x": -10.0, "max_x": 10.0,
            "min_y": -10.0, "max_y": 10.0
        }
    }
    
    context_issues = advanced_validator.validate_with_context(
        action_seq, None, robot_state, env_context
    )
    
    print("\nContext Validation Results:")
    for issue in context_issues:
        print(f"  {issue}")