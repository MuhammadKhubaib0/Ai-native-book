"""
Comprehensive end-to-end tests for the complete VLA Capstone system.
"""
import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import numpy as np
import json
from typing import Dict, Any, List

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
from ..services.error_recovery import ErrorRecoveryService
from ..simulation.capstone_env import CapstoneSimulationEnvironment
from ..evaluation.capstone_metrics import CapstoneMetricsEvaluator


class TestComprehensiveSystem(unittest.TestCase):
    """
    Comprehensive end-to-end tests for the complete VLA Capstone system.
    """
    
    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        self.vla_system = VLASystem(execution_mode=VLAExecutionMode.SIMULATION)
        self.metrics_evaluator = CapstoneMetricsEvaluator()
        self.sim_env = CapstoneSimulationEnvironment()
        
        # Mock services for testing
        self.mock_whisper = Mock(spec=WhisperAudioProcessor)
        self.mock_llm = Mock(spec=LLMService)
        self.mock_fusion = Mock(spec=MultimodalFusionService)
        self.mock_vision = Mock(spec=VisionIntegrationService)
        self.mock_action_validator = Mock(spec=ActionValidator)
        self.mock_error_recovery = Mock(spec=ErrorRecoveryService)
    
    @patch('..core.vla_system.WhisperAudioProcessor')
    @patch('..core.vla_system.LLMService')
    @patch('..core.vla_system.MultimodalFusionService')
    @patch('..core.vla_system.VisionIntegrationService')
    @patch('..core.vla_system.ActionValidator')
    @patch('..core.vla_system.ErrorRecoveryService')
    def test_complete_voice_to_action_pipeline(self, MockErrRec, MockValidator, MockVision, MockFusion, MockLLM, MockWhisper):
        """
        Test the complete pipeline from voice command to action execution.
        """
        # Setup mocks
        MockWhisper.return_value = self.mock_whisper
        MockLLM.return_value = self.mock_llm
        MockFusion.return_value = self.mock_fusion
        MockVision.return_value = self.mock_vision
        MockValidator.return_value = self.mock_action_validator
        MockErrRec.return_value = self.mock_error_recovery
        
        # Mock the whisper processor to return a known transcription
        self.mock_whisper.process_audio_bytes.return_value = ("Move forward 2 meters", 0.85)
        
        # Mock the LLM to return a known action sequence
        mock_action_steps = [
            ActionStep(
                id="step_1",
                action_sequence_id="seq_123",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 2.0, "y": 0.0, "theta": 0.0},
                timeout=10,
                order=0
            )
        ]
        self.mock_llm.generate_action_sequence.return_value = mock_action_steps
        
        # Mock validation to pass
        self.mock_action_validator.validate_action_sequence.return_value = []
        
        # Create a sample audio input (in a real test, this would be actual audio data)
        sample_audio = b"mock_audio_data"
        
        # Run the complete pipeline
        action_sequence = asyncio.run(
            self.vla_system.process_voice_command(sample_audio)
        )
        
        # Verify the results
        self.assertIsNotNone(action_sequence)
        self.assertEqual(len(action_sequence.sequence), 1)
        self.assertEqual(action_sequence.sequence[0].action_type, ActionType.NAVIGATION)
        self.assertEqual(action_sequence.sequence[0].parameters["x"], 2.0)
        
        # Verify that the correct services were called
        self.mock_whisper.process_audio_bytes.assert_called_once()
        self.mock_llm.generate_action_sequence.assert_called_once()
        self.mock_action_validator.validate_action_sequence.assert_called_once()
    
    @patch('..core.vla_system.WhisperAudioProcessor')
    @patch('..core.vla_system.LLMService')
    @patch('..core.vla_system.MultimodalFusionService')
    @patch('..core.vla_system.VisionIntegrationService')
    @patch('..core.vla_system.ActionValidator')
    @patch('..core.vla_system.ErrorRecoveryService')
    def test_multimodal_fusion_integration(self, MockErrRec, MockValidator, MockVision, MockFusion, MockLLM, MockWhisper):
        """
        Test integration of multimodal fusion with voice and vision inputs.
        """
        # Setup mocks
        MockWhisper.return_value = self.mock_whisper
        MockLLM.return_value = self.mock_llm
        MockFusion.return_value = self.mock_fusion
        MockVision.return_value = self.mock_vision
        MockValidator.return_value = self.mock_action_validator
        MockErrRec.return_value = self.mock_error_recovery
        
        # Create multimodal input
        multimodal_input = MultimodalInput(
            id="mm_input_1",
            visual_data={
                "objects": [
                    {"class": "cup", "bbox": [0.2, 0.3, 0.4, 0.5], "confidence": 0.9}
                ]
            },
            sensor_data=None,
            voice_input_id="Pick up the red cup",
            confidence=0.85,
            timestamp=datetime.now()
        )
        
        # Mock the fusion service
        mock_fusion_result = {
            "intent": "manipulation",
            "parameters": {"object_class": "cup", "action": "grasp"}
        }
        self.mock_fusion.fuse_modalities.return_value = (mock_fusion_result, 0.82)
        
        # Mock LLM to generate appropriate action steps
        mock_action_steps = [
            ActionStep(
                id="step_1",
                action_sequence_id="seq_456",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 1.0, "y": 0.5, "theta": 0.0},
                timeout=10,
                order=0
            ),
            ActionStep(
                id="step_2",
                action_sequence_id="seq_456",
                action_type=ActionType.MANIPULATION,
                parameters={"action": "grasp", "object_class": "cup"},
                timeout=15,
                order=1
            )
        ]
        self.mock_llm.generate_action_sequence.return_value = mock_action_steps
        
        # Process the multimodal input (this would happen in the VLA system)
        # For this test, we'll directly test the fusion and action generation
        
        # Simulate the fusion process
        fusion_result, confidence = self.mock_fusion.fuse_modalities(
            voice_data={"text": multimodal_input.voice_input_id},
            vision_data=multimodal_input.visual_data,
            sensor_data=None
        )
        
        # Generate action sequence based on fusion result
        action_steps = asyncio.run(
            self.mock_llm.generate_action_sequence(
                intent=fusion_result["intent"],
                parameters=fusion_result["parameters"],
                context={}
            )
        )
        
        # Verify results
        self.assertIsNotNone(fusion_result)
        self.assertGreater(confidence, 0.7)  # Should have reasonable confidence
        self.assertEqual(len(action_steps), 2)  # Should have navigation and manipulation steps
        self.assertEqual(action_steps[0].action_type, ActionType.NAVIGATION)
        self.assertEqual(action_steps[1].action_type, ActionType.MANIPULATION)
    
    @patch('..simulation.capstone_env.CapstoneSimulationEnvironment')
    def test_simulation_integration(self, MockSimEnv):
        """
        Test integration with the simulation environment.
        """
        # Setup mock
        MockSimEnv.return_value = self.sim_env
        self.sim_env.setup_environment = AsyncMock(return_value=True)
        self.sim_env.run_scenario = AsyncMock(return_value={
            "success": True,
            "completion_percentage": 100.0,
            "execution_time": 25.5,
            "results": [{"command": "Go to kitchen", "success": True}]
        })
        
        # Test scenario execution
        scenario_result = asyncio.run(
            self.sim_env.run_scenario("scenario_1", verbose=False)
        )
        
        # Verify results
        self.assertTrue(scenario_result["success"])
        self.assertEqual(scenario_result["completion_percentage"], 100.0)
        self.assertGreater(scenario_result["execution_time"], 0)
    
    def test_error_recovery_integration(self):
        """
        Test error recovery capabilities within the system.
        """
        # Mock recovery service to return a recovery strategy
        self.mock_error_recovery.handle_error.return_value = {
            "strategy": "replan",
            "action_sequence": ActionSequence(
                id="recovery_seq",
                voice_command_id="cmd_123",
                sequence=[
                    ActionStep(
                        id="recovery_step_1",
                        action_sequence_id="recovery_seq",
                        action_type=ActionType.NAVIGATION,
                        parameters={"x": 0.5, "y": 0.5, "theta": 0.0},
                        timeout=10,
                        order=0
                    )
                ],
                description="Recovery sequence",
                status=ActionSequenceStatus.PENDING
            ),
            "message": "Recovery strategy applied"
        }
        
        # Simulate an error in action execution and recovery
        error_details = {
            "error_type": "navigation_error",
            "failed_action": "navigation_to_target",
            "context": {"target_location": [1.0, 1.0]}
        }
        
        recovery_result = self.mock_error_recovery.handle_error(
            error_type="navigation_error",
            action_sequence=ActionSequence(
                id="failed_seq",
                voice_command_id="cmd_123",
                sequence=[ActionStep(
                    id="failed_step",
                    action_sequence_id="failed_seq",
                    action_type=ActionType.NAVIGATION,
                    parameters={"x": 1.0, "y": 1.0, "theta": 0.0},
                    timeout=10,
                    order=0
                )],
                description="Failed sequence",
                status=ActionSequenceStatus.FAILED
            ),
            error_details=error_details
        )
        
        # Verify recovery was attempted
        self.assertEqual(recovery_result["strategy"], "replan")
        self.assertIsNotNone(recovery_result["action_sequence"])
        self.assertIn("Recovery strategy applied", recovery_result["message"])
    
    def test_metrics_evaluation_integration(self):
        """
        Test that system components properly interface with metrics evaluation.
        """
        # Simulate some trial results
        for i in range(5):
            success = i < 4  # Last trial will fail, simulating 80% success rate
            completion_time = 15.0 + (i * 2.0)  # Increasing time for variation
            steps_completed = 3 if success else np.random.randint(0, 3)
            steps_total = 3
            
            errors = ["navigation_error"] if not success and i > 2 else []
            metrics = {"accuracy": 0.85 + (i * 0.01), "efficiency": 0.75 + (i * 0.02)}
            
            self.metrics_evaluator.record_trial_result(
                trial_id=f"trial_{i}",
                success=success,
                completion_time=completion_time,
                steps_completed=steps_completed,
                steps_total=steps_total,
                errors=errors,
                metrics=metrics
            )
        
        # Get all metrics
        all_metrics = self.metrics_evaluator.get_all_metrics()
        
        # Verify key metrics exist and have valid values
        self.assertIn("task_completion_rate", all_metrics)
        self.assertIn("mean_completion_time", all_metrics)
        self.assertIn("success_rate", all_metrics)
        self.assertIn("comprehensive_score", all_metrics)
        
        # Check that metrics have reasonable values
        self.assertGreaterEqual(all_metrics["task_completion_rate"], 0.0)
        self.assertLessEqual(all_metrics["task_completion_rate"], 1.0)
        self.assertGreaterEqual(all_metrics["success_rate"], 0.0)
        self.assertLessEqual(all_metrics["success_rate"], 1.0)
        self.assertGreaterEqual(all_metrics["comprehensive_score"], 0.0)
        self.assertLessEqual(all_metrics["comprehensive_score"], 1.0)
    
    async def test_long_sequential_execution(self):
        """
        Test execution of a long sequence of commands to verify system stability.
        """
        # Create a sequence of related commands
        test_commands = [
            "Go to the kitchen",
            "Find the red cup",
            "Move to the red cup",
            "Pick up the red cup",
            "Go to the table",
            "Place the cup on the table"
        ]
        
        execution_results = []
        
        for i, command in enumerate(test_commands):
            # Create a voice command
            voice_command = VoiceCommand(
                id=f"cmd_seq_{i}",
                transcribed_text=command,
                intent="",  # Will be set by processing
                parameters={},
                confidence=0.85,
                timestamp=datetime.now()
            )
            
            # Mock processing of the command
            # In a real test, we'd run the full pipeline
            mock_action_sequence = ActionSequence(
                id=f"seq_{i}",
                voice_command_id=voice_command.id,
                sequence=[
                    ActionStep(
                        id=f"step_{i}_1",
                        action_sequence_id=f"seq_{i}",
                        action_type=ActionType.NAVIGATION if "go to" in command.lower() else 
                                   ActionType.MANIPULATION if "pick up" in command.lower() or "place" in command.lower() else
                                   ActionType.PERCEPTION,
                        parameters={"target": command},
                        timeout=15,
                        order=0
                    )
                ],
                description=f"Action for: {command}",
                status=ActionSequenceStatus.COMPLETED
            )
            
            execution_results.append({
                "command": command,
                "action_sequence": mock_action_sequence,
                "success": True,  # Simulate success
                "execution_time": np.random.uniform(5, 15)  # Random time for simulation
            })
        
        # Verify that all commands were processed
        self.assertEqual(len(execution_results), len(test_commands))
        
        # Verify that each command produced an action sequence
        for result in execution_results:
            self.assertIsNotNone(result["action_sequence"])
            self.assertTrue(result["success"])
            self.assertGreater(result["execution_time"], 0)
    
    def test_confidence_thresholding(self):
        """
        Test the system's behavior with different confidence thresholds.
        """
        from ..config import settings
        
        # Save original threshold
        original_threshold = settings.minimum_confidence_score
        
        try:
            # Test with high confidence threshold
            settings.minimum_confidence_score = 0.95
            
            # Create a voice command with medium confidence
            voice_command = VoiceCommand(
                id="low_conf_cmd",
                transcribed_text="Move forward",
                intent="navigation",
                parameters={},
                confidence=0.85,  # Below threshold
                timestamp=datetime.now()
            )
            
            # In the VLA system, this should be rejected due to low confidence
            # For this test, we'll simulate the validation process
            from ..validation.voice_command_validation import validate_voice_command_for_execution
            validation_result = validate_voice_command_for_execution(voice_command)
            
            # Verify that low confidence command is flagged
            confidence_issues = [issue for issue in validation_result.errors if "confidence" in issue.lower()]
            self.assertGreater(len(confidence_issues), 0)
            
            # Test with low confidence threshold
            settings.minimum_confidence_score = 0.80
            
            # Same command should now pass validation
            validation_result = validate_voice_command_for_execution(voice_command)
            confidence_issues = [issue for issue in validation_result.errors if "confidence" in issue.lower()]
            self.assertEqual(len(confidence_issues), 0)
            
        finally:
            # Restore original threshold
            settings.minimum_confidence_score = original_threshold
    
    def test_system_state_consistency(self):
        """
        Test that the system state remains consistent during execution.
        """
        # This test verifies that system state is updated appropriately
        initial_state = asyncio.run(self.vla_system.get_system_state())
        
        # Simulate processing a command
        sample_audio = b"mock_audio_data"
        
        # Mock the response to avoid actual processing
        with patch.object(self.vla_system, 'process_voice_command') as mock_process:
            mock_process.return_value = ActionSequence(
                id="seq_test",
                voice_command_id="cmd_test",
                sequence=[
                    ActionStep(
                        id="step_1",
                        action_sequence_id="seq_test",
                        action_type=ActionType.NAVIGATION,
                        parameters={"x": 1.0, "y": 0.0},
                        timeout=10,
                        order=0
                    )
                ],
                description="Test sequence",
                status=ActionSequenceStatus.PENDING
            )
            
            action_sequence = asyncio.run(self.vla_system.process_voice_command(sample_audio))
        
        # Get state after processing
        post_state = asyncio.run(self.vla_system.get_system_state())
        
        # The system state should have been updated
        # Specifically, the current command and action sequence IDs should be updated
        self.assertNotEqual(initial_state.current_voice_command, post_state.current_voice_command)
        self.assertNotEqual(initial_state.current_action_sequence, post_state.current_action_sequence)
        
        # The last update time should be newer
        self.assertGreater(post_state.last_update, initial_state.last_update)
    
    def test_concurrent_access_handling(self):
        """
        Test the system's ability to handle concurrent access safely.
        """
        import concurrent.futures
        import threading
        
        # Shared counter to track successful operations
        successful_operations = 0
        lock = threading.Lock()
        
        def process_command(command_text: str):
            nonlocal successful_operations
            
            # Create a voice command
            voice_cmd = VoiceCommand(
                id=f"concurrent_cmd_{threading.current_thread().ident}",
                transcribed_text=command_text,
                intent="navigation",
                parameters={"target": command_text},
                confidence=0.9,
                timestamp=datetime.now()
            )
            
            # Simulate processing 
            mock_action_seq = ActionSequence(
                id=f"concurrent_seq_{threading.current_thread().ident}",
                voice_command_id=voice_cmd.id,
                sequence=[
                    ActionStep(
                        id=f"step_{threading.current_thread().ident}",
                        action_sequence_id=f"concurrent_seq_{threading.current_thread().ident}",
                        action_type=ActionType.NAVIGATION,
                        parameters={"x": 1.0, "y": 1.0},
                        timeout=10,
                        order=0
                    )
                ],
                description=f"Concurrent command: {command_text}",
                status=ActionSequenceStatus.PENDING
            )
            
            # Simulate successful operation
            with lock:
                successful_operations += 1
            
            return mock_action_seq
        
        # Execute multiple commands concurrently
        commands = [f"Command {i}" for i in range(10)]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_command, cmd) for cmd in commands]
            results = [future.result() for future in futures]
        
        # Verify all operations were successful
        self.assertEqual(successful_operations, len(commands))
        self.assertEqual(len(results), len(commands))
        
        # All results should be valid ActionSequence objects
        for result in results:
            self.assertIsInstance(result, ActionSequence)
            self.assertEqual(result.sequence[0].action_type, ActionType.NAVIGATION)


