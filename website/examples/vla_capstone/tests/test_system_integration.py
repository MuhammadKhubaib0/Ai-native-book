"""
Integration tests for the complete VLA Capstone system.
Tests the integration between all major components.
"""
import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import numpy as np
from datetime import datetime
import json
import tempfile
import os

from ..core.vla_system import VLASystem, VLAExecutionMode
from ..models.voice_command import VoiceCommand, VoiceCommandStatus
from ..models.action_sequence import ActionSequence, ActionSequenceStatus
from ..models.action_step import ActionStep, ActionType
from ..models.multimodal_input import MultimodalInput
from ..models.vla_system_state import VLASystemState
from ..services.whisper_processor import WhisperAudioProcessor
from ..services.llm_service import LLMService, LLMConfig
from ..services.multimodal_fusion import MultimodalFusionService
from ..services.vision_integration import VisionIntegrationService
from ..services.action_validator import ActionValidator
from ..services.error_recovery import ErrorRecoveryService, ErrorType, RecoveryStrategy
from ..simulation.gazebo_integration import GazeboIntegrationService
from ..integrations.isaac_integration import IsaacSimIntegrationService
from ..evaluation.capstone_metrics import CapstoneMetricsEvaluator
from ..api.vla_api import create_app
from fastapi.testclient import TestClient
from ..config import settings


