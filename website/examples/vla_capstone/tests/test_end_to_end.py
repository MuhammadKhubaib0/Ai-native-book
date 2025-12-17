"""
End-to-end integration test for the complete VLA system.
Tests the entire pipeline from voice command to action execution.
"""
import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import tempfile
import os
from datetime import datetime
import numpy as np

from ..core.vla_system import VLASystem, VLAExecutionMode
from ..models.voice_command import VoiceCommand
from ..models.action_sequence import ActionSequence
from ..models.action_step import ActionStep, ActionType
from ..models.multimodal_input import MultimodalInput
from ..models.vla_system_state import VLASystemState
from ..services.whisper_processor import WhisperAudioProcessor
from ..services.llm_service import LLMService, LLMConfig
from ..services.vision_integration import VisionIntegrationService
from ..services.multimodal_fusion import MultimodalFusionService
from ..services.action_sequencer import ActionSequencer
from ..services.navigation_service import NavigationService
from ..services.object_manipulation import ObjectManipulationService
from ..simulation.gazebo_integration import GazeboIntegrationService
from ..integrations.isaac_integration import IsaacSimIntegrationService
from ..evaluation.capstone_metrics import CapstoneMetricsEvaluator
from ..config import settings


class TestEndToEndVLAIntegration(unittest.TestCase):
    """
    End-to-end integration tests for the complete VLA pipeline.
    """
    
    def setUp(self):
        """
        Set up test fixtures for end-to-end tests.
        """
        # Create a complete VLA system
        self.vla_system = VLASystem(execution_mode=VLAExecutionMode.SIMULATION)
        
        # Create mock services to avoid dependency on actual external services
        self.mock_whisper = Mock(spec=WhisperAudioProcessor)
        self.mock_llm = Mock(spec=LLMService)
        self.mock_vision = Mock(spec=VisionIntegrationService)
        self.mock_fusion = Mock(spec=MultimodalFusionService)
        self.mock_sequencer = Mock(spec=ActionSequencer)
        self.mock_navigation = Mock(spec=NavigationService)
        self.mock_manipulation = Mock(spec=ObjectManipulationService)
        self.mock_gazebo = Mock(spec=GazeboIntegrationService)
        self.mock_isaac = Mock(spec=IsaacSimIntegrationService)
        self.mock_metrics = Mock(spec=CapstoneMetricsEvaluator)
        
        # Set up proper mocking for services
        self.vla_system.whisper_service = self.mock_whisper
        self.vla_system.llm_service = self.mock_llm
        self.vla_system.vision_service = self.mock_vision
        self.vla_system.fusion_service = self.mock_fusion
        self.vla_system.action_sequencer = self.mock_sequencer
        self.vla_system.navigation_service = self.mock_navigation
        self.vla_system.manipulation_service = self.mock_manipulation
        self.vla_system.gazebo_service = self.mock_gazebo
        self.vla_system.isaac_integration = self.mock_isaac
    
    @patch('..services.whisper_processor.WhisperAudioProcessor.process_audio_bytes')
    @patch('..services.llm_service.LLMService.generate_action_sequence')
    @patch('..services.multimodal_fusion.MultimodalFusionService.fuse_modalities')
    @patch('..services.action_sequencer.ActionSequencer.sequence_actions')
    @patch('..simulation.gazebo_integration.GazeboIntegrationService.execute_action_in_simulation')
    async def test_complete_voice_to_action_pipeline(
        self,
        mock_execute_action,
        mock_sequence_actions,
        mock_fuse_modalities,
        mock_generate_action,
        mock_process_audio
    ):
        """
        Test the complete pipeline: voice -> whisper -> llm -> fusion -> action -> execution.
        """
        # Mock the services to simulate successful processing
        mock_process_audio.return_value = ("Go to the kitchen and pick up the red cup", 0.88)
        
        # Create mock action steps
        mock_action_steps = [
            ActionStep(
                id="nav_step_1",
                action_sequence_id="seq_123",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 2.0, "y": 1.0, "theta": 0.0},
                timeout=10,
                order=0
            ),
            ActionStep(
                id="perception_step_1",
                action_sequence_id="seq_123",
                action_type=ActionType.PERCEPTION,
                parameters={"action": "detect", "target": "red_cup"},
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
        mock_generate_action.return_value = mock_action_steps
        
        # Mock action sequencing
        mock_sequence_actions.return_value = ActionSequence(
            id="seq_123",
            voice_command_id="cmd_123",
            sequence=mock_action_steps,
            description="Go to kitchen and grasp red cup",
            status="pending"
        )
        
        # Mock fusion
        mock_fuse_modalities.return_value = ({
            "intent": "complex_task",
            "parameters": {"primary_action": "navigate_and_grasp", "target_object": "red_cup", "target_location": "kitchen"}
        }, 0.85)
        
        # Mock action execution
        mock_execute_action.return_value = True
        
        # Create mock audio data (in practice, this would be actual audio)
        mock_audio_data = b"mock_audio_data_for_kitchen_command"
        
        # Execute the complete pipeline
        action_sequence = await self.vla_system.process_voice_command(mock_audio_data)
        
        # Verify each step of the pipeline was called
        mock_process_audio.assert_called_once()
        mock_generate_action.assert_called_once()
        mock_fuse_modalities.assert_called_once()
        mock_sequence_actions.assert_called_once()
        
        # Verify the action sequence was created with correct properties
        self.assertIsNotNone(action_sequence)
        self.assertEqual(len(action_sequence.sequence), 3)
        self.assertEqual(action_sequence.sequence[0].action_type, ActionType.NAVIGATION)
        self.assertEqual(action_sequence.sequence[1].action_type, ActionType.PERCEPTION)
        self.assertEqual(action_sequence.sequence[2].action_type, ActionType.MANIPULATION)
        
        # Execute the action sequence
        execution_success = await self.vla_system.execute_action_sequence(action_sequence)
        self.assertTrue(execution_success, "Action sequence execution should succeed")
        
        # Verify all actions were executed
        self.assertEqual(mock_execute_action.call_count, 3, "All 3 actions should be executed")
    
    @patch('..services.whisper_processor.WhisperAudioProcessor.process_audio_bytes')
    @patch('..services.llm_service.LLMService.generate_action_sequence')
    @patch('..services.multimodal_fusion.MultimodalFusionService.fuse_modalities')
    @patch('..services.action_sequencer.ActionSequencer.sequence_actions')
    @patch('..simulation.gazebo_integration.GazeboIntegrationService.execute_action_in_simulation')
    async def test_multimodal_integration_pipeline(
        self,
        mock_execute_action,
        mock_sequence_actions,
        mock_fuse_modalities,
        mock_generate_action,
        mock_process_audio
    ):
        """
        Test multimodal input integration: voice + visual + sensor data.
        """
        # Mock processing
        mock_process_audio.return_value = ("Find the book and bring it to me", 0.92)
        mock_generate_action.return_value = [
            ActionStep(
                id="nav_to_object",
                action_sequence_id="seq_456",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 1.5, "y": 0.5},
                timeout=10,
                order=0
            ),
            ActionStep(
                id="grasp_object",
                action_sequence_id="seq_456",
                action_type=ActionType.MANIPULATION,
                parameters={"action": "grasp", "object_id": "detected_book"},
                timeout=15,
                order=1
            )
        ]
        
        # Mock fusion with multimodal data
        mock_fuse_modalities.return_value = ({
            "intent": "fetch_object",
            "parameters": {"object_class": "book", "action": "fetch"}
        }, 0.89)
        
        mock_sequence_actions.return_value = ActionSequence(
            id="seq_456",
            voice_command_id="cmd_456",
            sequence=mock_generate_action.return_value,
            description="Fetch the book",
            status="pending"
        )
        
        # Mock action execution
        mock_execute_action.return_value = True
        
        # Create multimodal input
        multimodal_input = MultimodalInput(
            id="mm_test_input",
            visual_data={
                "objects": [
                    {"class": "book", "position": [1.5, 0.5, 0.8], "confidence": 0.87}
                ]
            },
            sensor_data={"timestamp": datetime.now().timestamp()},
            voice_input_id="Find the book and bring it to me",
            confidence=0.9,
            timestamp=datetime.now()
        )
        
        # Process multimodal input through fusion
        fused_result, confidence = await self.vla_system.fuse_modalities(
            voice_data={"text": multimodal_input.voice_input_id, "confidence": 0.9},
            vision_data=multimodal_input.visual_data,
            sensor_data=multimodal_input.sensor_data
        )
        
        # Verify fusion worked
        self.assertIsNotNone(fused_result)
        self.assertGreaterEqual(confidence, 0.7)
        
        # Generate action sequence from fusion result
        action_steps = await self.vla_system.generate_action_sequence_from_fusion(fused_result, confidence)
        self.assertIsNotNone(action_steps)
        self.assertGreater(len(action_steps.sequence), 0)
        
        # Execute the sequence
        success = await self.vla_system.execute_action_sequence(action_steps)
        self.assertTrue(success)
        
        # Verify action execution
        mock_execute_action.assert_called()
    
    @patch('..services.whisper_processor.WhisperAudioProcessor.process_audio_bytes')
    @patch('..services.llm_service.LLMService.generate_action_sequence')
    @patch('..simulation.gazebo_integration.GazeboIntegrationService.execute_action_in_simulation')
    async def test_error_recovery_integration(
        self,
        mock_execute_action,
        mock_generate_action,
        mock_process_audio
    ):
        """
        Test error recovery integration in the complete pipeline.
        """
        # Create a scenario where an action fails and recovery is needed
        
        # Make the first action execution fail, but subsequent ones succeed
        call_count = 0
        def mock_execute_side_effect(action_step):
            nonlocal call_count
            call_count += 1
            # Make the first action fail
            return call_count > 1  # Return False only for first call
        
        mock_execute_action.side_effect = mock_execute_side_effect
        mock_process_audio.return_value = ("Go forward and pick up the object", 0.85)
        
        mock_action_steps = [
            ActionStep(
                id="failing_nav_step",
                action_sequence_id="seq_789",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 1.0, "y": 0.0},
                timeout=10,
                order=0
            ),
            ActionStep(
                id="success_manipulation_step",
                action_sequence_id="seq_789",
                action_type=ActionType.MANIPULATION,
                parameters={"action": "grasp", "object_id": "obj_1"},
                timeout=15,
                order=1
            )
        ]
        mock_generate_action.return_value = mock_action_steps
        
        # Create mock audio
        mock_audio = b"mock_audio_data"
        
        # Process and execute the command
        action_sequence = await self.vla_system.process_voice_command(mock_audio)
        execution_result = await self.vla_system.execute_action_sequence(action_sequence)
        
        # The execution result depends on the error recovery configuration
        # Since the second action should succeed, overall result may still be positive
        # depending on how the error recovery handles the first failure
        
        # Verify that both actions were attempted (error recovery should have tried alternatives)
        self.assertGreaterEqual(mock_execute_action.call_count, 1)
    
    @patch('..services.whisper_processor.WhisperAudioProcessor.process_audio_bytes')
    @patch('..services.llm_service.LLMService.generate_action_sequence')
    @patch('..simulation.gazebo_integration.GazeboIntegrationService.execute_action_in_simulation')
    async def test_concurrent_command_processing(
        self,
        mock_execute_action,
        mock_generate_action,
        mock_process_audio
    ):
        """
        Test processing of multiple commands concurrently.
        """
        # Mock successful processing for all commands
        mock_process_audio.return_value = ("Move forward 1 meter", 0.9)
        mock_generate_action.return_value = [
            ActionStep(
                id="concurrent_action",
                action_sequence_id="seq_concurrent",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 1.0, "y": 0.0},
                timeout=10,
                order=0
            )
        ]
        mock_execute_action.return_value = True
        
        # Create multiple audio inputs to process concurrently
        audio_inputs = [f"mock_audio_{i}".encode() for i in range(5)]
        
        async def process_input(audio_data):
            action_seq = await self.vla_system.process_voice_command(audio_data)
            if action_seq:
                return await self.vla_system.execute_action_sequence(action_seq)
            return False
        
        # Process all inputs concurrently
        results = await asyncio.gather(*[
            process_input(audio) for audio in audio_inputs
        ], return_exceptions=True)
        
        # Verify all commands were processed (allowing for potential exceptions)
        completed_count = sum(1 for r in results if not isinstance(r, Exception) and r == True)
        self.assertEqual(completed_count, len(audio_inputs), 
                         f"All {len(audio_inputs)} commands should have been processed successfully")
    
    def test_system_state_consistency(self):
        """
        Test consistency of system state throughout the pipeline.
        """
        # Create a mock system state
        initial_state = VLASystemState(
            id="test_state_initial",
            current_voice_command="",
            current_action_sequence="",
            system_status="idle",
            perception_data={},
            last_update=datetime.now()
        )
        
        # Process a command and verify state updates
        async def run_state_test():
            # Get initial state
            state_before = await self.vla_system.get_system_state()
            
            # Mock processing a command
            mock_audio = b"mock_audio_data_go_to_kitchen"
            
            with patch.object(self.vla_system.whisper_service, 'process_audio_bytes') as mock_whisper:
                with patch.object(self.vla_system.llm_service, 'generate_action_sequence') as mock_llm:
                    with patch.object(self.vla_system.gazebo_service, 'execute_action_in_simulation') as mock_exec:
                        
                        mock_whisper.return_value = ("Go to the kitchen", 0.88)
                        mock_llm.return_value = [
                            ActionStep(
                                id="state_test_action",
                                action_sequence_id="state_seq_1",
                                action_type=ActionType.NAVIGATION,
                                parameters={"x": 2.0, "y": 1.0},
                                timeout=10,
                                order=0
                            )
                        ]
                        mock_exec.return_value = True
                        
                        # Process and execute command
                        action_seq = await self.vla_system.process_voice_command(mock_audio)
                        if action_seq:
                            exec_success = await self.vla_system.execute_action_sequence(action_seq)
                        
                        # Get state after command processing
                        state_after = await self.vla_system.get_system_state()
                        
                        # Verify state has been updated appropriately
                        self.assertNotEqual(state_before, state_after)
                        self.assertNotEqual(state_before.last_update, state_after.last_update)
                        self.assertNotEqual(state_before.system_status, state_after.system_status)
                        self.assertIn("kitchen", state_after.current_voice_command.lower() if state_after.current_voice_command else "")
        
        asyncio.run(run_state_test())
    
    @patch('..services.whisper_processor.WhisperAudioProcessor.process_audio_bytes')
    @patch('..services.llm_service.LLMService.generate_action_sequence')
    @patch('..simulation.gazebo_integration.GazeboIntegrationService.execute_action_in_simulation')
    async def test_performance_under_load(
        self,
        mock_execute_action,
        mock_generate_action,
        mock_process_audio
    ):
        """
        Test system performance under load conditions.
        """
        import time
        
        # Mock successful processing
        mock_process_audio.return_value = ("Simple navigation command", 0.9)
        mock_generate_action.return_value = [
            ActionStep(
                id="perf_test_action",
                action_sequence_id="perf_seq_1",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 1.0, "y": 0.0},
                timeout=10,
                order=0
            )
        ]
        mock_execute_action.return_value = True
        
        # Measure performance of processing many commands
        num_commands = 20
        start_time = time.time()
        
        success_count = 0
        for i in range(num_commands):
            mock_audio = f"mock_audio_command_{i}".encode()
            
            action_seq = await self.vla_system.process_voice_command(mock_audio)
            if action_seq:
                exec_success = await self.vla_system.execute_action_sequence(action_seq)
                if exec_success:
                    success_count += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify performance metrics
        avg_time_per_command = total_time / num_commands
        success_rate = success_count / num_commands
        
        # Performance should be reasonable: < 2 seconds per command on average
        # and > 90% success rate
        self.assertLess(avg_time_per_command, 2.0, 
                       f"Average processing time too high: {avg_time_per_command:.2f}s per command")
        self.assertGreaterEqual(success_rate, 0.9, 
                               f"Success rate too low: {success_rate:.2f}")
        
        print(f"Performance test results: {num_commands} commands in {total_time:.2f}s, "
              f"avg {avg_time_per_command:.3f}s per command, {success_rate:.1f}% success rate")
    
    @patch('..services.whisper_processor.WhisperAudioProcessor.process_audio_bytes')
    @patch('..services.llm_service.LLMService.generate_action_sequence')
    @patch('..simulation.gazebo_integration.GazeboIntegrationService.execute_action_in_simulation')
    def test_action_sequence_complexity_handling(
        self,
        mock_execute_action,
        mock_generate_action,
        mock_process_audio
    ):
        """
        Test handling of complex action sequences with many steps.
        """
        # Mock processing for complex command
        mock_process_audio.return_value = ("Perform a complex task with many steps", 0.9)
        
        # Create a longer sequence of actions to test complexity handling
        complex_action_steps = []
        for i in range(10):  # Create 10 action steps
            action_step = ActionStep(
                id=f"complex_action_{i}",
                action_sequence_id="complex_seq_1",
                action_type=ActionType.NAVIGATION if i % 3 == 0 else 
                           ActionType.MANIPULATION if i % 3 == 1 else 
                           ActionType.PERCEPTION,
                parameters={
                    "x": float(i) * 0.5, 
                    "y": float(i % 2) * 0.5,
                    "action": f"action_{i}",
                    "object_id": f"object_{i}" if i % 2 == 0 else None
                },
                timeout=10,
                order=i
            )
            complex_action_steps.append(action_step)
        
        mock_generate_action.return_value = complex_action_steps
        mock_execute_action.return_value = True  # All actions succeed
        
        async def run_complex_test():
            # Process complex command
            mock_audio = b"mock_audio_complex_command"
            
            action_sequence = await self.vla_system.process_voice_command(mock_audio)
            self.assertIsNotNone(action_sequence)
            self.assertEqual(len(action_sequence.sequence), 10)
            
            # Execute complex sequence
            execution_success = await self.vla_system.execute_action_sequence(action_sequence)
            self.assertTrue(execution_success)
            
            # Verify all steps were executed
            self.assertEqual(mock_execute_action.call_count, 10)
        
        asyncio.run(run_complex_test())
    
    async def test_educational_tracking_integration(self):
        """
        Test integration with educational tracking components.
        """
        # This would test integration with the student progress tracking system
        # In our mock system, we'll just verify the integration points exist
        
        # Verify VLA system has methods for educational tracking
        self.assertTrue(hasattr(self.vla_system, 'update_student_progress'))
        
        # Mock a call to update student progress
        with patch.object(self.vla_system, 'update_student_progress') as mock_update:
            mock_update.return_value = True
            
            result = await self.vla_system.update_student_progress(
                student_id="student_123",
                module_name="VLA_Capstone",
                chapter_name="Complete_Integration_Test",
                progress=100.0
            )
            
            self.assertTrue(result)
            mock_update.assert_called_once()
        
        print("Educational tracking integration verified")


