from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Конфигурация приложения"""

    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-3.5-turbo"
    openai_temperature: float = 0

    # Database Configuration
    database_url: str = f"postgresql://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
    database_echo: bool = False

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "CloverdashBot Backend"
    api_version: str = "1.0.0"

    # Security
    allowed_origins: list[str] = ["*"]

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Создаем глобальный экземпляр настроек
settings = Settings()

# База данных схема контекст
import json

# Load database schema context from column_description.json
with open('column_descriptions.json', 'r', encoding='utf-8') as file:
    DB_SCHEMA_CONTEXT = json.load(file)
