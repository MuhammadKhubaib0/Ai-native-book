"""
Service for filtering noise from audio signals to improve voice recognition accuracy.
"""
import numpy as np
from scipy import signal
from typing import Union
import librosa


class NoiseFilter:
    """
    Service for filtering noise from audio signals to improve voice recognition.
    """
    
    def __init__(self):
        # Parameters for various filtering techniques
        self.sample_rate = 16000  # Standard for speech recognition
        self.frame_length = 2048
        self.hop_length = 512
        self.noise_floor_threshold = 0.02  # Adjust based on expected noise levels
    
    def apply_spectral_gate(
        self, 
        audio_signal: np.ndarray, 
        noise_percentile: float = 20.0
    ) -> np.ndarray:
        """
        Apply spectral gating to remove noise from audio signal.
        
        :param audio_signal: Input audio signal as numpy array
        :param noise_percentile: Percentile to use for estimating noise floor (0-100)
        :return: Filtered audio signal
        """
        # Convert to STFT (Short-Time Fourier Transform)
        stft = librosa.stft(audio_signal, n_fft=self.frame_length, hop_length=self.hop_length)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise floor using percentile
        noise_floor = np.percentile(magnitude, noise_percentile, axis=1, keepdims=True)
        
        # Create a mask to suppress noise
        mask = magnitude > noise_floor
        magnitude_filtered = magnitude * mask
        
        # Reconstruct the signal
        stft_filtered = magnitude_filtered * np.exp(1j * phase)
        filtered_signal = librosa.istft(
            stft_filtered, 
            hop_length=self.hop_length, 
            length=len(audio_signal)
        )
        
        return filtered_signal.astype(audio_signal.dtype)
    
    def apply_adaptive_filter(
        self, 
        audio_signal: np.ndarray, 
        reference_noise: np.ndarray = None
    ) -> np.ndarray:
        """
        Apply adaptive filtering to remove noise from audio signal.
        
        :param audio_signal: Input audio signal as numpy array
        :param reference_noise: Reference noise signal (optional, for adaptive filtering)
        :return: Filtered audio signal
        """
        if reference_noise is None:
            # If no reference noise is provided, we'll estimate it
            # by finding the quietest segments in the audio
            reference_noise = self._estimate_noise_profile(audio_signal)
        
        # Basic adaptive filtering using Wiener filtering approach
        # Compute power spectral density estimates
        Pxx = np.abs(np.fft.fft(audio_signal))**2
        Pnn = np.abs(np.fft.fft(reference_noise))**2
        
        # Compute Wiener filter
        H = Pxx / (Pxx + Pnn)
        
        # Apply filter
        filtered_signal = np.fft.ifft(H * np.fft.fft(audio_signal)).real
        
        return filtered_signal.astype(audio_signal.dtype)
    
    def _estimate_noise_profile(self, audio_signal: np.ndarray) -> np.ndarray:
        """
        Estimate the noise profile from the audio signal.
        
        :param audio_signal: Input audio signal
        :return: Estimated noise profile
        """
        # For simplicity, we'll take the first 10% of the signal as noise estimate
        # In practice, you'd use more sophisticated noise estimation techniques
        noise_length = int(0.1 * len(audio_signal))  # 10% of signal
        return audio_signal[:noise_length]
    
    def apply_bandpass_filter(
        self, 
        audio_signal: np.ndarray, 
        low_freq: float = 300.0, 
        high_freq: float = 3400.0
    ) -> np.ndarray:
        """
        Apply a bandpass filter to focus on human voice frequencies.
        
        :param audio_signal: Input audio signal
        :param low_freq: Low cutoff frequency (Hz)
        :param high_freq: High cutoff frequency (Hz)
        :return: Filtered audio signal
        """
        nyquist = self.sample_rate / 2
        low = low_freq / nyquist
        high = high_freq / nyquist
        
        # Design a Butterworth bandpass filter
        b, a = signal.butter(4, [low, high], btype='band', fs=self.sample_rate)
        
        # Apply the filter
        filtered_signal = signal.filtfilt(b, a, audio_signal)
        
        return filtered_signal.astype(audio_signal.dtype)
    
    def apply_simple_gate(self, audio_signal: np.ndarray) -> np.ndarray:
        """
        Apply a simple noise gate based on amplitude threshold.
        
        :param audio_signal: Input audio signal
        :return: Filtered audio signal
        """
        # Calculate the RMS (root mean square) for each frame
        frame_size = 1024
        frames = librosa.util.frame(audio_signal, frame_length=frame_size, hop_length=frame_size)
        rms = librosa.feature.rms(y=audio_signal)[0]
        
        # Create a mask based on the threshold
        threshold_mask = rms > self.noise_floor_threshold
        
        # Upsample the mask to match audio length
        upsampled_mask = np.repeat(threshold_mask, frame_size)
        
        # Apply the mask to the original signal
        filtered_signal = audio_signal * upsampled_mask[:len(audio_signal)]
        
        return filtered_signal.astype(audio_signal.dtype)
    
    def filter_audio(self, audio_data: Union[np.ndarray, bytes], filter_type: str = "spectral_gate") -> np.ndarray:
        """
        Apply the specified noise filter to audio data.
        
        :param audio_data: Audio data as numpy array or bytes
        :param filter_type: Type of filter to apply ("spectral_gate", "adaptive", "bandpass", "simple_gate")
        :return: Filtered audio signal as numpy array
        """
        if isinstance(audio_data, bytes):
            # Convert bytes to numpy array
            # This assumes WAV format - in practice you'd need to decode properly
            import io
            from scipy.io import wavfile
            audio_io = io.BytesIO(audio_data)
            _, audio_signal = wavfile.read(audio_io)
        else:
            audio_signal = audio_data.astype(np.float32)
        
        # Normalize if needed
        if audio_signal.dtype == np.int16:
            audio_signal = audio_signal.astype(np.float32) / 32768.0
        
        # Apply the selected filter
        if filter_type == "spectral_gate":
            return self.apply_spectral_gate(audio_signal)
        elif filter_type == "adaptive":
            return self.apply_adaptive_filter(audio_signal)
        elif filter_type == "bandpass":
            return self.apply_bandpass_filter(audio_signal)
        elif filter_type == "simple_gate":
            return self.apply_simple_gate(audio_signal)
        else:
            raise ValueError(f"Unknown filter type: {filter_type}")