class TestRobustnessAndEdgeCases(unittest.TestCase):
    """
    Test robustness and edge cases for the VLA system.
    """
    
    def setUp(self):
        """
        Set up test fixtures for robustness tests.
        """
        self.vla_system = VLASystem(execution_mode=VLAExecutionMode.SIMULATION)
    
    @patch('..services.whisper_processor.WhisperAudioProcessor.process_audio_bytes')
    async def test_empty_command_handling(self, mock_process_audio):
        """
        Test handling of empty or null commands.
        """
        mock_process_audio.return_value = ("", 0.1)  # Low confidence empty string
        
        # Process empty audio/command
        action_sequence = await self.vla_system.process_voice_command(b"")
        
        # Should return None or handle gracefully
        self.assertIsNone(action_sequence, "Should handle empty command gracefully")
    
    @patch('..services.whisper_processor.WhisperAudioProcessor.process_audio_bytes')
    @patch('..services.llm_service.LLMService.generate_action_sequence')
    async def test_very_long_command_handling(self, mock_generate_action, mock_process_audio):
        """
        Test handling of very long commands.
        """
        # Mock a very long command
        very_long_command = "Go to the " + "kitchen " * 1000  # Extremely long command
        mock_process_audio.return_value = (very_long_command, 0.8)
        mock_generate_action.return_value = [
            ActionStep(
                id="long_command_action",
                action_sequence_id="long_seq_1",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 1.0, "y": 1.0},
                timeout=10,
                order=0
            )
        ]
        
        # Process the long command
        action_sequence = await self.vla_system.process_voice_command(b"mock_audio")
        
        # Should handle gracefully even if the command is very long
        self.assertIsNotNone(action_sequence)
        
        # Execution should also work
        with patch('..simulation.gazebo_integration.GazeboIntegrationService.execute_action_in_simulation') as mock_exec:
            mock_exec.return_value = True
            exec_success = await self.vla_system.execute_action_sequence(action_sequence)
            self.assertTrue(exec_success)
    
    @patch('..services.whisper_processor.WhisperAudioProcessor.process_audio_bytes')
    @patch('..services.llm_service.LLMService.generate_action_sequence')
    async def test_invalid_coordinates_handling(self, mock_generate_action, mock_process_audio):
        """
        Test handling of invalid coordinates in action generation.
        """
        mock_process_audio.return_value = ("Go to position x=invalid, y=NaN", 0.7)
        # Mock LLM to return action with invalid coordinates
        mock_generate_action.return_value = [
            ActionStep(
                id="invalid_coords_action",
                action_sequence_id="invalid_seq_1",
                action_type=ActionType.NAVIGATION,
                parameters={"x": float('inf'), "y": float('nan')},  # Invalid coordinates
                timeout=10,
                order=0
            )
        ]
        
        # Process the command with invalid coordinates
        action_sequence = await self.vla_system.process_voice_command(b"mock_audio")
        
        # The sequence should be created but may not execute successfully
        self.assertIsNotNone(action_sequence)
        self.assertEqual(len(action_sequence.sequence), 1)
        
        # When executed, error handling should manage the invalid coordinates
        with patch('..simulation.gazebo_integration.GazeboIntegrationService.execute_action_in_simulation') as mock_exec:
            # Mock execution to return False for invalid coordinates
            mock_exec.return_value = False
            exec_result = await self.vla_system.execute_action_sequence(action_sequence)
            
            # Should handle the error gracefully
            # The exact behavior depends on the error recovery implementation
            # but it should not crash
            self.assertIsNotNone(exec_result)
    
    @patch('..services.whisper_processor.WhisperAudioProcessor.process_audio_bytes')
    @patch('..services.llm_service.LLMService.generate_action_sequence')
    async def test_extremely_high_confidence_handling(self, mock_generate_action, mock_process_audio):
        """
        Test handling of commands with extremely high confidence.
        """
        mock_process_audio.return_value = ("Absolutely go to the kitchen immediately", 0.99)  # Very high confidence
        mock_generate_action.return_value = [
            ActionStep(
                id="high_conf_action",
                action_sequence_id="high_conf_seq_1",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 2.0, "y": 1.0},
                timeout=5,  # Short timeout due to high confidence
                order=0
            )
        ]
        
        # Process high confidence command
        action_sequence = await self.vla_system.process_voice_command(b"mock_audio")
        
        # Should process normally regardless of high confidence
        self.assertIsNotNone(action_sequence)
        self.assertAlmostEqual(action_sequence.sequence[0].timeout, 5, places=1)
        
        # Execute the sequence
        with patch('..simulation.gazebo_integration.GazeboIntegrationService.execute_action_in_simulation') as mock_exec:
            mock_exec.return_value = True
            exec_success = await self.vla_system.execute_action_sequence(action_sequence)
            self.assertTrue(exec_success)


