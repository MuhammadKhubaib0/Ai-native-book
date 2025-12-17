import asyncio
import openai
import whisper
import os
from typing import Optional
from pathlib import Path
from pydantic import BaseModel
import base64
import io
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


class WhisperConfig(BaseModel):
    """Configuration for the Whisper service."""
    api_key: Optional[str] = None
    model_name: str = "base"  # Options: tiny, base, small, medium, large
    api_base: Optional[str] = None  # For Azure OpenAI or custom endpoints
    language: Optional[str] = "en"  # Language for transcription


class WhisperService:
    """
    Service class for handling voice transcription using OpenAI Whisper.
    """
    
    def __init__(self, config: WhisperConfig = None):
        """
        Initialize the Whisper service with configuration.
        
        :param config: WhisperConfig object with service configuration
        """
        self.config = config or WhisperConfig()
        
        # Set OpenAI API key
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required for Whisper service")
        
        openai.api_key = api_key
        
        # Set API base if provided (for Azure OpenAI or custom endpoints)
        if self.config.api_base:
            openai.base_url = self.config.api_base
        
        # Load local Whisper model based on configuration
        self._local_model = whisper.load_model(self.config.model_name)
    
    async def transcribe_audio_file(self, file_path: str) -> str:
        """
        Transcribe an audio file using Whisper.
        
        :param file_path: Path to the audio file
        :return: Transcribed text
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # Use local Whisper model for transcription
        result = self._local_model.transcribe(file_path, language=self.config.language)
        return result["text"]
    
    async def transcribe_audio_data(self, audio_data: bytes) -> str:
        """
        Transcribe raw audio data using Whisper.
        
        :param audio_data: Raw audio data as bytes
        :return: Transcribed text
        """
        # Save audio data to a temporary file
        with io.BytesIO(audio_data) as buffer:
            # Write the bytes to a temporary file
            temp_file = Path("temp_audio.wav")
            with open(temp_file, "wb") as f:
                f.write(audio_data)
            
            try:
                # Use local Whisper model to transcribe
                result = self._local_model.transcribe(str(temp_file), language=self.config.language)
                return result["text"]
            finally:
                # Clean up temporary file
                if temp_file.exists():
                    temp_file.unlink()
    
    async def transcribe_with_confidence(self, audio_data: bytes) -> tuple[str, float]:
        """
        Transcribe audio data and return both text and confidence score.
        
        Note: For now, we return a placeholder confidence score since the 
        current Whisper implementation doesn't provide direct confidence scores.
        In practice, you might implement custom confidence estimation.
        
        :param audio_data: Raw audio data as bytes
        :return: Tuple of (transcribed_text, confidence_score)
        """
        text = await self.transcribe_audio_data(audio_data)
        
        # Placeholder confidence calculation
        # In a real implementation, this would involve more sophisticated analysis
        confidence = self._estimate_confidence(text)
        
        return text, confidence
    
    def _estimate_confidence(self, text: str) -> float:
        """
        Estimate confidence in the transcription based on various heuristics.
        
        :param text: Transcribed text
        :return: Estimated confidence score (0-1)
        """
        # A basic confidence estimation based on length and character variety
        if not text or len(text.strip()) == 0:
            return 0.0
        
        # If the text is very short, confidence might be lower
        if len(text.strip()) < 3:
            return 0.3  # Low confidence for very short text
        
        # Check for repeated characters or simple patterns (indicating possible poor recognition)
        unique_chars = set(text.lower())
        if len(unique_chars) < 5:  # Very few unique characters
            return 0.4  # Low confidence
        
        # More sophisticated confidence estimation would go here
        # This is a simplified approach
        return 0.8  # Default confidence for reasonable text


# Example usage:
if __name__ == "__main__":
    # Configuration
    config = WhisperConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="base"
    )
    
    # Initialize service
    whisper_service = WhisperService(config)
    
    # Example of how to use the service
    # Note: This is conceptual since we don't have actual audio data in this example
    async def example():
        # Example audio data (this would be actual audio bytes in practice)
        example_audio_data = b"Example audio data bytes"
        
        try:
            text, confidence = await whisper_service.transcribe_with_confidence(example_audio_data)
            print(f"Transcribed text: {text}")
            print(f"Confidence: {confidence}")
        except Exception as e:
            print(f"Error in transcription: {e}")
    
    # Run the example
    # asyncio.run(example())