class AdvancedNoiseFilter(NoiseFilter):
    """
    Advanced noise filtering with additional techniques.
    """
    
    def __init__(self):
        super().__init__()
        # Additional parameters for advanced techniques
        self.snr_threshold = 10  # Signal-to-noise ratio threshold in dB
    
    def apply_ml_noise_reduction(self, audio_signal: np.ndarray) -> np.ndarray:
        """
        Apply machine learning-based noise reduction.
        
        Note: This is a conceptual implementation.
        In practice, you would integrate with a trained model like RNNoise or similar.
        
        :param audio_signal: Input audio signal
        :return: Denoised audio signal
        """
        # This is a placeholder implementation
        # In a real implementation, you'd use a trained ML model
        # For example, RNNoise, SEGAN, or other deep learning models
        
        # For now, we'll just apply a simple spectral gate as a placeholder
        return self.apply_spectral_gate(audio_signal)
    
    def compute_snr(self, audio_signal: np.ndarray) -> float:
        """
        Compute an estimate of the signal-to-noise ratio.
        
        :param audio_signal: Input audio signal
        :return: SNR in dB
        """
        # Simple SNR estimation
        # This is a basic estimate and not accurate for all types of noise
        signal_power = np.mean(audio_signal ** 2)
        noise_power = np.var(audio_signal)  # Assuming noise is variation around mean
        
        if noise_power == 0:
            return float('inf')  # Perfect SNR
        
        snr_linear = signal_power / noise_power
        snr_db = 10 * np.log10(snr_linear)
        
        return snr_db


# Example usage:
if __name__ == "__main__":
    # Create a simple test signal with noise
    sample_rate = 16000
    duration = 1.0  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create a simple audio signal (sine wave with noise)
    signal_freq = 500  # Hz
    clean_signal = 0.5 * np.sin(2 * np.pi * signal_freq * t)
    noise = 0.1 * np.random.normal(size=clean_signal.shape)
    noisy_signal = clean_signal + noise
    
    # Create noise filter
    noise_filter = NoiseFilter()
    
    # Apply different types of filtering
    filtered_spectrum = noise_filter.apply_spectral_gate(noisy_signal)
    filtered_bandpass = noise_filter.apply_bandpass_filter(noisy_signal)
    filtered_gate = noise_filter.apply_simple_gate(noisy_signal)
    
    print("Noise filtering applied successfully")
    print(f"Original signal shape: {noisy_signal.shape}")
    print(f"Filtered signal shapes: {filtered_spectrum.shape}, {filtered_bandpass.shape}, {filtered_gate.shape}")
    
    # Compute SNR for original and filtered signals
    advanced_filter = AdvancedNoiseFilter()
    original_snr = advanced_filter.compute_snr(noisy_signal)
    filtered_snr = advanced_filter.compute_snr(filtered_spectrum)
    print(f"Original SNR: {original_snr:.2f} dB")
    print(f"Filtered SNR: {filtered_snr:.2f} dB")