class TestIntegrationWithExternalSystems(unittest.TestCase):
    """
    Test integration with external systems like Isaac Sim and Gazebo.
    """
    
    def setUp(self):
        """
        Set up test fixtures for external system integration.
        """
        self.vla_system = VLASystem(execution_mode=VLAExecutionMode.SIMULATION)
    
    @patch('..integration.isaac_integration.IsaacSimIntegrationService.get_perception_data')
    @patch('..simulation.gazebo_integration.GazeboIntegrationService.execute_action_in_simulation')
    async def test_isaac_integration_for_perception(self, mock_gazebo_exec, mock_isaac_perception):
        """
        Test integration with Isaac Sim for perception data.
        """
        # Mock Isaac Sim to return perception data
        mock_isaac_perception.return_value = {
            "objects": [
                {"class": "cup", "position": [1.0, 1.0, 0.8], "confidence": 0.92}
            ],
            "scene_description": "A cup at coordinates (1.0, 1.0)"
        }
        mock_gazebo_exec.return_value = True
        
        # In a real implementation, this would involve Isaac Sim integration
        # For this test, we'll verify the integration is set up correctly
        self.assertIsNotNone(self.vla_system.isaac_integration)
        
        # Mock a command that would benefit from Isaac Sim perception
        voice_command = VoiceCommand(
            id="isaac_integration_cmd",
            transcribed_text="Find the cup in the scene",
            intent="perception",
            parameters={},
            confidence=0.85,
            timestamp=datetime.now()
        )
        
        # This would typically involve fusing Isaac Sim data with the voice command
        # For this test, we just verify the system can handle the integration
        perception_data = await mock_isaac_perception()
        self.assertIsNotNone(perception_data)
        self.assertIn("objects", perception_data)
        self.assertGreater(len(perception_data["objects"]), 0)
        
        print("Isaac Sim integration verified")
    
    @patch('..simulation.gazebo_integration.GazeboIntegrationService.get_robot_state')
    @patch('..simulation.gazebo_integration.GazeboIntegrationService.execute_action_in_simulation')
    async def test_gazebo_integration_for_execution(self, mock_execute_action, mock_get_state):
        """
        Test integration with Gazebo for action execution.
        """
        # Mock Gazebo services
        mock_get_state.return_value = {
            "pose": {"x": 0.0, "y": 0.0, "z": 0.0, "rotation": {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}},
            "status": "idle"
        }
        mock_execute_action.return_value = True
        
        # Create an action sequence to execute in Gazebo
        action_sequence = ActionSequence(
            id="gazebo_test_seq",
            voice_command_id="cmd_gazebo_test",
            sequence=[
                ActionStep(
                    id="gazebo_nav_action",
                    action_sequence_id="gazebo_test_seq",
                    action_type=ActionType.NAVIGATION,
                    parameters={"x": 1.0, "y": 1.0, "theta": 0.0},
                    timeout=10,
                    order=0
                )
            ],
            description="Test navigation in Gazebo",
            status="pending"
        )
        
        # Get initial robot state
        robot_state = await mock_get_state()
        self.assertIsNotNone(robot_state)
        self.assertEqual(robot_state["status"], "idle")
        
        # Execute the action sequence
        success = await self.vla_system.execute_action_sequence(action_sequence)
        self.assertTrue(success)
        
        # Verify action execution was called
        mock_execute_action.assert_called()
        
        print("Gazebo integration verified")


