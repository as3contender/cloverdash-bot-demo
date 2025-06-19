from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Конфигурация приложения"""

    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-3.5-turbo"
    openai_temperature: float = 0

    # Database Configuration (можно использовать либо database_url, либо отдельные параметры)
    database_url: Optional[str] = None
    database_host: Optional[str] = None
    database_port: Optional[int] = None
    database_user: Optional[str] = None
    database_password: Optional[str] = None
    database_name: Optional[str] = None
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
        extra = "allow"  # Разрешаем дополнительные поля

    def get_database_url(self) -> str:
        """Получаем URL базы данных из настроек"""
        if self.database_url:
            return self.database_url
        elif all(
            [self.database_host, self.database_port, self.database_user, self.database_password, self.database_name]
        ):
            return f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"
        else:
            # Возвращаем тестовый URL по умолчанию
            return "postgresql://test:test@localhost:5432/test_db"


# Создаем глобальный экземпляр настроек
settings = Settings()

# База данных схема контекст
DB_SCHEMA_CONTEXT = None

try:
    import json

    with open("column_descriptions.json", "r", encoding="utf-8") as file:
        DB_SCHEMA_CONTEXT = json.load(file)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Error loading DB schema context: {e}")
