"""
Service for handling audio recording and management in the VLA system.
"""
import asyncio
import pyaudio
import wave
import os
from typing import Optional, Tuple
import numpy as np
from datetime import datetime
from pathlib import Path
import io


class AudioHandler:
    """
    Service for recording, saving, and managing audio data.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1024,
        format_type: int = pyaudio.paInt16
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format_type = format_type
        self.audio_interface = pyaudio.PyAudio()
    
    def __del__(self):
        """Clean up the PyAudio interface."""
        if hasattr(self, 'audio_interface'):
            self.audio_interface.terminate()
    
    def list_audio_devices(self) -> list:
        """
        List all available audio input devices.
        
        :return: List of available input devices with their indices
        """
        devices = []
        for i in range(self.audio_interface.get_device_count()):
            info = self.audio_interface.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:  # Input device
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'channels': info['maxInputChannels'],
                    'defaultSampleRate': info['defaultSampleRate']
                })
        return devices
    
    def record_audio(
        self,
        duration: float = 5.0,
        device_index: Optional[int] = None
    ) -> bytes:
        """
        Record audio for a specified duration.
        
        :param duration: Duration to record in seconds
        :param device_index: Index of the audio input device to use (None for default)
        :return: Recorded audio data as bytes (WAV format)
        """
        # Open a stream for recording
        stream = self.audio_interface.open(
            format=self.format_type,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            input_device_index=device_index
        )
        
        print(f"Recording for {duration} seconds...")
        
        frames = []
        for _ in range(0, int(self.sample_rate / self.chunk_size * duration)):
            data = stream.read(self.chunk_size)
            frames.append(data)
        
        print("Recording finished.")
        
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        
        # Convert to WAV format
        audio_bytes = self._frames_to_wav_bytes(frames)
        
        return audio_bytes
    
    async def record_audio_async(
        self,
        duration: float = 5.0,
        device_index: Optional[int] = None
    ) -> bytes:
        """
        Asynchronously record audio for a specified duration.
        
        :param duration: Duration to record in seconds
        :param device_index: Index of the audio input device to use (None for default)
        :return: Recorded audio data as bytes (WAV format)
        """
        # This is a basic async wrapper; for true async recording,
        # you'd need to use a callback-based approach or a different library
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.record_audio, 
            duration, 
            device_index
        )
    
    def record_until_silence(
        self,
        max_duration: float = 10.0,
        silence_threshold: float = 500,
        silence_duration: float = 1.0,
        device_index: Optional[int] = None
    ) -> bytes:
        """
        Record audio until a period of silence is detected.
        
        :param max_duration: Maximum duration to record in seconds
        :param silence_threshold: Threshold for detecting silence (lower = more sensitive)
        :param silence_duration: Duration of silence required to stop recording (in seconds)
        :param device_index: Index of the audio input device to use (None for default)
        :return: Recorded audio data as bytes (WAV format)
        """
        stream = self.audio_interface.open(
            format=self.format_type,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            input_device_index=device_index
        )
        
        print("Recording until silence...")
        
        frames = []
        silent_frames = 0
        total_frames = 0
        max_frames = int(self.sample_rate / self.chunk_size * max_duration)
        silence_frames = int(self.sample_rate / self.chunk_size * silence_duration)
        
        while total_frames < max_frames:
            data = stream.read(self.chunk_size)
            frames.append(data)
            total_frames += 1
            
            # Convert to numpy array for volume calculation
            audio_data = np.frombuffer(data, dtype=np.int16)
            amplitude = np.sqrt(np.mean(audio_data**2))
            
            if amplitude < silence_threshold:
                silent_frames += 1
                if silent_frames >= silence_frames:
                    print(f"Silence detected. Recording stopped after {total_frames * self.chunk_size / self.sample_rate:.2f}s.")
                    break
            else:
                silent_frames = 0  # Reset silent frame counter
        
        print(f"Recording finished after {total_frames * self.chunk_size / self.sample_rate:.2f}s.")
        
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        
        # Convert to WAV format
        audio_bytes = self._frames_to_wav_bytes(frames)
        
        return audio_bytes
    
    def _frames_to_wav_bytes(self, frames: list) -> bytes:
        """
        Convert recorded frames to WAV format bytes.
        
        :param frames: List of audio frames
        :return: Audio data as WAV bytes
        """
        # Create an in-memory WAV file
        wav_io = io.BytesIO()
        
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(self.audio_interface.get_sample_size(self.format_type))
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(b''.join(frames))
        
        # Get WAV bytes
        wav_bytes = wav_io.getvalue()
        wav_io.close()
        
        return wav_bytes
    
    def save_audio_to_file(self, audio_data: bytes, file_path: str):
        """
        Save audio bytes to a WAV file.
        
        :param audio_data: Audio data as bytes
        :param file_path: Path to save the audio file
        """
        # Ensure the directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(audio_data)
    
    def load_audio_from_file(self, file_path: str) -> bytes:
        """
        Load audio from a WAV file.
        
        :param file_path: Path to the audio file
        :return: Audio data as bytes
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        with open(file_path, 'rb') as f:
            return f.read()