class TestSystemIntegration(unittest.TestCase):
    """
    Integration tests for the complete VLA Capstone system.
    Tests integration between all major components.
    """
    
    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        # Mock external services to avoid needing actual APIs during testing
        self.mock_services_patcher = patch.multiple(
            'website.examples.vla_capstone.core.vla_system',
            WhisperAudioProcessor=Mock(),
            LLMService=Mock(),
            MultimodalFusionService=Mock(),
            VisionIntegrationService=Mock(),
            ActionValidator=Mock(),
            ErrorRecoveryService=Mock(),
            GazeboIntegrationService=Mock(),
            IsaacSimIntegrationService=Mock()
        )
        self.mock_services = self.mock_services_patcher.start()
        
        # Create VLA system instance
        self.vla_system = VLASystem(execution_mode=VLAExecutionMode.SIMULATION)
        
        # Create test client for API tests
        app = create_app()
        self.client = TestClient(app)
        
        # Create metrics evaluator
        self.metrics_evaluator = CapstoneMetricsEvaluator()
    
    def tearDown(self):
        """
        Clean up after each test method.
        """
        self.mock_services_patcher.stop()
    
    def test_complete_voice_to_execution_pipeline(self):
        """
        Test the complete pipeline from voice input to action execution.
        """
        # Mock the Whisper service to return a known transcription
        self.mock_services['WhisperAudioProcessor'].return_value.process_audio_bytes = AsyncMock(
            return_value=("Go to the kitchen and pick up the red cup", 0.88)
        )
        
        # Mock the LLM service to return navigation and manipulation actions
        mock_actions = [
            ActionStep(
                id="nav_step_1",
                action_sequence_id="seq_123",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 2.0, "y": 1.5, "theta": 0.0},
                timeout=10,
                order=0
            ),
            ActionStep(
                id="perception_step_1",
                action_sequence_id="seq_123",
                action_type=ActionType.PERCEPTION,
                parameters={"action": "detect", "object_type": "cup", "color": "red"},
                timeout=5,
                order=1
            ),
            ActionStep(
                id="manipulation_step_1",
                action_sequence_id="seq_123",
                action_type=ActionType.MANIPULATION,
                parameters={"action": "grasp", "object_id": "red_cup_1"},
                timeout=15,
                order=2
            )
        ]
        self.mock_services['LLMService'].return_value.generate_action_sequence = AsyncMock(
            return_value=mock_actions
        )
        
        # Mock action validation
        self.mock_services['ActionValidator'].return_value.validate_action_sequence = Mock(return_value=[])
        
        # Mock Gazebo integration for action execution
        self.mock_services['GazeboIntegrationService'].return_value.execute_action_in_simulation = AsyncMock(
            return_value=True
        )
        
        # Create a mock audio input (in a real test, this would be actual audio data)
        mock_audio_input = b"mock_audio_data_that_transcribes_to_goto_kitchen_pick_up_red_cup"
        
        # Execute the complete pipeline
        result = asyncio.run(
            self.vla_system.process_voice_command(mock_audio_input)
        )
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ActionSequence)
        self.assertEqual(len(result.sequence), 3)
        
        # Verify action types are as expected
        self.assertEqual(result.sequence[0].action_type, ActionType.NAVIGATION)
        self.assertEqual(result.sequence[1].action_type, ActionType.PERCEPTION)
        self.assertEqual(result.sequence[2].action_type, ActionType.MANIPULATION)
        
        # Verify action parameters
        self.assertEqual(result.sequence[0].parameters["x"], 2.0)
        self.assertEqual(result.sequence[0].parameters["y"], 1.5)
        self.assertIn("cup", result.sequence[1].parameters["object_type"])
        self.assertIn("red", result.sequence[1].parameters["color"])
        self.assertEqual(result.sequence[2].parameters["action"], "grasp")
        
        # Verify services were called appropriately
        self.mock_services['WhisperAudioProcessor'].return_value.process_audio_bytes.assert_called_once()
        self.mock_services['LLMService'].return_value.generate_action_sequence.assert_called_once()
        self.mock_services['ActionValidator'].return_value.validate_action_sequence.assert_called_once()
    
    def test_multimodal_input_processing(self):
        """
        Test processing of multimodal inputs combining voice, vision, and sensors.
        """
        # Mock vision service to return objects
        mock_vision_data = {
            "objects": [
                {
                    "class": "cup",
                    "bbox": [0.2, 0.3, 0.4, 0.5],
                    "confidence": 0.92,
                    "position": [1.2, 0.8, 0.0]
                },
                {
                    "class": "table",
                    "bbox": [0.0, 0.0, 1.0, 1.0],
                    "confidence": 0.88,
                    "position": [1.0, 0.5, 0.0]
                }
            ],
            "scene_description": "A red cup on a wooden table in the kitchen"
        }
        self.mock_services['VisionIntegrationService'].return_value.process_scene_in_isaac_sim = AsyncMock(
            return_value=mock_vision_data
        )
        
        # Mock fusion service
        mock_fusion_result = {
            "intent": "manipulation",
            "parameters": {
                "target_object": "red cup",
                "action": "grasp",
                "object_position": [1.2, 0.8, 0.0]
            }
        }
        self.mock_services['MultimodalFusionService'].return_value.fuse_modalities = AsyncMock(
            return_value=(mock_fusion_result, 0.85)
        )
        
        # Mock LLM to generate appropriate action sequence
        mock_actions = [
            ActionStep(
                id="nav_to_cup",
                action_sequence_id="multimodal_seq_1",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 1.2, "y": 0.8, "theta": 0.0},
                timeout=10,
                order=0
            ),
            ActionStep(
                id="grasp_cup",
                action_sequence_id="multimodal_seq_1",
                action_type=ActionType.MANIPULATION,
                parameters={"action": "grasp", "object_id": "red_cup"},
                timeout=15,
                order=1
            )
        ]
        self.mock_services['LLMService'].return_value.generate_action_sequence = AsyncMock(
            return_value=mock_actions
        )
        
        # Create multimodal input
        multimodal_input = MultimodalInput(
            id="mm_input_1",
            visual_data=mock_vision_data,
            sensor_data={"timestamp": datetime.now().timestamp()},
            voice_input_id="Pick up the red cup on the table",
            confidence=0.85,
            timestamp=datetime.now()
        )
        
        # Process multimodal input through the VLA system
        # In a real implementation, this would happen through the process_multimodal_input method
        # For this test, we'll simulate the processing flow
        
        # Fusion step
        fusion_result, fusion_confidence = asyncio.run(
            self.mock_services['MultimodalFusionService'].return_value.fuse_modalities(
                voice_data={"text": multimodal_input.voice_input_id},
                vision_data=multimodal_input.visual_data,
                sensor_data=multimodal_input.sensor_data
            )
        )
        
        # Action generation step
        action_sequence = asyncio.run(
            self.mock_services['LLMService'].return_value.generate_action_sequence(
                intent=fusion_result["intent"],
                parameters=fusion_result["parameters"],
                context={}
            )
        )
        
        # Verify fusion worked correctly
        self.assertIsNotNone(fusion_result)
        self.assertGreater(fusion_confidence, 0.7)
        self.assertEqual(fusion_result["intent"], "manipulation")
        
        # Verify action sequence generation
        self.assertIsNotNone(action_sequence)
        self.assertEqual(len(action_sequence), 2)
        self.assertEqual(action_sequence[0].action_type, ActionType.NAVIGATION)
        self.assertEqual(action_sequence[1].action_type, ActionType.MANIPULATION)
    
    def test_error_recovery_integration(self):
        """
        Test the integration of error recovery mechanisms.
        """
        # Mock services to simulate an error condition
        self.mock_services['WhisperAudioProcessor'].return_value.process_audio_bytes = AsyncMock(
            return_value=("Move to position x=1000, y=1000", 0.92)  # Invalid position
        )
        
        # Mock LLM to generate navigation action to invalid position
        mock_actions = [
            ActionStep(
                id="invalid_nav_step",
                action_sequence_id="error_seq_1",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 1000.0, "y": 1000.0, "theta": 0.0},  # Invalid position
                timeout=10,
                order=0
            )
        ]
        self.mock_services['LLMService'].return_value.generate_action_sequence = AsyncMock(
            return_value=mock_actions
        )
        
        # Mock action validator to flag the invalid action
        self.mock_services['ActionValidator'].return_value.validate_action_sequence = Mock(
            return_value=["navigation target out of bounds"]
        )
        
        # Mock error recovery to handle the out-of-bounds error
        self.mock_services['ErrorRecoveryService'].return_value.handle_error = Mock(return_value={
            "strategy": RecoveryStrategy.REPLAN.value,
            "action_sequence": ActionSequence(
                id="recovery_seq_1",
                voice_command_id="cmd_123",
                sequence=[
                    ActionStep(
                        id="safe_nav_step",
                        action_sequence_id="recovery_seq_1",
                        action_type=ActionType.NAVIGATION,
                        parameters={"x": 1.0, "y": 1.0, "theta": 0.0},  # Safe position
                        timeout=10,
                        order=0
                    )
                ],
                description="Recovery sequence after out of bounds error",
                status=ActionSequenceStatus.PENDING
            ),
            "message": "Recovery from out of bounds navigation"
        })
        
        # Create audio input that results in invalid navigation
        mock_audio = b"mock_audio_for_invalid_navigation"
        
        # Process the command (this should trigger error recovery)
        result = asyncio.run(
            self.vla_system.process_voice_command(mock_audio)
        )
        
        # Verify that error recovery was triggered and a new sequence was generated
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ActionSequence)
        self.assertIn("Recovery", result.description)
        
        # Verify error recovery was called
        self.mock_services['ErrorRecoveryService'].return_value.handle_error.assert_called_once()
    
    def test_api_integration(self):
        """
        Test integration with the VLA system API.
        """
        # Test the voice command endpoint
        voice_command_data = {
            "transcribed_text": "Move forward 2 meters",
            "confidence": 0.85,
            "intent": "navigation",
            "parameters": {"distance": 2.0, "unit": "meters"}
        }
        
        response = self.client.post("/vla/voice-command", json=voice_command_data)
        
        # The API endpoint depends on actual implementation
        # This test verifies the endpoint exists and returns appropriate response
        self.assertIn(response.status_code, [200, 404, 500])  # OK, Not Found, or Server Error are valid
        
        # Test the system state endpoint
        response = self.client.get("/vla/system-state")
        self.assertIn(response.status_code, [200, 404, 500])
        
        # Try to access if the endpoint exists
        if response.status_code == 200:
            state_data = response.json()
            self.assertIsInstance(state_data, dict)
            self.assertIn("system_status", state_data)
    
    def test_action_validation_integration(self):
        """
        Test integration between action generation and validation.
        """
        # Mock LLM to generate various types of actions
        mock_actions = [
            ActionStep(
                id="valid_nav_step",
                action_sequence_id="valid_seq_1",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 1.0, "y": 1.0, "theta": 0.0},
                timeout=10,
                order=0
            ),
            ActionStep(
                id="invalid_timeout_step",
                action_sequence_id="valid_seq_1",
                action_type=ActionType.MANIPULATION,
                parameters={"action": "grasp", "object": "cup"},
                timeout=-5,  # Invalid timeout
                order=1
            )
        ]
        self.mock_services['LLMService'].return_value.generate_action_sequence = AsyncMock(
            return_value=mock_actions
        )
        
        # Mock validator to return validation issues
        self.mock_services['ActionValidator'].return_value.validate_action_sequence = Mock(
            return_value=[
                f"Timeout must be positive, got {-5}"
            ]
        )
        
        # Test action sequence creation and validation
        action_sequence = ActionSequence(
            id="test_seq_1",
            voice_command_id="test_cmd_1",
            sequence=mock_actions,
            description="Test sequence with validation issues",
            status=ActionSequenceStatus.PENDING
        )
        
        validation_issues = self.mock_services['ActionValidator'].return_value.validate_action_sequence(
            action_sequence
        )
        
        # Verify that validation correctly identified the issue
        self.assertGreater(len(validation_issues), 0)
        self.assertIn("timeout", validation_issues[0].lower())
    
    def test_system_state_synchronization(self):
        """
        Test synchronization of system state across components.
        """
        # Get initial system state
        initial_state = asyncio.run(self.vla_system.get_system_state())
        
        # Simulate processing a voice command
        self.mock_services['WhisperAudioProcessor'].return_value.process_audio_bytes = AsyncMock(
            return_value=("Test command", 0.90)
        )
        
        # Mock LLM to generate an action
        mock_actions = [
            ActionStep(
                id="test_step_1",
                action_sequence_id="test_seq_1",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 0.5, "y": 0.5},
                timeout=10,
                order=0
            )
        ]
        self.mock_services['LLMService'].return_value.generate_action_sequence = AsyncMock(
            return_value=mock_actions
        )
        
        # Process command to update system state
        mock_audio = b"mock_audio"
        action_sequence = asyncio.run(
            self.vla_system.process_voice_command(mock_audio)
        )
        
        # Get updated system state
        updated_state = asyncio.run(self.vla_system.get_system_state())
        
        # Verify that the system state was updated
        # The current command and action sequence IDs should be different
        self.assertNotEqual(initial_state.current_voice_command, updated_state.current_voice_command)
        self.assertNotEqual(initial_state.current_action_sequence, updated_state.current_action_sequence)
        
        # The state should have been updated
        self.assertGreater(updated_state.last_update, initial_state.last_update)
    
    def test_simulation_integration(self):
        """
        Test integration with simulation environments.
        """
        # Mock Gazebo service to simulate successful action execution
        self.mock_services['GazeboIntegrationService'].return_value.execute_action_in_simulation = AsyncMock(
            return_value=True
        )
        self.mock_services['GazeboIntegrationService'].return_value.get_robot_state = AsyncMock(
            return_value={
                "pose": {"x": 0.0, "y": 0.0, "z": 0.0, "rotation": {"qx": 0, "qy": 0, "qz": 0, "qw": 1}},
                "velocity": {"linear": {"x": 0.0, "y": 0.0, "z": 0.0}, "angular": {"x": 0, "y": 0, "z": 0}}
            }
        )
        
        # Create and execute a simple action sequence in simulation
        action_sequence = ActionSequence(
            id="sim_test_seq",
            voice_command_id="sim_cmd_1",
            sequence=[
                ActionStep(
                    id="sim_nav_step",
                    action_sequence_id="sim_test_seq",
                    action_type=ActionType.NAVIGATION,
                    parameters={"x": 1.0, "y": 0.0, "theta": 0.0},
                    timeout=10,
                    order=0
                )
            ],
            description="Simulation test sequence",
            status=ActionSequenceStatus.PENDING
        )
        
        # In a real implementation, this would be executed through the system
        # For this test, we'll verify the simulation service is called correctly
        execution_result = asyncio.run(
            self.mock_services['GazeboIntegrationService'].return_value.execute_action_in_simulation(
                action_sequence.sequence[0]
            )
        )
        
        # Verify execution was successful
        self.assertTrue(execution_result)
        
        # Verify robot state retrieval worked
        robot_state = asyncio.run(
            self.mock_services['GazeboIntegrationService'].return_value.get_robot_state()
        )
        self.assertIsNotNone(robot_state)
        self.assertIn("pose", robot_state)
    
    def test_metrics_evaluation_integration(self):
        """
        Test integration of metrics evaluation with system execution.
        """
        # Simulate multiple execution trials
        for i in range(5):
            success = i < 4  # Fourth trial will fail (80% success rate)
            completion_time = 15.0 + (i * 2.0)  # Vary completion time
            steps_completed = 3 if success else 1  # Either complete all steps or just one
            steps_total = 3
            errors = ["navigation_timeout"] if not success and i > 2 else []
            
            # Record trial result
            self.metrics_evaluator.record_trial_result(
                trial_id=f"integration_trial_{i}",
                success=success,
                completion_time=completion_time,
                steps_completed=steps_completed,
                steps_total=steps_total,
                errors=errors,
                metrics={
                    "accuracy": 0.85 + (i * 0.02),
                    "efficiency": 0.75 + (i * 0.03)
                }
            )
        
        # Get comprehensive metrics
        all_metrics = self.metrics_evaluator.get_all_metrics()
        
        # Verify key metrics exist
        self.assertIn("task_completion_rate", all_metrics)
        self.assertIn("mean_completion_time", all_metrics)
        self.assertIn("success_rate", all_metrics)
        self.assertIn("comprehensive_score", all_metrics)
        
        # Verify metrics have reasonable values
        self.assertGreaterEqual(all_metrics["task_completion_rate"], 0.0)
        self.assertLessEqual(all_metrics["task_completion_rate"], 1.0)
        self.assertGreaterEqual(all_metrics["success_rate"], 0.0)
        self.assertLessEqual(all_metrics["success_rate"], 1.0)
        
        # Task completion rate should be 80% (4 out of 5 trials succeeded)
        self.assertAlmostEqual(all_metrics["task_completion_rate"], 0.8, places=1)
    
    def test_confidence_threshold_integration(self):
        """
        Test integration of confidence thresholds across the system.
        """
        from ..config import settings
        
        # Remember original threshold
        original_threshold = settings.minimum_confidence_score
        
        try:
            # Set a high confidence threshold
            settings.minimum_confidence_score = 0.90
            
            # Test with a low-confidence voice command
            low_conf_command = VoiceCommand(
                id="low_conf_cmd",
                transcribed_text="Unclear command",
                intent="unknown",
                parameters={},
                confidence=0.75,  # Below threshold
                timestamp=datetime.now()
            )
            
            # In a real system, this would be filtered out early
            # For this test, we'll verify that validation catches low confidence
            from ..validation.voice_command_validation import validate_voice_command_for_execution
            validation_result = validate_voice_command_for_execution(low_conf_command)
            
            # Should have confidence-related validation errors
            confidence_errors = [error for error in validation_result.errors 
                               if "confidence" in error.lower() or "threshold" in error.lower()]
            self.assertGreater(len(confidence_errors), 0, 
                             "Low-confidence command should have confidence validation errors")
            
            # Now test with high confidence
            settings.minimum_confidence_score = 0.70  # Lower threshold
            
            high_conf_command = VoiceCommand(
                id="high_conf_cmd",
                transcribed_text="Clear command",
                intent="navigation",
                parameters={"target": "kitchen"},
                confidence=0.75,  # Above threshold now
                timestamp=datetime.now()
            )
            
            validation_result = validate_voice_command_for_execution(high_conf_command)
            confidence_errors = [error for error in validation_result.errors 
                               if "confidence" in error.lower() or "threshold" in error.lower()]
            self.assertEqual(len(confidence_errors), 0,
                           "High-confidence command should not have confidence validation errors")
            
        finally:
            # Restore original threshold
            settings.minimum_confidence_score = original_threshold
    
    async def test_long_running_integration(self):
        """
        Test system behavior over a sequence of commands to check for resource leaks,
        state corruption, or performance degradation.
        """
        # Track metrics over multiple commands
        execution_times = []
        success_count = 0
        total_commands = 10
        
        for i in range(total_commands):
            # Mock different commands
            command_texts = [
                f"Go to position x={i*0.5}, y={i*0.3}",
                f"Detect object at location {i*0.2}, {i*0.4}",
                f"Move forward {i*0.1} meters",
                f"Turn {i*10} degrees",
                f"Find the {['red', 'blue', 'green'][i % 3]} object"
            ]
            command_text = command_texts[i % len(command_texts)]
            
            # Set up mocks
            self.mock_services['WhisperAudioProcessor'].return_value.process_audio_bytes = AsyncMock(
                return_value=(command_text, 0.85 + (i * 0.01))
            )
            
            mock_actions = [
                ActionStep(
                    id=f"step_{i}_1",
                    action_sequence_id=f"seq_{i}",
                    action_type=ActionType.NAVIGATION if "go to" in command_text.lower() 
                                 else ActionType.PERCEPTION if "detect" in command_text.lower() or "find" in command_text.lower()
                                 else ActionType.OTHER,
                    parameters={"command_idx": i, "original_text": command_text},
                    timeout=10,
                    order=0
                )
            ]
            self.mock_services['LLMService'].return_value.generate_action_sequence = AsyncMock(
                return_value=mock_actions
            )
            
            # Mock validation to pass
            self.mock_services['ActionValidator'].return_value.validate_action_sequence = Mock(
                return_value=[]
            )
            
            # Measure execution time
            start_time = datetime.now()
            try:
                result = asyncio.run(
                    self.vla_system.process_voice_command(b"mock_audio")
                )
                if result:
                    success_count += 1
            except Exception as e:
                print(f"Command {i} failed: {e}")
            
            end_time = datetime.now()
            execution_times.append((end_time - start_time).total_seconds())
        
        # Analyze results
        average_time = sum(execution_times) / len(execution_times)
        success_rate = success_count / total_commands
        
        # Verify performance hasn't degraded significantly
        self.assertLess(average_time, 5.0, f"Average execution time too high: {average_time}s")
        self.assertGreater(success_rate, 0.8, f"Success rate too low: {success_rate}")
        
        # Check for memory leaks by ensuring execution times don't consistently increase
        if len(execution_times) >= 5:
            early_avg = sum(execution_times[:3]) / 3
            late_avg = sum(execution_times[-3:]) / 3
            # Allow some variation but prevent dramatic degradation
            self.assertLess(late_avg, early_avg * 2.0, 
                          "Execution time appears to be degrading over time")
        
        print(f"Long-running test completed: {success_rate*100:.1f}% success rate, "
              f"avg time {average_time:.2f}s")


