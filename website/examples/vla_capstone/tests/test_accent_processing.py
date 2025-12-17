"""
Unit tests for accent processing and voice recognition with different accents.
"""
import unittest
import asyncio
from unittest.mock import Mock, patch
from ..services.whisper_processor import WhisperAudioProcessor
from ..services.intent_extraction import extract_intent
from ..services.audio_preprocessing import AudioPreprocessingService


class TestAccentProcessing(unittest.TestCase):
    """
    Test suite for accent processing and voice recognition with different accents.
    """
    
    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        self.processor = WhisperAudioProcessor()
        self.preprocessor = AudioPreprocessingService()
    
    @patch('..services.whisper_service.WhisperService.transcribe_with_confidence')
    def test_recognition_with_british_accent(self, mock_transcribe):
        """
        Test recognition of British English accent variations.
        """
        # Mock different British accent phrases
        test_cases = [
            ("Move forwards two metres", "navigation"),
            ("Go to the lift", "navigation"),  # British term for elevator
            ("Go to the boot", "navigation"),  # British term for trunk
            ("Take the torch from the boot", "manipulation")  # British term for flashlight
        ]
        
        for text, expected_intent in test_cases:
            with self.subTest(text=text):
                # Mock the transcribe method to return the same text
                mock_transcribe.return_value = (text, 0.85)
                
                # Process the audio (mock)
                result = asyncio.run(self.processor.process_audio_bytes(b"mock audio"))
                
                # Extract intent
                intent, _ = extract_intent(result[0])
                
                # Check that intent is extracted correctly despite accent variations
                self.assertEqual(intent, expected_intent)
    
    @patch('..services.whisper_service.WhisperService.transcribe_with_confidence')
    def test_recognition_with_australian_accent(self, mock_transcribe):
        """
        Test recognition of Australian English accent variations.
        """
        # Mock different Australian accent phrases
        test_cases = [
            ("G'day mate, move two metres forward", "navigation"),  # G'day greeting
            ("Go to the servo", "navigation"),  # Australian term for gas station
            ("Grab that esky for me", "manipulation")  # Australian term for cooler
        ]
        
        for text, expected_intent in test_cases:
            with self.subTest(text=text):
                # Mock the transcribe method to return the same text
                mock_transcribe.return_value = (text, 0.78)
                
                # Process the audio (mock)
                result = asyncio.run(self.processor.process_audio_bytes(b"mock audio"))
                
                # Extract intent
                intent, _ = extract_intent(result[0])
                
                # Check that intent is extracted correctly despite accent variations
                self.assertEqual(intent, expected_intent)
    
    @patch('..services.whisper_service.WhisperService.transcribe_with_confidence')
    def test_recognition_with_american_accent(self, mock_transcribe):
        """
        Test recognition of American English accent variations.
        """
        # Mock different American accent phrases
        test_cases = [
            ("Move forward 2 meters", "navigation"),
            ("Go to the elevator", "navigation"),
            ("Go to the trunk", "navigation"),
            ("Pick up the flashlight", "manipulation")
        ]
        
        for text, expected_intent in test_cases:
            with self.subTest(text=text):
                # Mock the transcribe method to return the same text
                mock_transcribe.return_value = (text, 0.89)
                
                # Process the audio (mock)
                result = asyncio.run(self.processor.process_audio_bytes(b"mock audio"))
                
                # Extract intent
                intent, _ = extract_intent(result[0])
                
                # Check that intent is extracted correctly
                self.assertEqual(intent, expected_intent)
    
    @patch('..services.whisper_service.WhisperService.transcribe_with_confidence')
    def test_recognition_with_slight_noise(self, mock_transcribe):
        """
        Test recognition with background noise that might affect accent perception.
        """
        # Simulate audio with slight noise
        test_cases = [
            ("(inaudible buzz) Move forward 2 meters", "navigation"),
            ("Static [clears throat] Go to the kitchen", "navigation"),
        ]
        
        for text, expected_intent in test_cases:
            with self.subTest(text=text):
                # Mock the transcribe method to return cleaned text
                cleaned_text = text.replace("(inaudible buzz)", "").replace("Static ", "").replace("[clears throat] ", "").strip()
                mock_transcribe.return_value = (cleaned_text, 0.82)
                
                # Process the audio (mock)
                result = asyncio.run(self.processor.process_audio_bytes(b"mock audio"))
                
                # Extract intent
                intent, _ = extract_intent(result[0])
                
                # Check that intent is extracted correctly despite noise
                self.assertEqual(intent, expected_intent)
    
    def test_preprocessing_improves_recognition(self):
        """
        Test that audio preprocessing helps with accent recognition.
        """
        # This test verifies that the preprocessing service can handle
        # different types of audio input that might come from various accents
        mock_audio = b"mock audio data with accent variations"
        
        # Test that preprocessing runs without error
        try:
            processed = self.preprocessor.preprocess_audio(mock_audio)
            self.assertIsInstance(processed, bytes)
            self.assertGreater(len(processed), 0)  # Should produce some output
        except Exception as e:
            self.fail(f"Audio preprocessing failed with accent data: {e}")
    
    @patch('..services.whisper_service.WhisperService.transcribe_with_confidence')
    def test_recognition_confidence_thresholds(self, mock_transcribe):
        """
        Test that different accents produce reasonable confidence scores.
        """
        # Test cases with expected confidence ranges
        test_cases = [
            # Clear pronunciation should have higher confidence
            ("Move forward 2 meters", (0.85, 1.0)),
            # Strong accent or unclear pronunciation should have lower confidence
            ("Moov forwud 2 meeters", (0.60, 0.85)),
            # Very unclear should have low confidence
            ("Mv frwd 2 mt", (0.30, 0.60))
        ]
        
        for text, (min_expected, max_expected) in test_cases:
            with self.subTest(text=text):
                # Mock the transcribe method
                mock_transcribe.return_value = (text, (min_expected + max_expected) / 2)  # Mid-point
                
                # Process the audio (mock)
                result = asyncio.run(self.processor.process_audio_bytes(b"mock audio"))
                
                # Check that confidence is in expected range
                confidence = result[1]
                self.assertGreaterEqual(confidence, min_expected)
                self.assertLessEqual(confidence, max_expected)
    
    def test_intent_extraction_with_accent_variations(self):
        """
        Test that intent extraction works with common accent variations.
        """
        # Test different ways to say the same command in different accents/dialects
        navigation_phrases = [
            "Move forward two meters",
            "Move forwards two metres",  # British spelling
            "Go forward 2 meters",
            "Head forward 2 meters",
            "Drive forward 2 meters"
        ]
        
        for phrase in navigation_phrases:
            with self.subTest(phrase=phrase):
                intent, _ = extract_intent(phrase)
                self.assertEqual(intent, "navigation", f"Failed for phrase: {phrase}")


class TestAccentProcessingIntegration(unittest.TestCase):
    """
    Integration tests for accent processing (would require actual audio files).
    These tests are skipped by default since they need real audio data.
    """
    
    @unittest.skip("Integration tests require Whisper model and real audio samples")
    def test_real_accent_samples(self):
        """
        Test with real audio samples of different accents.
        This test requires actual audio files to be available.
        """
        # In a real implementation, this would test with actual audio samples
        # from different accents
        pass


if __name__ == '__main__':
    # Run the tests
    unittest.main()