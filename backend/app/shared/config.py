from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # API Configuration
    API_PREFIX: str = "/api/v1"

    # LLM Generation Settings
    MAX_NEW_TOKENS: int = 100
    TEMPERATURE: float = 0.3  # Lower for more consistent character adherence
    TOP_P: float = 0.8  # More focused responses

    # Assistant Model
    MODEL_ASSISTANT: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

    # Hugging Face Configuration
    HF_HOME: str = "/home/appuser/.cache/huggingface"

    # Database Configuration
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "assistant"

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Global settings instance
settings = Settings()