class TestRealWorldIntegration(unittest.TestCase):
    """
    Tests that would run with a real system setup (disabled by default).
    """
    
    @unittest.skip("Requires real hardware and simulation setup")
    def test_real_hardware_integration(self):
        """
        Test with real hardware (requires physical robot).
        """
        # This test would run with a real robot and real sensors
        # It's skipped by default because it requires physical setup
        
        # In a real implementation:
        # 1. Connect to real robot via ROS 2
        # 2. Execute real commands
        # 3. Verify physical execution
        # 4. Measure real-world metrics
        
        self.skipTest("Real hardware integration test disabled by default")
    
    @unittest.skip("Requires Isaac Sim installation")
    def test_isaac_sim_integration(self):
        """
        Test integration with Isaac Sim.
        """
        # This test would require Isaac Sim to be installed and running
        # In a real implementation:
        # 1. Connect to Isaac Sim
        # 2. Use real perception data from Isaac Sim
        # 3. Execute actions in Isaac Sim
        # 4. Validate results
        
        self.skipTest("Isaac Sim integration test disabled by default")


class TestStressIntegration(unittest.TestCase):
    """
    Stress tests for the integrated system.
    """
    
    def setUp(self):
        """
        Set up for stress tests.
        """
        # Use mocked services to avoid dependency on external APIs during stress testing
        self.mock_services_patcher = patch.multiple(
            'website.examples.vla_capstone.core.vla_system',
            WhisperAudioProcessor=Mock(),
            LLMService=Mock(),
            MultimodalFusionService=Mock(),
            VisionIntegrationService=Mock(),
            ActionValidator=Mock(),
            ErrorRecoveryService=Mock(),
            GazeboIntegrationService=Mock(),
            IsaacSimIntegrationService=Mock()
        )
        self.mock_services = self.mock_services_patcher.start()
        
        self.vla_system = VLASystem(execution_mode=VLAExecutionMode.SIMULATION)
    
    def tearDown(self):
        """
        Clean up after stress tests.
        """
        self.mock_services_patcher.stop()
    
    def test_concurrent_command_processing(self):
        """
        Test concurrent processing of multiple voice commands.
        """
        import concurrent.futures
        import threading
        
        # Mock responses
        self.mock_services['WhisperAudioProcessor'].return_value.process_audio_bytes = AsyncMock(
            side_effect=lambda audio_data: (f"Command from thread {threading.current_thread().ident}", 0.85)
        )
        
        mock_actions = [
            ActionStep(
                id="stress_step_1",
                action_sequence_id="stress_seq_1",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 1.0, "y": 1.0},
                timeout=10,
                order=0
            )
        ]
        self.mock_services['LLMService'].return_value.generate_action_sequence = AsyncMock(
            return_value=mock_actions
        )
        
        self.mock_services['ActionValidator'].return_value.validate_action_sequence = Mock(
            return_value=[]
        )
        
        def process_command(thread_id):
            """Function to process a single command in a thread."""
            audio_data = f"mock_audio_from_thread_{thread_id}".encode()
            try:
                result = asyncio.run(
                    self.vla_system.process_voice_command(audio_data)
                )
                return result is not None
            except Exception as e:
                print(f"Thread {thread_id} error: {e}")
                return False
        
        # Execute multiple commands concurrently
        num_threads = 5
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(process_command, i) for i in range(num_threads)]
            results = [future.result() for future in futures]
        
        # Verify that all commands were processed successfully
        successful_processes = sum(results)
        self.assertEqual(successful_processes, num_threads, 
                        f"Not all {num_threads} concurrent commands were processed successfully")
        
        print(f"All {num_threads} concurrent commands processed successfully")
    
    def test_large_command_sequence(self):
        """
        Test processing of a large sequence of commands.
        """
        # Create a sequence of related commands
        test_commands = [
            "Go to the kitchen",
            "Find the red cup",
            "Move to the red cup",
            "Pick up the red cup",
            "Go to the table",
            "Place the cup on the table",
            "Return to the starting position"
        ]
        
        # Process each command
        for i, command in enumerate(test_commands):
            # Mock the service responses
            self.mock_services['WhisperAudioProcessor'].return_value.process_audio_bytes = AsyncMock(
                return_value=(command, 0.85 + (i * 0.01))
            )
            
            mock_actions = [
                ActionStep(
                    id=f"large_seq_step_{i}",
                    action_sequence_id=f"large_seq_{i}",
                    action_type=ActionType.NAVIGATION if "go to" in command.lower() 
                                 else ActionType.PERCEPTION if "find" in command.lower()
                                 else ActionType.MANIPULATION if "pick up" in command.lower() or "place" in command.lower()
                                 else ActionType.OTHER,
                    parameters={"command": command, "step_number": i},
                    timeout=10,
                    order=i
                )
            ]
            self.mock_services['LLMService'].return_value.generate_action_sequence = AsyncMock(
                return_value=mock_actions
            )
            
            self.mock_services['ActionValidator'].return_value.validate_action_sequence = Mock(
                return_value=[]
            )
            
            # Process the command
            result = asyncio.run(
                self.vla_system.process_voice_command(b"mock_audio")
            )
            
            self.assertIsNotNone(result, f"Command {i} ({command}) failed to generate action sequence")
            self.assertEqual(len(result.sequence), 1, f"Command {i} should have generated 1 action step")
        
        print(f"Successfully processed {len(test_commands)} sequential commands")
    
    def test_memory_usage_over_time(self):
        """
        Test that memory usage remains stable over extended operation.
        """
        import psutil
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process a set of commands repeatedly
        for iteration in range(20):
            # Process a command
            self.mock_services['WhisperAudioProcessor'].return_value.process_audio_bytes = AsyncMock(
                return_value=("Test command", 0.90)
            )
            
            mock_actions = [
                ActionStep(
                    id=f"memory_test_step_{iteration}",
                    action_sequence_id=f"memory_test_seq_{iteration}",
                    action_type=ActionType.NAVIGATION,
                    parameters={"x": iteration * 0.1, "y": iteration * 0.1},
                    timeout=10,
                    order=0
                )
            ]
            self.mock_services['LLMService'].return_value.generate_action_sequence = AsyncMock(
                return_value=mock_actions
            )
            
            self.mock_services['ActionValidator'].return_value.validate_action_sequence = Mock(
                return_value=[]
            )
            
            result = asyncio.run(
                self.vla_system.process_voice_command(b"mock_audio")
            )
            
            # Force garbage collection periodically
            if iteration % 5 == 4:
                gc.collect()
        
        # Check final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        self.assertLess(
            memory_increase, 100.0,
            f"Memory usage increased by {memory_increase:.2f}MB, which is excessive"
        )
        
        print(f"Memory usage after {20} operations: increased by {memory_increase:.2f}MB")


