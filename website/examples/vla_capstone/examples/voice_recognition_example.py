"""
Python integration example for voice recognition in the VLA Capstone project.
Demonstrates how to integrate voice recognition capabilities with the complete system.
"""
import asyncio
import aiohttp
import numpy as np
import sounddevice as sd
import time
from scipy.io import wavfile
import tempfile
import os
from typing import Dict, Any, Optional
import json

# Import VLA system components
from ..models.voice_command import VoiceCommand, VoiceCommandStatus
from ..models.action_sequence import ActionSequence
from ..services.whisper_processor import WhisperAudioProcessor
from ..services.llm_service import LLMService, LLMConfig
from ..services.vision_integration import VisionIntegrationService
from ..services.multimodal_fusion import MultimodalFusionService
from ..core.vla_system import VLASystem
from ..config import settings


class VoiceRecognitionExample:
    """
    Example implementation of voice recognition integration with the VLA system.
    """
    
    def __init__(self):
        """Initialize the voice recognition example."""
        # Initialize VLA system services
        self.whisper_processor = WhisperAudioProcessor()
        self.llm_service = LLMService(LLMConfig(
            model_name=settings.llm_model,
            temperature=settings.llm_temperature
        ))
        self.vision_service = VisionIntegrationService()
        self.fusion_service = MultimodalFusionService()
        self.vla_system = VLASystem()
        
        # Audio settings
        self.sample_rate = 16000  # Standard for speech recognition
        self.channels = 1
        self.duration = 5  # Record for 5 seconds
        self.device = None  # Use default audio device
    
    def record_audio(self, duration: int = 5) -> bytes:
        """
        Record audio from the microphone.
        
        :param duration: Duration to record in seconds
        :return: Audio data as bytes (WAV format)
        """
        print(f"Recording audio for {duration} seconds...")
        
        # Record audio
        audio_data = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='int16'
        )
        
        # Wait for recording to complete
        sd.wait()
        
        # Convert to bytes (we'll temporarily save to WAV and read back)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        try:
            # Save to temporary file
            wavfile.write(temp_filename, self.sample_rate, audio_data)
            
            # Read the WAV file as bytes
            with open(temp_filename, 'rb') as f:
                audio_bytes = f.read()
            
            return audio_bytes
        finally:
            # Clean up temporary file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
    
    async def process_audio_stream(self, audio_stream: bytes) -> Optional[VoiceCommand]:
        """
        Process an audio stream through the voice recognition pipeline.
        
        :param audio_stream: Audio stream as bytes
        :return: Processed voice command or None if processing failed
        """
        try:
            print("Processing audio stream through voice recognition pipeline...")
            
            # Step 1: Process audio with Whisper
            transcription, confidence = await self.whisper_processor.process_audio_bytes(audio_stream)
            
            if confidence < settings.minimum_confidence_score:
                print(f"Transcription confidence {confidence:.3f} below threshold {settings.minimum_confidence_score}")
                return None
            
            print(f"Transcription: '{transcription}' (confidence: {confidence:.3f})")
            
            # Step 2: Create voice command object
            voice_command = VoiceCommand(
                id=f"cmd_{int(time.time() * 1000)}",
                transcribed_text=transcription,
                confidence=confidence,
                intent="",  # Will be filled by LLM processing
                parameters={},
                timestamp=time.time()
            )
            
            return voice_command
            
        except Exception as e:
            print(f"Error processing audio stream: {str(e)}")
            return None
    
    async def process_voice_command_with_vla_system(self, voice_command: VoiceCommand) -> Optional[ActionSequence]:
        """
        Process a voice command through the complete VLA system pipeline.
        
        :param voice_command: The voice command to process
        :return: Action sequence or None if processing failed
        """
        try:
            print(f"Processing voice command through VLA system: '{voice_command.transcribed_text}'")
            
            # Use the VLA system to generate action sequence from the voice command
            # In a real implementation, this would directly use the VLA system's method
            # For this example, we'll simulate the process
            
            # Generate action sequence using LLM (simulated)
            action_steps = await self.llm_service.generate_action_sequence(
                intent="command_interpretation",
                parameters={
                    "command": voice_command.transcribed_text,
                    "context": {"environment": "simulated", "capabilities": ["navigation", "manipulation", "perception"]}
                }
            )
            
            if not action_steps:
                print("LLM did not generate any action steps")
                return None
            
            # Create action sequence
            action_sequence = ActionSequence(
                id=f"seq_{int(time.time() * 1000)}",
                voice_command_id=voice_command.id,
                sequence=action_steps,
                description=f"Generated from command: {voice_command.transcribed_text}",
                status=ActionSequenceStatus.PENDING
            )
            
            print(f"Generated action sequence with {len(action_sequence.sequence)} steps")
            
            return action_sequence
            
        except Exception as e:
            print(f"Error processing voice command through VLA system: {str(e)}")
            return None
    
    async def run_voice_recognition_example(self):
        """
        Run the complete voice recognition integration example.
        """
        print("Starting VLA Capstone Voice Recognition Example")
        print("=" * 60)
        
        try:
            # Record audio from microphone
            audio_bytes = self.record_audio(duration=5)
            
            if not audio_bytes:
                print("Failed to record audio")
                return
            
            print(f"Recorded {len(audio_bytes)} bytes of audio data")
            
            # Process the audio through voice recognition
            voice_command = await self.process_audio_stream(audio_bytes)
            
            if not voice_command:
                print("Failed to process voice command")
                return
            
            print(f"Recognized voice command: '{voice_command.transcribed_text}'")
            print(f"Confidence: {voice_command.confidence:.3f}")
            
            # Process through complete VLA pipeline
            action_sequence = await self.process_voice_command_with_vla_system(voice_command)
            
            if not action_sequence:
                print("Failed to generate action sequence")
                return
            
            print(f"Generated action sequence with {len(action_sequence.sequence)} steps:")
            for i, step in enumerate(action_sequence.sequence):
                print(f"  {i+1}. {step.action_type.value}: {step.parameters}")
            
            # For simulation, we'll not execute the actions
            print("Action sequence ready for execution in simulation!")
            
        except KeyboardInterrupt:
            print("\nExample interrupted by user")
        except Exception as e:
            print(f"Error running example: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def demonstrate_api_integration(self):
        """
        Demonstrate how to integrate with the VLA system through API calls.
        """
        print("Demonstrating API integration...")
        
        # Example API call to process voice command
        api_endpoint = f"http://localhost:{settings.server_port}/vla/process_command"
        
        # In a real implementation, you would send the audio data to the API
        # For this example, we'll just show the API structure
        
        example_request = {
            "audio_data": "base64_encoded_audio_data",  # Actually base64 encoded
            "context": {
                "environment": "simulated",
                "robot_capabilities": ["navigation", "manipulation", "perception"]
            }
        }
        
        example_response = {
            "execution_id": "exec_123456",
            "success": True,
            "action_sequence": {
                "id": "seq_789",
                "steps": [
                    {
                        "id": "step_1",
                        "action_type": "navigation",
                        "parameters": {"x": 1.0, "y": 0.5},
                        "timeout": 10
                    },
                    {
                        "id": "step_2", 
                        "action_type": "manipulation",
                        "parameters": {"action": "grasp", "object_id": "red_cup"},
                        "timeout": 15
                    }
                ]
            },
            "confidence": 0.87
        }
        
        print("Sample API request structure:")
        print(json.dumps(example_request, indent=2))
        
        print("\nSample API response structure:")
        print(json.dumps(example_response, indent=2))
        
        print("\nActual API integration would require:")
        print("1. Sending POST request to the API endpoint")
        print("2. Handling audio data as base64 encoded string")
        print("3. Processing the returned action sequence")
        print("4. Executing the sequence in simulation")


class AdvancedVoiceRecognitionExample(VoiceRecognitionExample):
    """
    Advanced example with additional features like continuous recognition and noise filtering.
    """
    
    def __init__(self):
        super().__init__()
        self.continuous_recognition = False
        self.noise_filtering_enabled = True
        self.silence_threshold = 0.01
        self.max_recording_duration = 10.0
        self.vad_enabled = True  # Voice activity detection
    
    def is_silent(self, audio_data: np.ndarray, threshold: float = 0.01) -> bool:
        """
        Check if the audio data is silent (below threshold).
        
        :param audio_data: Audio data as numpy array
        :param threshold: Silence threshold
        :return: True if audio is silent, False otherwise
        """
        if audio_data.size == 0:
            return True
        
        # Calculate RMS (Root Mean Square) as a measure of audio power
        rms = np.sqrt(np.mean(audio_data.astype(float) ** 2))
        return rms < threshold
    
    def detect_voice_activity(self, audio_data: np.ndarray, window_size: int = 1024) -> bool:
        """
        Simple voice activity detection based on energy.
        
        :param audio_data: Audio data as numpy array
        :param window_size: Size of analysis window
        :return: True if voice activity detected, False otherwise
        """
        if len(audio_data) < window_size:
            # Calculate energy for the whole segment
            energy = np.mean(audio_data.astype(float) ** 2)
        else:
            # Calculate energy in sliding windows
            energies = []
            for i in range(0, len(audio_data) - window_size, window_size//2):
                window = audio_data[i:i+window_size]
                energy = np.mean(window.astype(float) ** 2)
                energies.append(energy)
            
            # Voice activity if average energy in any window exceeds threshold
            avg_energy = np.mean(energies) if energies else 0
            # Dynamic threshold based on overall signal power
            dynamic_threshold = np.std(audio_data) * 0.5
            
            return avg_energy > dynamic_threshold
    
    async def record_until_voice_activity(self, max_duration: float = 10.0) -> Optional[bytes]:
        """
        Record audio until voice activity is detected (or timeout occurs).
        
        :param max_duration: Maximum recording duration in seconds
        :return: Audio data as bytes if voice detected, None otherwise
        """
        print(f"Listening for voice activity (timeout: {max_duration}s)...")
        
        # Calculate total frames to record
        total_frames = int(max_duration * self.sample_rate)
        chunk_frames = int(0.1 * self.sample_rate)  # 100ms chunks
        
        all_audio_data = []
        voice_detected = False
        start_time = time.time()
        
        # Callback for continuous recording
        def audio_callback(indata, frames, time, status):
            nonlocal voice_detected
            if status:
                print(f"Audio stream status: {status}")
            
            # Convert to int16 array
            audio_chunk = indata[:, 0].copy()  # Take first channel if stereo
            
            # Check for voice activity
            if self.vad_enabled:
                if self.detect_voice_activity(audio_chunk):
                    voice_detected = True
                    print("Voice activity detected!")
                
                # If voice detected, start recording
                if voice_detected:
                    all_audio_data.append(audio_chunk)
            else:
                # Record all audio if VAD disabled
                all_audio_data.append(audio_chunk)
            
            # Check for timeout
            if time.time() - start_time > max_duration:
                print("Max duration reached")
                return
        
        try:
            # Use callback approach for continuous recording until voice activity
            stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='int16',
                callback=audio_callback,
                blocksize=chunk_frames
            )
            
            with stream:
                while time.time() - start_time < max_duration:
                    if voice_detected and not self.vad_enabled:
                        break  # Break if voice was detected and we're recording everything
                    time.sleep(0.01)  # Small sleep to prevent busy waiting
            
            if not all_audio_data:
                print("No audio data recorded")
                return None
            
            # Combine all recorded chunks
            full_audio = np.concatenate(all_audio_data)
            
            # Save to temporary file and return as bytes
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            try:
                wavfile.write(temp_filename, self.sample_rate, full_audio)
                
                with open(temp_filename, 'rb') as f:
                    audio_bytes = f.read()
                
                return audio_bytes
            finally:
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                    
        except Exception as e:
            print(f"Error in voice activity detection: {str(e)}")
            return None
    
    async def run_continuous_recognition_example(self):
        """
        Run an example of continuous voice recognition.
        """
        print("Starting Continuous Voice Recognition Example")
        print("=" * 60)
        
        try:
            # Record until voice activity is detected
            audio_bytes = await self.record_until_voice_activity(max_duration=10.0)
            
            if not audio_bytes:
                print("No voice activity detected or recording failed")
                return
            
            print(f"Recorded {len(audio_bytes)} bytes after voice activity detection")
            
            # Process audio
            voice_command = await self.process_audio_stream(audio_bytes)
            
            if not voice_command:
                print("Failed to process voice command")
                return
            
            print(f"Recognized: '{voice_command.transcribed_text}' with confidence {voice_command.confidence:.3f}")
            
            # Process through VLA system
            action_sequence = await self.process_voice_command_with_vla_system(voice_command)
            
            if action_sequence:
                print(f"Generated action sequence with {len(action_sequence.sequence)} steps")
                for i, step in enumerate(action_sequence.sequence):
                    print(f"  Step {i+1}: {step.action_type.value} - {step.parameters}")
            else:
                print("Failed to generate action sequence")
        
        except KeyboardInterrupt:
            print("\nContinuous recognition interrupted by user")
        except Exception as e:
            print(f"Error in continuous recognition: {str(e)}")
            import traceback
            traceback.print_exc()


def run_voice_recognition_examples():
    """
    Run the voice recognition integration examples.
    """
    print("VLA Capstone - Voice Recognition Integration Examples")
    print("=" * 80)
    
    # Basic example
    print("\n[1] Running Basic Voice Recognition Example...")
    basic_example = VoiceRecognitionExample()
    asyncio.run(basic_example.run_voice_recognition_example())
    
    print("\n" + "-" * 80)
    
    # API integration demonstration
    print("\n[2] API Integration Demonstration...")
    basic_example.demonstrate_api_integration()
    
    print("\n" + "-" * 80)
    
    # Advanced example with voice activity detection
    print("\n[3] Running Advanced Voice Recognition Example (with Voice Activity Detection)...")
    advanced_example = AdvancedVoiceRecognitionExample()
    asyncio.run(advanced_example.run_continuous_recognition_example())
    
    print("\n" + "=" * 80)
    print("Voice Recognition Integration Examples Completed!")


# Example of using the VLA system API directly
async def api_integration_example():
    """
    Example of integrating voice recognition through the VLA system API.
    """
    import aiohttp
    
    # Create audio data (this would normally come from a microphone)
    # For this example, we'll use a mock audio file or generate a simple tone
    sample_rate = 16000
    duration = 2  # seconds
    frequency = 440  # Hz (A4 note)
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_wave = np.sin(2 * np.pi * frequency * t)
    audio_data = (audio_wave * 32767).astype(np.int16)  # Convert to 16-bit
    
    # Convert to WAV bytes
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
        wavfile.write(tmp_file.name, sample_rate, audio_data)
        with open(tmp_file.name, 'rb') as f:
            wav_bytes = f.read()
        os.unlink(tmp_file.name)
    
    # Encode audio as base64 for API
    import base64
    audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')
    
    # Prepare API request
    api_request = {
        "audio_data": audio_base64,
        "context": {
            "environment": "simulated",
            "robot_capabilities": ["navigation", "manipulation", "perception"]
        }
    }
    
    # Make API request (assuming the VLA system API is running)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'http://localhost:{settings.server_port}/vla/process_command',
                json=api_request
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("API Response:")
                    print(json.dumps(result, indent=2))
                else:
                    print(f"API request failed with status {response.status}")
                    response_text = await response.text()
                    print(f"Response: {response_text}")
                    
    except Exception as e:
        print(f"Error making API request: {str(e)}")


# Example of batch processing multiple commands
async def batch_processing_example():
    """
    Example of batch processing multiple voice commands.
    """
    print("Batch Processing Multiple Voice Commands Example")
    print("-" * 60)
    
    # Sample commands to process
    sample_commands = [
        "Go to the kitchen",
        "Pick up the red cup", 
        "Find the blue ball",
        "Move forward 2 meters",
        "Turn left 90 degrees"
    ]
    
    # In a real system, these would be actual audio recordings
    # For this example, we'll simulate the process
    vla_system = VLASystem()
    
    results = []
    for i, command_text in enumerate(sample_commands):
        print(f"Processing command {i+1}/{len(sample_commands)}: '{command_text}'")
        
        # In a real implementation, each command would be converted to audio
        # and processed through the full pipeline
        # For simulation, we'll create a mock voice command
        
        mock_voice_command = VoiceCommand(
            id=f"mock_cmd_{i}",
            transcribed_text=command_text,
            confidence=0.9,  # High confidence for mock data
            intent="navigation" if "go" in command_text.lower() or "move" in command_text.lower() else 
                    "manipulation" if "pick" in command_text.lower() or "grasp" in command_text.lower() else
                    "perception",
            parameters={},
            timestamp=time.time()
        )
        
        # Process through VLA system (simulated)
        print(f"  Generated action sequence for: {command_text}")
        
        results.append({
            "command": command_text,
            "processed": True,
            "timestamp": datetime.now().isoformat()
        })
    
    print(f"\nProcessed {len(results)} commands successfully")
    
    # Print summary
    print("\nBatch Processing Summary:")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result['command']}")


if __name__ == "__main__":
    # Run the main example
    run_voice_recognition_examples()
    
    print("\n" + "=" * 80)
    print("Additional Examples:")
    
    # Run API integration example
    print("\n[4] API Integration Example...")
    asyncio.run(api_integration_example())
    
    # Run batch processing example
    print("\n[5] Batch Processing Example...")
    asyncio.run(batch_processing_example())
    
    print("\nAll voice recognition integration examples completed!")