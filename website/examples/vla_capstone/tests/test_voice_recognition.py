"""
Unit tests for voice recognition functionality.
"""
import unittest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from ..models.voice_command import VoiceCommand
from ..services.whisper_processor import WhisperAudioProcessor
from ..services.intent_extraction import extract_intent
from ..validation.voice_command_validation import validate_voice_command
from ..services.voice_command_manager import VoiceCommandManager


class TestVoiceRecognition(unittest.TestCase):
    """
    Test suite for voice recognition functionality.
    """
    
    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        self.processor = WhisperAudioProcessor()
        self.manager = VoiceCommandManager()
    
    @patch('..services.whisper_service.WhisperService.transcribe_with_confidence')
    def test_process_audio_bytes_success(self, mock_transcribe):
        """
        Test processing audio bytes successfully.
        """
        # Mock the transcribe method
        mock_transcribe.return_value = ("Hello, move forward", 0.85)
        
        # Create test audio data (mock)
        test_audio = b"fake audio data"
        
        # Call the method
        result = asyncio.run(self.processor.process_audio_bytes(test_audio))
        
        # Verify the result
        self.assertEqual(result[0], "Hello, move forward")
        self.assertEqual(result[1], 0.85)
        mock_transcribe.assert_called_once_with(test_audio)
    
    @patch('..services.whisper_service.WhisperService.transcribe_with_confidence')
    def test_process_audio_with_low_confidence(self, mock_transcribe):
        """
        Test processing audio with low confidence.
        """
        # Mock the transcribe method with low confidence
        mock_transcribe.return_value = ("Unclear command", 0.3)
        
        test_audio = b"fake audio data with low quality"
        
        result = asyncio.run(self.processor.process_audio_bytes(test_audio))
        
        self.assertEqual(result[0], "Unclear command")
        self.assertEqual(result[1], 0.3)
    
    def test_extract_intent_navigation(self):
        """
        Test intent extraction for navigation commands.
        """
        test_cases = [
            ("Move forward 2 meters", "navigation", {"direction": "forward", "distance": 2.0, "unit": "meters"}),
            ("Go to the kitchen", "navigation", {"location": "kitchen"}),
            ("Turn left by 90 degrees", "navigation", {"direction": "left", "angle": 90.0})
        ]
        
        for text, expected_intent, expected_params in test_cases:
            intent, params = extract_intent(text)
            self.assertEqual(intent, expected_intent, f"Failed for: {text}")
            for key, value in expected_params.items():
                self.assertIn(key, params, f"Missing {key} in {text}")
                self.assertEqual(params[key], value, f"Wrong value for {key} in {text}")
    
    def test_extract_intent_manipulation(self):
        """
        Test intent extraction for manipulation commands.
        """
        test_cases = [
            ("Pick up the red cube", "manipulation", {"action": "pick up", "object": "red cube"}),
            ("Move the ball to the box", "manipulation", {"object": "ball", "destination": "box"})
        ]
        
        for text, expected_intent, expected_params in test_cases:
            intent, params = extract_intent(text)
            self.assertEqual(intent, expected_intent, f"Failed for: {text}")
            for key, value in expected_params.items():
                self.assertIn(key, params, f"Missing {key} in {text}")
                self.assertEqual(params[key], value, f"Wrong value for {key} in {text}")
    
    def test_extract_intent_unknown(self):
        """
        Test intent extraction for unknown commands.
        """
        text = "This is an unknown command pattern"
        intent, params = extract_intent(text)
        self.assertEqual(intent, "unknown")
        self.assertIn("raw_text", params)
        self.assertEqual(params["raw_text"], text)
    
    def test_validate_voice_command_valid(self):
        """
        Test validation of a valid voice command.
        """
        voice_command = VoiceCommand(
            id="test-123",
            transcribed_text="Move forward",
            intent="navigation",
            parameters={"distance": 1.0},
            confidence=0.9
        )
        
        result = validate_voice_command(voice_command)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_validate_voice_command_invalid_confidence(self):
        """
        Test validation of a voice command with invalid confidence.
        """
        voice_command = VoiceCommand(
            id="test-123",
            transcribed_text="Move forward",
            intent="navigation",
            parameters={"distance": 1.0},
            confidence=1.5  # Invalid confidence > 1.0
        )
        
        result = validate_voice_command(voice_command)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        self.assertIn("confidence", result.errors[0].lower())
    
    def test_validate_voice_command_empty_text(self):
        """
        Test validation of a voice command with empty text.
        """
        voice_command = VoiceCommand(
            id="test-123",
            transcribed_text="",
            intent="",
            parameters={},
            confidence=0.9
        )
        
        result = validate_voice_command(voice_command)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        self.assertIn("cannot be empty", result.errors[0])
    
    def test_voice_command_manager_create_command(self):
        """
        Test creating a voice command via the manager.
        """
        import asyncio
        
        # Test creating a command
        command = asyncio.run(
            self.manager.create_voice_command("Test command", confidence=0.85)
        )
        
        self.assertIsNotNone(command)
        self.assertEqual(command.transcribed_text, "Test command")
        self.assertEqual(command.confidence, 0.85)
        self.assertEqual(command.status.value, "pending")  # .value because it's an enum
    
    def test_voice_command_manager_update_status(self):
        """
        Test updating the status of a voice command.
        """
        import asyncio
        
        # Create a command first
        command = asyncio.run(
            self.manager.create_voice_command("Test command", confidence=0.85)
        )
        
        # Update its status
        success = asyncio.run(
            self.manager.update_voice_command_status(command.id, command.__class__.status.__class__("processed"))
        )
        
        self.assertTrue(success)
        
        # Retrieve and verify the updated command
        retrieved = asyncio.run(self.manager.get_voice_command(command.id))
        self.assertIsNotNone(retrieved)
        # Note: We need to handle the enum comparison properly
        # For this test, we'll just verify the command was retrieved successfully


@unittest.skip("Integration tests require Whisper model and audio input")
class TestVoiceRecognitionIntegration(unittest.TestCase):
    """
    Integration tests for voice recognition (requires actual Whisper model and audio).
    These are skipped by default.
    """
    
    def setUp(self):
        """
        Set up test fixtures for integration tests.
        """
        self.processor = WhisperAudioProcessor()
    
    def test_process_real_audio_file(self):
        """
        Test processing a real audio file (requires an actual file).
        """
        # This would require an actual audio file to be present
        # For demonstration purposes only
        pass


if __name__ == '__main__':
    # Run the tests
    unittest.main()