from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Конфигурация приложения"""

    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    openai_temperature: float = 0
    openai_base_url: Optional[str] = None  # Для использования прокси или альтернативных эндпоинтов
    openai_proxy: Optional[str] = None  # Прокси в формате http://proxy:port

    # Application Database Configuration (для пользователей, истории, настроек)
    app_database_url: Optional[str] = None
    app_database_host: Optional[str] = None
    app_database_port: Optional[int] = None
    app_database_user: Optional[str] = None
    app_database_password: Optional[str] = None
    app_database_name: Optional[str] = None
    app_database_echo: bool = False

    # Data Database Configuration (для пользовательских данных и запросов)
    data_database_url: Optional[str] = None
    data_database_host: Optional[str] = None
    data_database_port: Optional[int] = None
    data_database_user: Optional[str] = None
    data_database_password: Optional[str] = None
    data_database_name: Optional[str] = None
    data_database_echo: bool = False

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "CloverdashBot Backend"
    api_version: str = "1.0.0"

    # Security
    allowed_origins: list[str] = ["*"]

    # Authentication
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30 * 24 * 60  # 30 дней

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # Разрешаем дополнительные поля

    def get_app_database_url(self) -> str:
        """Получаем URL базы данных приложения из настроек"""
        if self.app_database_url:
            return self.app_database_url
        elif all(
            [
                self.app_database_host,
                self.app_database_port,
                self.app_database_user,
                self.app_database_password,
                self.app_database_name,
            ]
        ):
            return f"postgresql://{self.app_database_user}:{self.app_database_password}@{self.app_database_host}:{self.app_database_port}/{self.app_database_name}"
        else:
            raise ValueError(
                "Application database configuration is incomplete. Please set either APP_DATABASE_URL or all individual APP_DATABASE_* parameters."
            )

    def get_data_database_url(self) -> str:
        """Получаем URL базы данных пользовательских данных из настроек"""
        if self.data_database_url:
            return self.data_database_url
        elif all(
            [
                self.data_database_host,
                self.data_database_port,
                self.data_database_user,
                self.data_database_password,
                self.data_database_name,
            ]
        ):
            return f"postgresql://{self.data_database_user}:{self.data_database_password}@{self.data_database_host}:{self.data_database_port}/{self.data_database_name}"
        else:
            raise ValueError(
                "Data database configuration is incomplete. Please set either DATA_DATABASE_URL or all individual DATA_DATABASE_* parameters."
            )


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