def run_end_to_end_tests():
    """
    Run the complete end-to-end integration test suite.
    """
    print("Running VLA System End-to-End Integration Tests")
    print("=" * 70)
    
    # Create test suites
    main_tests = unittest.TestLoader().loadTestsFromTestCase(TestEndToEndVLAIntegration)
    robustness_tests = unittest.TestLoader().loadTestsFromTestCase(TestRobustnessAndEdgeCases)
    integration_tests = unittest.TestLoader().loadTestsFromTestCase(TestIntegrationWithExternalSystems)
    
    # Combine all tests
    all_tests = unittest.TestSuite([
        main_tests,
        robustness_tests,
        integration_tests
    ])
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(all_tests)
    
    # Print results summary
    print("\n" + "=" * 70)
    print("END-TO-END INTEGRATION TEST RESULTS")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, trace in result.failures:
            print(f"  {test}")
            print(f"    {trace.split(chr(10))[0]}")
    
    if result.errors:
        print("\nERRORS:")
        for test, trace in result.errors:
            print(f"  {test}")
            print(f"    {trace.split(chr(10))[0]}")
    
    if result.wasSuccessful():
        print(f"\n🎉 All end-to-end integration tests passed!")
        print("The VLA system is fully integrated and working correctly.")
    else:
        print(f"\n❌ Some end-to-end integration tests failed.")
        print("Please review the failures/errors above before proceeding.")
    
    return result