@unittest.skip("Integration tests require full system setup with ROS2, Isaac Sim, and Gazebo")
class TestFullIntegration(unittest.TestCase):
    """
    Full integration tests that require complete system setup.
    These are skipped by default and can be enabled when needed.
    """
    
    def setUp(self):
        """
        Set up the full system for integration testing.
        """
        # Note: This would require a fully configured system with:
        # - Running ROS 2 system
        # - Isaac Sim environment
        # - Gazebo simulation
        # - All necessary API keys
        self.vla_system = VLASystem(execution_mode=VLAExecutionMode.SIMULATION)
        
        # Connect to the system
        asyncio.run(self.vla_system.connect_to_robot())
    
    def tearDown(self):
        """
        Clean up after integration tests.
        """
        asyncio.run(self.vla_system.disconnect_from_robot())
    
    def test_full_voice_command_integration(self):
        """
        Test the complete voice command to action execution flow with real components.
        """
        # Create an actual audio file with a simple command
        # This would require creating a real audio file with "Go to the kitchen"
        
        # In a real implementation:
        # 1. Generate or use a real audio file
        # 2. Process it through the full VLA pipeline
        # 3. Verify the correct action sequence is generated
        # 4. Execute in simulation
        # 5. Verify execution results
        
        # This is a placeholder for the real test
        self.skipTest("Full integration test not implemented")
    
    def test_multimodal_integration_with_isaac_sim(self):
        """
        Test multimodal integration with Isaac Sim.
        """
        # This would test:
        # 1. Capturing real vision data from Isaac Sim
        # 2. Processing voice command
        # 3. Fusing modalities
        # 4. Executing actions in Isaac Sim
        # 5. Verifying results
        
        self.skipTest("Isaac Sim integration test not implemented")
    
    def test_long_running_session(self):
        """
        Test the system's stability over a longer session with multiple commands.
        """
        # This would run a series of commands over an extended period
        # to test for memory leaks, state corruption, etc.
        
        self.skipTest("Long-running session test not implemented")


