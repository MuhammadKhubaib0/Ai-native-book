"""
Service for processing audio through Whisper for speech-to-text conversion.
"""
import asyncio
import tempfile
import os
from typing import Tuple, Optional
from pathlib import Path
import base64
from ..config import settings
from ..services.whisper_service import WhisperService, WhisperConfig


class WhisperAudioProcessor:
    """
    Service for processing audio data through Whisper for voice command recognition.
    """
    
    def __init__(self):
        # Initialize Whisper service with configuration from settings
        whisper_config = WhisperConfig(
            model_name=settings.whisper_model,
            language=settings.whisper_language
        )
        self.whisper_service = WhisperService(whisper_config)
    
    async def process_audio_bytes(self, audio_data: bytes) -> Tuple[str, float]:
        """
        Process raw audio bytes through Whisper to get transcribed text and confidence.
        
        :param audio_data: Raw audio data as bytes
        :return: Tuple of (transcribed_text, confidence_score)
        """
        # Transcribe the audio data
        transcribed_text, confidence = await self.whisper_service.transcribe_with_confidence(audio_data)
        
        return transcribed_text, confidence
    
    async def process_audio_file(self, file_path: str) -> Tuple[str, float]:
        """
        Process an audio file through Whisper to get transcribed text and confidence.
        
        :param file_path: Path to the audio file
        :return: Tuple of (transcribed_text, confidence_score)
        """
        # Transcribe the audio file
        transcribed_text = await self.whisper_service.transcribe_audio_file(file_path)
        
        # For file input, we return a default confidence since we're not processing raw bytes
        # In a real implementation, you might compute confidence differently for files
        confidence = self.whisper_service._estimate_confidence(transcribed_text)
        
        return transcribed_text, confidence
    
    async def process_audio_with_preprocessing(
        self, 
        audio_data: bytes, 
        apply_preprocessing: bool = True
    ) -> Tuple[str, float]:
        """
        Process audio data with optional preprocessing.
        
        :param audio_data: Raw audio data as bytes
        :param apply_preprocessing: Whether to apply audio preprocessing
        :return: Tuple of (transcribed_text, confidence_score)
        """
        from ..services.audio_preprocessing import AudioPreprocessingService
        
        processed_audio = audio_data
        
        if apply_preprocessing:
            # Apply preprocessing to improve recognition
            processor = AudioPreprocessingService()
            processed_audio = processor.preprocess_audio(audio_data)
        
        # Transcribe the (potentially preprocessed) audio data
        transcribed_text, confidence = await self.whisper_service.transcribe_with_confidence(processed_audio)
        
        return transcribed_text, confidence
    
    def validate_audio_format(self, audio_data: bytes) -> bool:
        """
        Validate that the audio data is in a format suitable for Whisper.
        
        :param audio_data: Raw audio data as bytes
        :return: True if format is valid, False otherwise
        """
        # In a real implementation, you would check the audio format
        # For this example, we'll just check if data exists and has content
        if not audio_data or len(audio_data) == 0:
            return False
        
        # Whisper typically works with WAV, MP3, and other formats
        # You could implement more sophisticated format detection here
        return True


# Alternative class that works directly with Whisper model
class DirectWhisperProcessor:
    """
    Alternative processor that works directly with the Whisper model,
    offering more fine-grained control over the transcription process.
    """
    
    def __init__(self):
        import whisper
        self.model = whisper.load_model(settings.whisper_model)
    
    def transcribe_audio(
        self, 
        audio_data: bytes, 
        language: Optional[str] = None,
        temperature: float = 0.0
    ) -> Tuple[str, float]:
        """
        Directly transcribe audio using the Whisper model.
        
        :param audio_data: Raw audio data as bytes
        :param language: Language of the audio (optional, uses configured default if not provided)
        :param temperature: Temperature for sampling (0.0 for deterministic)
        :return: Tuple of (transcribed_text, confidence_score)
        """
        import io
        import librosa
        import numpy as np
        
        # Save audio data to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(audio_data)
            temp_filename = temp_file.name
        
        try:
            # Load audio using librosa
            audio_array, sr = librosa.load(temp_filename, sr=16000)
            
            # Transcribe using Whisper
            result = self.model.transcribe(
                audio_array,
                language=language or settings.whisper_language,
                temperature=temperature
            )
            
            # In Whisper's implementation, we don't directly get confidence scores
            # We could implement our own confidence estimation based on the transcription result
            text = result["text"]
            confidence = self._estimate_confidence(text, result)
            
            return text, confidence
        finally:
            # Clean up temporary file
            os.unlink(temp_filename)
    
    def _estimate_confidence(self, text: str, transcription_result: dict) -> float:
        """
        Estimate confidence in the transcription based on various heuristics.
        
        :param text: Transcribed text
        :param transcription_result: Full result from Whisper transcription
        :return: Estimated confidence score (0-1)
        """
        # This is a simplified approach
        # In a real implementation, you'd use more sophisticated methods
        
        if not text or len(text.strip()) == 0:
            return 0.0
        
        # If the text is very short, confidence might be lower
        if len(text.strip()) < 3:
            return 0.3
        
        # Check for repeated characters or simple patterns (indicating possible poor recognition)
        unique_chars = set(text.lower())
        if len(unique_chars) < 5:  # Very few unique characters
            return 0.4
        
        # Default confidence for reasonable text
        return 0.8


# Example usage:
if __name__ == "__main__":
    import asyncio
    
    # Example of how to use the WhisperAudioProcessor
    async def example():
        processor = WhisperAudioProcessor()
        
        # Example audio data (this would be actual audio bytes in practice)
        # For demonstration purposes, we'll skip actual audio processing
        example_audio = b"Example audio data"
        
        try:
            # Process audio directly
            text, confidence = await processor.process_audio_bytes(example_audio)
            print(f"Transcribed text: {text}")
            print(f"Confidence: {confidence}")
            
            # Process with preprocessing
            text_pp, confidence_pp = await processor.process_audio_with_preprocessing(example_audio)
            print(f"Transcribed text (with preprocessing): {text_pp}")
            print(f"Confidence (with preprocessing): {confidence_pp}")
            
        except Exception as e:
            print(f"Error in processing: {e}")
    
    # Run the example
    # asyncio.run(example())