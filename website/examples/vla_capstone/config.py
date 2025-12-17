import os
from typing import Optional
from pydantic import BaseSettings
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    """
    # API Keys
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Whisper Configuration
    whisper_model: str = os.getenv("WHISPER_MODEL", "base")  # Options: tiny, base, small, medium, large
    whisper_language: str = os.getenv("WHISPER_LANGUAGE", "en")
    
    # LLM Configuration
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4-turbo")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "1000"))
    
    # ROS 2 Configuration
    ros_domain_id: int = int(os.getenv("ROS_DOMAIN_ID", "0"))
    
    # Application Configuration
    app_environment: str = os.getenv("ENVIRONMENT", "development")
    debug_mode: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Audio Configuration
    audio_chunk_size: int = int(os.getenv("AUDIO_CHUNK_SIZE", "1024"))
    audio_sample_rate: int = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
    audio_channels: int = int(os.getenv("AUDIO_CHANNELS", "1"))
    
    # Thresholds and Limits
    voice_recognition_threshold: float = float(os.getenv("VOICE_RECOGNITION_THRESHOLD", "0.85"))
    minimum_confidence_score: float = float(os.getenv("MINIMUM_CONFIDENCE_SCORE", "0.70"))
    
    # File paths
    data_directory: str = os.getenv("DATA_DIR", "./data")
    models_directory: str = os.getenv("MODELS_DIR", "./models")
    
    # Service endpoints
    openai_api_base: Optional[str] = os.getenv("OPENAI_API_BASE")
    anthropic_api_base: Optional[str] = os.getenv("ANTHROPIC_API_BASE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def validate_settings():
    """
    Validate that all required settings are properly configured.
    
    :raises ValueError: If any required setting is missing or invalid
    """
    errors = []
    
    # Check for required API keys based on active services
    if not settings.openai_api_key:
        errors.append("OPENAI_API_KEY is required")
    
    # Check model configuration
    valid_whisper_models = ["tiny", "base", "small", "medium", "large"]
    if settings.whisper_model not in valid_whisper_models:
        errors.append(f"WHISPER_MODEL must be one of {valid_whisper_models}")
    
    # Check temperature range
    if not 0.0 <= settings.llm_temperature <= 1.0:
        errors.append("LLM_TEMPERATURE must be between 0.0 and 1.0")
    
    # Check thresholds
    if not 0.0 <= settings.voice_recognition_threshold <= 1.0:
        errors.append("VOICE_RECOGNITION_THRESHOLD must be between 0.0 and 1.0")
    
    if not 0.0 <= settings.minimum_confidence_score <= 1.0:
        errors.append("MINIMUM_CONFIDENCE_SCORE must be between 0.0 and 1.0")
    
    if errors:
        raise ValueError("Configuration errors found:\n" + "\n".join(errors)


# Validate settings on module import
try:
    validate_settings()
except ValueError as e:
    print(f"Configuration warning: {e}")


# Example usage:
if __name__ == "__main__":
    # Print some key settings
    print(f"Environment: {settings.app_environment}")
    print(f"Debug mode: {settings.debug_mode}")
    print(f"Whisper model: {settings.whisper_model}")
    print(f"LLM model: {settings.llm_model}")
    print(f"Voice recognition threshold: {settings.voice_recognition_threshold}")
    
    # Check if API keys are set
    print(f"OpenAI API key set: {'Yes' if settings.openai_api_key else 'No'}")
    print(f"Anthropic API key set: {'Yes' if settings.anthropic_api_key else 'No'}")