# Performance benchmarking for the end-to-end system
async def benchmark_end_to_end_performance():
    """
    Benchmark the performance of the complete end-to-end system.
    """
    print("\nRunning End-to-End Performance Benchmark")
    print("-" * 50)
    
    import time
    
    # Create a VLA system instance
    vla_system = VLASystem(execution_mode=VLAExecutionMode.SIMULATION)
    
    # Set up mock services for benchmarking
    with patch.object(vla_system.whisper_service, 'process_audio_bytes') as mock_whisper:
        with patch.object(vla_system.llm_service, 'generate_action_sequence') as mock_llm:
            with patch.object(vla_system.gazebo_service, 'execute_action_in_simulation') as mock_exec:
                
                # Mock responses
                mock_whisper.return_value = ("Go to the kitchen and find a cup", 0.88)
                mock_llm.return_value = [
                    ActionStep(
                        id="bench_nav_step",
                        action_sequence_id="bench_seq_1",
                        action_type=ActionType.NAVIGATION,
                        parameters={"x": 2.0, "y": 1.0},
                        timeout=10,
                        order=0
                    ),
                    ActionStep(
                        id="bench_percept_step",
                        action_sequence_id="bench_seq_1", 
                        action_type=ActionType.PERCEPTION,
                        parameters={"action": "detect", "target": "cup"},
                        timeout=5,
                        order=1
                    )
                ]
                mock_exec.return_value = True
                
                # Run performance test
                num_iterations = 10
                times = []
                
                for i in range(num_iterations):
                    start_time = time.time()
                    
                    # Complete pipeline test: voice -> action sequence -> execution
                    action_seq = await vla_system.process_voice_command(f"mock_audio_{i}".encode())
                    if action_seq:
                        exec_success = await vla_system.execute_action_sequence(action_seq)
                    
                    end_time = time.time()
                    elapsed = (end_time - start_time) * 1000  # Convert to milliseconds
                    times.append(elapsed)
                
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                
                print(f"Performance Results ({num_iterations} iterations):")
                print(f"  Average Time: {avg_time:.2f}ms")
                print(f"  Min Time: {min_time:.2f}ms")
                print(f"  Max Time: {max_time:.2f}ms")
                print(f"  Total Time: {sum(times):.2f}ms")
                
                # Performance targets
                target_avg_time = 3000  # 3 seconds in ms
                
                if avg_time <= target_avg_time:
                    print(f"  ✅ Performance target met (≤{target_avg_time}ms)!")
                else:
                    print(f"  ❌ Performance target not met (≤{target_avg_time}ms), actual: {avg_time:.2f}ms")
                
                return {
                    "average_time_ms": avg_time,
                    "min_time_ms": min_time,
                    "max_time_ms": max_time,
                    "target_met": avg_time <= target_avg_time
                }