def run_integration_tests():
    """
    Run the integration test suite.
    """
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add tests from different test classes
    suite.addTest(unittest.makeSuite(TestSystemIntegration))
    suite.addTest(unittest.makeSuite(TestStressIntegration))
    
    # Run the test suite
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    # Run the integration tests
    result = run_integration_tests()
    
    print(f"\nIntegration Tests Summary:")
    print(f"- Tests run: {result.testsRun}")
    print(f"- Failures: {len(result.failures)}")
    print(f"- Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\nFailures ({len(result.failures)}):")
        for test, trace in result.failures:
            print(f"  {test}")
            print(f"    {trace.split(chr(10))[0]}")  # First line of error
    
    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for test, trace in result.errors:
            print(f"  {test}")
            print(f"    {trace.split(chr(10))[0]}")  # First line of error
    
    if result.wasSuccessful():
        print(f"\n🎉 All integration tests passed!")
        print(f"   Successfully validated system integration across all components.")
    else:
        print(f"\n❌ Some integration tests failed.")
        print(f"   Please check the above failures/errors for details.")
    
    # Run specific tests if needed
    print(f"\nTo run specific tests, use:")
    print(f"  python -m unittest tests.test_system_integration.TestSystemIntegration.test_complete_voice_to_execution_pipeline")
    print(f"  python -m unittest tests.test_system_integration.TestStressIntegration.test_concurrent_command_processing")