class EnhancedAudioHandler(AudioHandler):
    """
    Enhanced audio handler with additional features like voice activity detection.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1024,
        format_type: int = pyaudio.paInt16,
        vad_threshold: float = 0.02
    ):
        super().__init__(sample_rate, channels, chunk_size, format_type)
        self.vad_threshold = vad_threshold  # Voice Activity Detection threshold
    
    def record_with_vad(
        self,
        max_duration: float = 10.0,
        silence_duration: float = 2.0,
        device_index: Optional[int] = None
    ) -> bytes:
        """
        Record audio with Voice Activity Detection (VAD).
        Only records when voice activity is detected.
        
        :param max_duration: Maximum duration to record in seconds
        :param silence_duration: Duration of silence after which to stop recording
        :param device_index: Index of the audio input device to use (None for default)
        :return: Recorded audio data as bytes (WAV format)
        """
        stream = self.audio_interface.open(
            format=self.format_type,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            input_device_index=device_index
        )
        
        print("Recording with Voice Activity Detection...")
        
        frames = []
        recorded_frames = []
        silent_frames = 0
        total_frames = 0
        max_frames = int(self.sample_rate / self.chunk_size * max_duration)
        silence_frames = int(self.sample_rate / self.chunk_size * silence_duration)
        
        voice_detected = False
        started_recording = False
        
        while total_frames < max_frames:
            data = stream.read(self.chunk_size)
            frames.append(data)
            total_frames += 1
            
            # Convert to numpy array for analysis
            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            audio_data /= np.max(np.abs(audio_data))  # Normalize
            
            # Calculate energy (RMS) of the frame
            energy = np.sqrt(np.mean(audio_data**2))
            
            if energy > self.vad_threshold:
                # Voice activity detected
                voice_detected = True
                if not started_recording:
                    # Start recording from a few frames back to capture the beginning of speech
                    start_idx = max(0, len(frames) - 5)  # Include 5 frames before voice detection
                    recorded_frames = frames[start_idx:]
                    started_recording = True
                else:
                    recorded_frames.append(data)
                
                # Reset silent frame counter when voice is detected
                silent_frames = 0
            elif voice_detected and started_recording:
                # We were recording and now we detected silence
                silent_frames += 1
                recorded_frames.append(data)
                
                if silent_frames >= silence_frames:
                    # Sufficient silence detected, stop recording
                    print(f"Silence after speech detected. Recording stopped.")
                    break
            elif not started_recording:
                # Still in initial silence, continue waiting for voice
                continue
        
        print(f"Recording finished. Recorded {len(recorded_frames) * self.chunk_size / self.sample_rate:.2f}s of audio.")
        
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        
        # If no voice was detected during the entire max duration, return empty bytes
        if not started_recording:
            print("No voice activity detected during the recording period.")
            return b""
        
        # Convert to WAV format
        audio_bytes = self._frames_to_wav_bytes(recorded_frames)
        
        return audio_bytes


# Example usage:
if __name__ == "__main__":
    # Create an audio handler
    audio_handler = AudioHandler()
    
    # List available audio devices
    devices = audio_handler.list_audio_devices()
    print("Available audio devices:")
    for device in devices:
        print(f"  {device['index']}: {device['name']} (Channels: {device['channels']})")
    
    # Example of how to record audio
    # Note: The following would actually record audio from your microphone
    # For safety, we're not running it by default
    
    '''
    # Record for 5 seconds
    print("\nRecording for 5 seconds...")
    audio_data = audio_handler.record_audio(duration=5.0)
    print(f"Recorded {len(audio_data)} bytes of audio data")
    
    # Save to file
    file_path = f"recorded_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    audio_handler.save_audio_to_file(audio_data, file_path)
    print(f"Audio saved to: {file_path}")
    '''
    
    # Example of EnhancedAudioHandler with VAD
    print("\nUsing Enhanced Audio Handler with VAD...")
    enhanced_handler = EnhancedAudioHandler()
    
    # devices = enhanced_handler.list_audio_devices()
    # Use the first available device
    # if devices:
    #     device_index = devices[0]['index']
    #     print(f"Using device: {devices[0]['name']}")
    # else:
    #     device_index = None
    #     print("No input devices found, using default")
    
    print("Ready to record with voice activity detection.")