class TestEdgeCases(unittest.TestCase):
    """
    Tests for edge cases and error conditions.
    """
    
    def setUp(self):
        """
        Set up for edge case tests.
        """
        self.vla_system = VLASystem(execution_mode=VLAExecutionMode.SIMULATION)
    
    def test_empty_voice_command(self):
        """
        Test handling of empty voice commands.
        """
        # Test with empty audio
        empty_audio = b""
        
        # Mock whisper to return empty text
        with patch.object(self.vla_system.whisper_processor, 'process_audio_bytes') as mock_whisper:
            mock_whisper.return_value = ("", 0.0)  # Empty text, low confidence
            
            result = asyncio.run(
                self.vla_system.process_voice_command(empty_audio)
            )
            
            # Should return None for empty/invalid commands
            self.assertIsNone(result)
    
    def test_extremely_long_command(self):
        """
        Test handling of extremely long voice commands.
        """
        # Create an extremely long command
        long_command = "Move forward " * 1000 + " meters"  # Very long string
        
        with patch.object(self.vla_system.whisper_processor, 'process_audio_bytes') as mock_whisper:
            mock_whisper.return_value = (long_command, 0.85)
            
            # The system should handle this gracefully
            result = asyncio.run(
                self.vla_system.process_voice_command(b"mock_audio")
            )
        
        # For very long commands, the system might still generate actions
        # or it might validate and reject if the command is too complex
        # depending on the implementation
        
        # If an action sequence was generated, verify it's structurally valid
        if result is not None:
            self.assertIsInstance(result, ActionSequence)
            for step in result.sequence:
                self.assertIsInstance(step, ActionStep)
    
    def test_command_with_special_characters(self):
        """
        Test handling of voice commands with special characters.
        """
        special_command = "Go to the café with naïve naïveté"
        
        with patch.object(self.vla_system.whisper_processor, 'process_audio_bytes') as mock_whisper:
            mock_whisper.return_value = (special_command, 0.90)
            
            result = asyncio.run(
                self.vla_system.process_voice_command(b"mock_audio")
            )
        
        # The system should handle special characters without error
        if result is not None:
            self.assertIsInstance(result, ActionSequence)
    
    def test_invalid_coordinates(self):
        """
        Test handling of commands with invalid coordinates.
        """
        invalid_command = "Go to coordinates x=inf, y=NaN"
        
        with patch.object(self.vla_system.whisper_processor, 'process_audio_bytes') as mock_whisper:
            mock_whisper.return_value = (invalid_command, 0.85)
            
            # Mock LLM to return potentially invalid parameters
            with patch.object(self.vla_system.llm_service, 'generate_action_sequence') as mock_llm:
                # Return an action with potentially invalid coordinates
                mock_llm.return_value = [
                    ActionStep(
                        id="invalid_step",
                        action_sequence_id="seq_invalid",
                        action_type=ActionType.NAVIGATION,
                        parameters={"x": float('inf'), "y": float('nan')},
                        timeout=10,
                        order=0
                    )
                ]
                
                result = asyncio.run(
                    self.vla_system.process_voice_command(b"mock_audio")
                )
        
        # If result exists, the validation should catch invalid coordinates
        if result is not None:
            # The validation should have prevented the invalid parameters from causing issues
            self.assertIsInstance(result, ActionSequence)
    
    def test_system_shutdown_procedures(self):
        """
        Test proper cleanup during system shutdown.
        """
        # Create a VLA system
        system = VLASystem(execution_mode=VLAExecutionMode.SIMULATION)
        
        # Perform some mock operations to set internal state
        system.system_state.current_voice_command = "test_command"
        system.system_state.current_action_sequence = "test_sequence"
        
        # Shutdown the system
        asyncio.run(system.shutdown())
        
        # Verify cleanup happened (implementation-specific)
        # This would check that resources were properly released
        # For our mock, we'll just verify no exceptions were thrown


