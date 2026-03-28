"""
Configuration - Centralized settings with Pydantic
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        extra="allow",
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # ==================== DATABASE ==================== #
    database_url: str = "sqlite:///./gramin_sahayak.db"

    # ==================== API KEYS ==================== #
    # Gemini API (Google)
    GEMINI_API_KEY: str = ""
    
    # Groq API (backup/alternative)
    GROQ_API_KEY: str = ""
    
    # Telegram
    telegram_bot_token: str = ""
    telegram_webhook_url: str = ""
    
    # Weather
    openweather_api_key: str = ""

    # ==================== LLM CONFIGURATION ==================== #
    llm_provider: str = "gemini"  # "gemini" or "groq"
    llm_model: str = "gemini-1.5-flash"  # Gemini model
    groq_model: str = "llama-3.1-8b-instant"  # Groq model
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1000

    # ==================== RAG CONFIGURATION ==================== #
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 5
    
    # ==================== TTS & TRANSLATION ==================== #
    tts_service: str = "gtts"
    elevenlabs_api_key: str = ""
    
    translation_service: str = "google"
    libretranslate_url: str = "http://localhost:5000"

    # ==================== SCHEDULER ==================== #
    advisory_time: str = "08:00"

    # ==================== FILE UPLOAD ==================== #
    max_file_size_mb: int = 10
    upload_dir: str = "./uploads"
    
    # ==================== PATHS ==================== #
    ml_models_path: str = "models"
    rag_data_path: str = "data/pdfs"
    vector_db_path: str = "data/processed/faiss_index"
    audio_upload_path: str = "data/audio_uploads"
    temp_upload_path: str = "data/temp_uploads"

    # ==================== LANGUAGE ==================== #
    default_language: str = "hi"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Convenient exports
settings = get_settings()
DATABASE_URL = settings.database_url