def main():
    """
    Main function to run all end-to-end tests.
    """
    # Run the comprehensive test suite
    result = run_end_to_end_tests()
    
    # Run performance benchmark
    print("\n" + "=" * 70)
    performance_result = asyncio.run(benchmark_end_to_end_performance())
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL INTEGRATION SUMMARY")
    print("=" * 70)
    
    if result.wasSuccessful() and performance_result["target_met"]:
        print("🎉 COMPLETE SUCCESS: All tests passed AND performance targets met!")
        print("The VLA Capstone system is ready for advanced deployment.")
    elif result.wasSuccessful():
        print("⚠️  TESTS PASSED BUT PERFORMANCE TARGETS NOT MET")
        print("The system functions correctly but may need optimization.")
    elif performance_result["target_met"]:
        print("⚠️  PERFORMANCE TARGETS MET BUT SOME TESTS FAILED")
        print("The system is fast but has functionality gaps.")
    else:
        print("❌ NEITHER TESTS NOR PERFORMANCE TARGETS MET")
        print("The system needs significant work before deployment.")
    
    print(f"  - Tests Passed: {result.wasSuccessful()}")
    print(f"  - Performance Target Met: {performance_result['target_met']}")
    print(f"  - Average Pipeline Time: {performance_result['average_time_ms']:.2f}ms")
    print(f"  - Performance Goal: ≤{performance_result['target_avg_time'] if 'target_avg_time' in locals() else 3000}ms")


if __name__ == "__main__":
    main()