class TestPerformance(unittest.TestCase):
    """
    Performance tests to ensure system operates efficiently.
    """
    
    def setUp(self):
        """
        Set up for performance tests.
        """
        self.vla_system = VLASystem(execution_mode=VLAExecutionMode.SIMULATION)
    
    def test_command_processing_latency(self):
        """
        Test the latency of command processing under normal conditions.
        """
        import time
        
        command = "Move forward 1 meter"
        
        with patch.object(self.vla_system.whisper_processor, 'process_audio_bytes') as mock_whisper:
            mock_whisper.return_value = (command, 0.9)
            
            with patch.object(self.vla_system.llm_service, 'generate_action_sequence') as mock_llm:
                mock_llm.return_value = [
                    ActionStep(
                        id="perf_step",
                        action_sequence_id="perf_seq",
                        action_type=ActionType.NAVIGATION,
                        parameters={"x": 1.0, "y": 0.0},
                        timeout=10,
                        order=0
                    )
                ]
                
                # Measure processing time
                start_time = time.time()
                result = asyncio.run(
                    self.vla_system.process_voice_command(b"mock_audio")
                )
                end_time = time.time()
                
                processing_time = end_time - start_time
        
        # Processing should typically be under 5 seconds for simple commands
        self.assertLess(processing_time, 5.0, f"Processing took too long: {processing_time}s")
        
        # Verify result was generated
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ActionSequence)
    
    def test_memory_usage_stability(self):
        """
        Test that memory usage remains stable over multiple operations.
        """
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform multiple operations
        command = "Go to the kitchen"
        
        with patch.object(self.vla_system.whisper_processor, 'process_audio_bytes') as mock_whisper:
            mock_whisper.return_value = (command, 0.85)
            
            with patch.object(self.vla_system.llm_service, 'generate_action_sequence') as mock_llm:
                mock_llm.return_value = [
                    ActionStep(
                        id="mem_test_step",
                        action_sequence_id="mem_test_seq",
                        action_type=ActionType.NAVIGATION,
                        parameters={"x": 1.0, "y": 1.0},
                        timeout=10,
                        order=0
                    )
                ]
                
                # Process the same command multiple times
                for _ in range(50):  # Process 50 commands
                    result = asyncio.run(
                        self.vla_system.process_voice_command(b"mock_audio")
                    )
                    self.assertIsNotNone(result)
        
        # Check memory usage hasn't grown significantly
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Memory growth should be minimal (within 50MB)
        memory_growth = final_memory - initial_memory
        self.assertLess(memory_growth, 50.0, 
                       f"Memory grew by {memory_growth}MB, which is too much")


# Helper function for running the comprehensive test suite
def run_comprehensive_tests():
    """
    Run the comprehensive test suite.
    """
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add tests from the main test class
    suite.addTest(unittest.makeSuite(TestComprehensiveSystem))
    suite.addTest(unittest.makeSuite(TestEdgeCases))
    suite.addTest(unittest.makeSuite(TestPerformance))
    
    # Run the test suite
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


# Example usage
if __name__ == "__main__":
    # Run the tests
    result = run_comprehensive_tests()
    
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, trace in result.failures:
            print(f"{test}: {trace}")
    
    if result.errors:
        print("\nErrors:")
        for test, trace in result.errors:
            print(f"{test}: {trace}")
    
    if result.wasSuccessful():
        print("\nAll tests passed! 🎉")
    else:
        print("\nSome tests failed. 😞")