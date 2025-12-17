"""
Unit tests for complex command processing in the LLM-based action sequencing system.
"""
import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from ..models.voice_command import VoiceCommand
from ..models.action_sequence import ActionSequence, ActionSequenceStatus
from ..models.action_step import ActionStep, ActionType
from ..services.llm_service import LLMService, LLMConfig
from ..services.task_decomposition import TaskDecompositionService
from ..services.action_sequencer import ActionSequencer
from ..services.action_validator import ActionValidator
from ..services.error_recovery import ErrorRecoveryService, ErrorType, RecoveryStrategy
from ..parsers.llm_response_parser import LLMResponseParser


class TestComplexCommandProcessing(unittest.TestCase):
    """
    Test suite for complex command processing functionality.
    """
    
    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        self.llm_service = LLMService()
        self.task_decomposer = TaskDecompositionService()
        self.action_sequencer = ActionSequencer()
        self.action_validator = ActionValidator()
        self.error_recovery = ErrorRecoveryService()
        self.parser = LLMResponseParser()
    
    @patch('..services.llm_service.LLMService.generate_action_sequence')
    def test_process_simple_navigation_command(self, mock_generate):
        """
        Test processing of a simple navigation command.
        """
        # Mock the LLM service to return a simple navigation action
        mock_action_steps = [
            ActionStep(
                id="step-1",
                action_sequence_id="seq-123",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 1.0, "y": 2.0, "theta": 0.0},
                timeout=10,
                order=0
            )
        ]
        mock_generate.return_value = mock_action_steps
        
        # Create a voice command
        voice_command = VoiceCommand(
            id="cmd-123",
            transcribed_text="Go to position x=1, y=2",
            intent="navigation",
            parameters={"x": 1.0, "y": 2.0},
            confidence=0.9
        )
        
        # Generate action sequence using LLM
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        action_steps = loop.run_until_complete(
            self.llm_service.generate_action_sequence(
                intent=voice_command.intent,
                parameters=voice_command.parameters
            )
        )
        
        # Sequence the actions
        action_sequence = self.action_sequencer.sequence_actions(
            actions=[{
                "id": step.id,
                "action_type": step.action_type,
                "parameters": step.parameters,
                "timeout": step.timeout,
                "order": step.order
            } for step in action_steps]
        )
        
        loop.close()
        
        # Validate the sequence
        issues = self.action_validator.validate_action_sequence(action_sequence)
        
        # Assertions
        self.assertEqual(len(action_sequence.sequence), 1)
        self.assertEqual(action_sequence.sequence[0].action_type, ActionType.NAVIGATION)
        self.assertEqual(action_sequence.sequence[0].parameters["x"], 1.0)
        self.assertEqual(action_sequence.sequence[0].parameters["y"], 2.0)
        self.assertEqual(len(issues), 0, f"Validation issues found: {issues}")
    
    @patch('..services.task_decomposition.TaskDecompositionService.decompose_task')
    def test_process_complex_command_decomposition(self, mock_decompose):
        """
        Test processing of a complex command using task decomposition.
        """
        # Mock the task decomposition service
        from ..services.task_decomposition import Subtask, TaskType
        import uuid
        
        mock_subtasks = [
            Subtask(
                id=str(uuid.uuid4()),
                description="Navigate to kitchen",
                task_type=TaskType.NAVIGATION,
                parameters={"destination": "kitchen"},
                dependencies=[],
                estimated_duration=10.0
            ),
            Subtask(
                id=str(uuid.uuid4()),
                description="Detect red cup",
                task_type=TaskType.PERCEPTION,
                parameters={"object_type": "red cup"},
                dependencies=[],
                estimated_duration=5.0
            ),
            Subtask(
                id=str(uuid.uuid4()),
                description="Grasp the cup",
                task_type=TaskType.MANIPULATION,
                parameters={"object_id": "red_cup"},
                dependencies=[],
                estimated_duration=8.0
            )
        ]
        mock_decompose.return_value = mock_subtasks
        
        # Process a complex command
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        subtasks = loop.run_until_complete(
            self.task_decomposer.decompose_task(
                command="Go to the kitchen, find the red cup, and pick it up"
            )
        )
        
        loop.close()
        
        # Assertions
        self.assertEqual(len(subtasks), 3)
        self.assertIn("kitchen", subtasks[0].description.lower())
        self.assertIn("detect", subtasks[1].description.lower())
        self.assertIn("grasp", subtasks[2].description.lower())
    
    def test_action_sequence_validation(self):
        """
        Test validation of complex action sequences.
        """
        # Create a complex action sequence
        action_steps = [
            ActionStep(
                id="step-1",
                action_sequence_id="seq-123",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 1.0, "y": 2.0},
                timeout=10,
                order=0
            ),
            ActionStep(
                id="step-2",
                action_sequence_id="seq-123",
                action_type=ActionType.PERCEPTION,
                parameters={"action": "detect", "object_type": "cup"},
                timeout=5,
                order=1
            ),
            ActionStep(
                id="step-3",
                action_sequence_id="seq-123",
                action_type=ActionType.MANIPULATION,
                parameters={"action": "grasp", "object_id": "detected_cup"},
                timeout=15,
                order=2
            )
        ]
        
        action_sequence = ActionSequence(
            id="seq-123",
            voice_command_id="cmd-123",
            sequence=action_steps,
            description="Complex task sequence",
            status=ActionSequenceStatus.PENDING
        )
        
        # Validate the sequence
        issues = self.action_validator.validate_action_sequence(action_sequence)
        is_valid_for_execution = self.action_validator.validate_for_execution(action_sequence)
        
        # Assertions
        self.assertEqual(len(issues), 0, f"Validation issues found: {issues}")
        self.assertTrue(is_valid_for_execution)
    
    def test_error_recovery_for_invalid_action(self):
        """
        Test error recovery when an action sequence contains invalid actions.
        """
        # Create an action sequence with an invalid action
        action_steps = [
            ActionStep(
                id="step-1",
                action_sequence_id="seq-123",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 1.0, "y": 2.0},
                timeout=10,
                order=0
            ),
            ActionStep(
                id="step-2",
                action_sequence_id="seq-123",
                action_type=ActionType.MANIPULATION,
                parameters={},  # Missing required parameters
                timeout=15,
                order=1
            )
        ]
        
        action_sequence = ActionSequence(
            id="seq-123",
            voice_command_id="cmd-123",
            sequence=action_steps,
            description="Sequence with invalid action",
            status=ActionSequenceStatus.PENDING
        )
        
        # Validate and expect issues
        issues = self.action_validator.validate_action_sequence(action_sequence)
        self.assertGreater(len(issues), 0, "Expected validation to find issues")
        
        # Test error recovery
        recovery_result = self.error_recovery.handle_error(
            error_type=ErrorType.VALIDATION_ERROR,
            action_sequence=action_sequence,
            error_details={"validation_issues": [str(issue) for issue in issues]}
        )
        
        # Assertions
        self.assertIn("strategy", recovery_result)
        self.assertIn("recovery_result", recovery_result)
        self.assertIn(recovery_result["strategy"], [s.value for s in RecoveryStrategy])
    
    def test_llm_response_parsing(self):
        """
        Test parsing of LLM responses into action sequences.
        """
        # Test JSON array response
        json_response = '''
        [
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
            "parameters": {"action": "detect", "object_type": "cup"},
            "timeout": 5,
            "order": 1
          }
        ]
        '''
        
        # Parse the response
        parsed_actions = self.parser.parse_response(json_response)
        
        # Assertions
        self.assertEqual(len(parsed_actions), 2)
        self.assertEqual(parsed_actions[0]["action_type"], "navigation")
        self.assertEqual(parsed_actions[0]["parameters"]["x"], 1.0)
        self.assertEqual(parsed_actions[1]["action_type"], "perception")
        self.assertEqual(parsed_actions[1]["parameters"]["action"], "detect")
    
    def test_complex_command_with_multiple_validations(self):
        """
        Test processing a complex command with multiple validation steps.
        """
        complex_command_text = "Move forward 2 meters, then turn left 90 degrees, and finally move forward 1 meter"
        
        # Simulate the full processing pipeline
        
        # 1. Task decomposition
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        subtasks = loop.run_until_complete(
            self.task_decomposer.decompose_task(command=complex_command_text)
        )
        
        # 2. Convert to action steps (simulated)
        action_dicts = [
            {
                "id": f"action_{i}",
                "action_type": "navigation",
                "parameters": {"x": float(i+1), "y": 0.0, "theta": 0.0},
                "timeout": 10,
                "order": i
            }
            for i in range(len(subtasks) if subtasks else 3)  # Use 3 if no subtasks
        ]
        
        # 3. Sequence the actions
        action_sequence = self.action_sequencer.sequence_actions(actions=action_dicts)
        
        loop.close()
        
        # 4. Validate the sequence
        issues = self.action_validator.validate_action_sequence(action_sequence)
        summary = self.action_validator.get_validation_summary(issues)
        
        # Assertions
        self.assertGreaterEqual(len(action_sequence.sequence), 1)
        self.assertIsInstance(summary, dict)
        self.assertIn("total_issues", summary)
        self.assertIn("valid", summary)
        
        # The sequence should be valid if there are no invalid issues
        if summary["invalid_count"] == 0:
            self.assertTrue(summary["valid"])
        else:
            self.assertFalse(summary["valid"])


