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
    database_url: str
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
DB_SCHEMA_CONTEXT = """
Доступные таблицы и колонки в базе данных:

Это место для описания схемы базы данных, которое будет передаваться в контекст LLM.
Здесь должно быть описание всех таблиц, их колонок, типов данных и связей.

Пример:
- Таблица users: id (int), name (varchar), email (varchar), created_at (timestamp)
- Таблица orders: id (int), user_id (int), amount (decimal), status (varchar), created_at (timestamp)

Будет расширяться по мере подключения реальной базы данных.
"""
