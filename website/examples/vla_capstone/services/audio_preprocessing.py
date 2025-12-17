"""
Service for preprocessing audio data before sending to Whisper for recognition.
"""
import numpy as np
import scipy.signal
import io
from pydub import AudioSegment
from typing import Union, Tuple
import librosa


class AudioPreprocessingService:
    """
    Service for preprocessing audio data to improve voice recognition accuracy.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,  # Standard for speech recognition
        channels: int = 1,         # Mono
        chunk_size: int = 1024
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
    
    def preprocess_audio(
        self,
        audio_data: Union[bytes, str, np.ndarray],
        input_sample_rate: int = None
    ) -> bytes:
        """
        Preprocess audio data for Whisper recognition.
        
        :param audio_data: Audio data as bytes, file path, or numpy array
        :param input_sample_rate: Sample rate of input audio if numpy array
        :return: Processed audio data as bytes in WAV format
        """
        # Convert to AudioSegment for processing
        if isinstance(audio_data, str):
            # File path
            audio = AudioSegment.from_file(audio_data)
        elif isinstance(audio_data, bytes):
            # Raw bytes
            audio = AudioSegment.from_file(io.BytesIO(audio_data))
        elif isinstance(audio_data, np.ndarray):
            # NumPy array
            if input_sample_rate is None:
                raise ValueError("input_sample_rate must be provided when using numpy array")
            audio = self._numpy_to_audio_segment(audio_data, input_sample_rate)
        else:
            raise ValueError(f"Unsupported audio data type: {type(audio_data)}")
        
        # Apply preprocessing steps
        audio = self._normalize_audio(audio)
        audio = self._apply_noise_reduction(audio)
        audio = self._adjust_volume(audio)
        
        # Set target sample rate and channels
        audio = audio.set_frame_rate(self.sample_rate)
        audio = audio.set_channels(self.channels)
        
        # Export as WAV bytes
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        return wav_io.getvalue()
    
    def _numpy_to_audio_segment(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> AudioSegment:
        """
        Convert numpy array to AudioSegment.
        
        :param audio_data: Audio data as numpy array
        :param sample_rate: Sample rate of the audio
        :return: AudioSegment object
        """
        # Ensure audio_data is in the right format (mono, 16-bit)
        if audio_data.dtype != np.int16:
            # Normalize to [-1, 1] then scale to int16 range
            audio_data = np.clip(audio_data, -1, 1)
            audio_data = (audio_data * 32767).astype(np.int16)
        
        # Convert to bytes
        raw_data = audio_data.tobytes()
        
        # Create AudioSegment
        audio = AudioSegment(
            data=raw_data,
            sample_width=2,  # 16-bit
            frame_rate=sample_rate,
            channels=1
        )
        
        return audio
    
    def _normalize_audio(self, audio: AudioSegment) -> AudioSegment:
        """
        Normalize audio to a standard level.
        
        :param audio: Input audio segment
        :return: Normalized audio segment
        """
        # Normalize to -20 dB
        normalized = audio.normalize(headroom=0.1)
        return normalized
    
    def _apply_noise_reduction(self, audio: AudioSegment) -> AudioSegment:
        """
        Apply basic noise reduction to the audio.
        
        :param audio: Input audio segment
        :return: Noise-reduced audio segment
        """
        # For now, we'll implement a simple noise gate approach
        # In practice, you might use more sophisticated techniques
        samples = np.array(audio.get_array_of_samples())
        
        # Find the median value as a baseline for noise
        noise_floor = np.median(np.abs(samples))
        
        # Apply a simple noise threshold
        # Set values below noise floor to 0
        mask = np.abs(samples) > noise_floor
        filtered_samples = samples * mask
        
        # Convert back to AudioSegment
        filtered_audio = audio._spawn(filtered_samples.astype(np.int16).tobytes())
        
        return filtered_audio
    
    def _adjust_volume(self, audio: AudioSegment) -> AudioSegment:
        """
        Adjust volume to optimal level for speech recognition.
        
        :param audio: Input audio segment
        :return: Volume-adjusted audio segment
        """
        # Target dBFS for optimal speech recognition
        target_dBFS = -20.0
        
        # Calculate required change in volume
        current_dBFS = audio.dBFS
        change_dBFS = target_dBFS - current_dBFS
        
        # Apply volume change
        adjusted_audio = audio.apply_gain(change_dBFS)
        
        return adjusted_audio
    
    def detect_voice_activity(
        self,
        audio_data: Union[bytes, str, np.ndarray],
        threshold: float = 0.02,
        chunk_duration: float = 0.1  # 100ms chunks
    ) -> list[Tuple[float, float]]:
        """
        Detect voice activity in the audio and return time intervals of speech.
        
        :param audio_data: Audio data to analyze
        :param threshold: Energy threshold for voice detection
        :param chunk_duration: Duration of chunks to analyze (in seconds)
        :return: List of tuples with (start_time, end_time) for speech segments
        """
        # Load audio
        if isinstance(audio_data, str):
            audio = AudioSegment.from_file(audio_data)
        elif isinstance(audio_data, bytes):
            audio = AudioSegment.from_file(io.BytesIO(audio_data))
        elif isinstance(audio_data, np.ndarray):
            audio = self._numpy_to_audio_segment(audio_data, self.sample_rate)
        
        # Convert to numpy for processing
        samples = np.array(audio.get_array_of_samples())
        sample_rate = audio.frame_rate
        chunk_size = int(chunk_duration * sample_rate)
        
        speech_intervals = []
        in_speech = False
        speech_start = 0
        
        # Process in chunks
        for i in range(0, len(samples), chunk_size):
            chunk = samples[i:i + chunk_size]
            
            # Calculate RMS energy
            rms = np.sqrt(np.mean(chunk ** 2))
            
            # Check if above threshold
            if rms > threshold and not in_speech:
                # Start of speech
                speech_start = i / sample_rate
                in_speech = True
            elif rms <= threshold and in_speech:
                # End of speech
                speech_end = i / sample_rate
                speech_intervals.append((speech_start, speech_end))
                in_speech = False
        
        # Handle case where speech continues to end
        if in_speech:
            speech_end = len(samples) / sample_rate
            speech_intervals.append((speech_start, speech_end))
        
        return speech_intervals


# Example usage:
if __name__ == "__main__":
    import os
    
    # Create service
    processor = AudioPreprocessingService()
    
    # Example of preprocessing
    # Note: This would require an actual audio file to test
    # For demonstration, we'll just show the interface
    
    # Preprocessing could be done like this:
    # processed_audio = processor.preprocess_audio("path/to/audio.wav")
    
    # Or with bytes:
    # with open("path/to/audio.wav", "rb") as f:
    #     audio_bytes = f.read()
    # processed_audio = processor.preprocess_audio(audio_bytes)
    
    print("AudioPreprocessingService created and ready to use")
    print(f"Sample rate: {processor.sample_rate}Hz")
    print(f"Channels: {processor.channels}")