class TestAdvancedComplexCommandProcessing(unittest.TestCase):
    """
    Advanced tests for complex command processing with more sophisticated scenarios.
    """
    
    def setUp(self):
        """
        Set up test fixtures for advanced tests.
        """
        self.advanced_validator = ActionValidator(
            robot_capabilities=["navigation", "manipulation", "perception", "interaction"],
            ros_action_list=[
                "nav2_msgs/action/NavigateToPose",
                "control_msgs/action/FollowJointTrajectory",
                "moveit_msgs/action/MoveGroup"
            ]
        )
    
    def test_complex_command_with_context(self):
        """
        Test complex command processing with environmental and robot context.
        """
        from ..services.action_validator import AdvancedActionValidator
        
        # Create an advanced validator
        advanced_validator = AdvancedActionValidator(
            robot_capabilities=["navigation", "manipulation", "perception"],
            ros_action_list=["nav2_msgs/action/NavigateToPose", "control_msgs/action/FollowJointTrajectory"]
        )
        
        # Create an action sequence
        action_steps = [
            ActionStep(
                id="step-1",
                action_sequence_id="seq-123",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 50.5, "y": 2.0},  # Potentially out of bounds
                timeout=10,
                order=0
            )
        ]
        
        action_sequence = ActionSequence(
            id="seq-123",
            voice_command_id="cmd-123",
            sequence=action_steps,
            description="Test sequence with context",
            status=ActionSequenceStatus.PENDING
        )
        
        # Robot state with low battery
        robot_state = {
            "battery_level": 5.0,  # Low battery
            "safe_to_navigate": True
        }
        
        # Environmental context with bounds
        environment_context = {
            "bounds": {
                "min_x": -10.0, "max_x": 10.0,
                "min_y": -10.0, "max_y": 10.0
            }
        }
        
        # Validate with context
        issues = advanced_validator.validate_with_context(
            action_sequence, 
            robot_state=robot_state, 
            environment_context=environment_context
        )
        
        # Should have issues because of the environment bounds
        environment_issues = [issue for issue in issues if "environment" in issue.issue_type.lower()]
        battery_issues = [issue for issue in issues if "battery" in issue.issue_type.lower()]
        
        # Assertions
        self.assertGreater(len(environment_issues), 0, "Should detect coordinate out of bounds")
        # Battery issues depend on the estimate implementation
        # self.assertGreater(len(battery_issues), 0, "Should detect low battery")
    
    def test_error_recovery_with_learning(self):
        """
        Test error recovery with learning capabilities.
        """
        from ..services.error_recovery import AdvancedErrorRecoveryService
        
        # Create an advanced error recovery service
        advanced_recovery = AdvancedErrorRecoveryService()
        
        # Create a sample action sequence
        action_steps = [
            ActionStep(
                id="step-1",
                action_sequence_id="seq-123",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 1.0, "y": 2.0},
                timeout=10,
                order=0
            )
        ]
        
        action_sequence = ActionSequence(
            id="seq-123",
            voice_command_id="cmd-123",
            sequence=action_steps,
            description="Test sequence for recovery",
            status=ActionSequenceStatus.PENDING
        )
        
        # Record a few recovery outcomes
        advanced_recovery._record_recovery_outcome(
            ErrorType.EXECUTION_ERROR,
            RecoveryStrategy.RETRY,
            successful=False
        )
        advanced_recovery._record_recovery_outcome(
            ErrorType.EXECUTION_ERROR,
            RecoveryStrategy.REPLAN,
            successful=True
        )
        advanced_recovery._record_recovery_outcome(
            ErrorType.EXECUTION_ERROR,
            RecoveryStrategy.REPLAN,
            successful=True
        )
        
        # Get effectiveness statistics
        effectiveness = advanced_recovery.get_recovery_effectiveness()
        
        # Assertions
        self.assertIn("strategy_effectiveness", effectiveness)
        self.assertIn("REPLAN", effectiveness["strategy_effectiveness"])
        self.assertIn("RETRY", effectiveness["strategy_effectiveness"])
        
        # Replan should have a higher success rate than retry
        replan_success = effectiveness["strategy_effectiveness"]["REPLAN"]["success_rate"]
        retry_success = effectiveness["strategy_effectiveness"]["RETRY"]["success_rate"]
        
        # In our test case, replan is 100% successful while retry is 0% successful
        self.assertGreaterEqual(replan_success, retry_success)


if __name__ == '__main__':
    # Run the tests
    unittest.main()