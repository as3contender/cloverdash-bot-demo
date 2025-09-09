import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class BotConfig:
    """Конфигурация Telegram бота"""

    telegram_token: str
    backend_url: str
    log_level: str = "INFO"
    max_retries: int = 3
    request_timeout: int = 30
    cache_ttl: int = 300  # 5 минут
    max_query_length: int = 2000
    max_records_display: int = 5
    max_sample_records: int = 3


class Config:
    """Центральный класс конфигурации"""

    @staticmethod
    def load_from_env() -> BotConfig:
        """Загрузка конфигурации из переменных окружения"""
        telegram_token = os.getenv("TELEGRAM_TOKEN")
        if not telegram_token:
            raise ValueError("TELEGRAM_TOKEN not found in environment variables")

        return BotConfig(
            telegram_token=telegram_token,
            backend_url=os.getenv("BACKEND_URL", "http://localhost:8000"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            cache_ttl=int(os.getenv("CACHE_TTL", "300")),
            max_query_length=int(os.getenv("MAX_QUERY_LENGTH", "2000")),
            max_records_display=int(os.getenv("MAX_RECORDS_DISPLAY", "5")),
            max_sample_records=int(os.getenv("MAX_SAMPLE_RECORDS", "3")),
        )


# Константы для callback данных
class CallbackData:
    """Константы для callback данных inline кнопок"""

    EXAMPLE_PREFIX = "ex:"

    # Русские примеры
    TIME_RU = "time_ru"
    SALES_RU = "sales_ru"
    BESTSELLER_RU = "bestseller_ru"

    # Английские примеры
    TIME_EN = "time_en"
    SALES_EN = "sales_en"
    BESTSELLER_EN = "bestseller_en"

    # Маппинг на полные запросы
    EXAMPLES_MAP = {
        TIME_RU: "Покажи текущее время",
        SALES_RU: "Какова общая сумма продаж в январе 2025 года?",
        BESTSELLER_RU: "Какой товар продается лучше всего по количеству?",
        TIME_EN: "Show current time",
        SALES_EN: "What is the total sales amount in January 2025?",
        BESTSELLER_EN: "What is the best-selling product by quantity?",
    }


# Константы для emoji и символов
class Emoji:
    """Константы для emoji и специальных символов"""

    SEARCH = "🔍"
    SUCCESS = "✅"
    ERROR = "❌"
    CROSS = "❌"  # Alias for ERROR
    TARGET = "🎯"  # Target emoji for selections
    DATABASE = "📊"
    TABLE = "📋"
    VIEW = "👁️"
    RECORD = "🔹"
    FOLDER = "🗂️"
    LIGHTBULB = "💡"
    GEAR = "⚙️"
    GLOBE = "🌐"
    SPEECH = "💬"
    TOOL = "🔧"
    NULL_VALUE = "∅"
    TIME = "⏱️"

    # Aliases for convenience
    CHECK = "✅"  # Alias for SUCCESS

    # Flag emojis
    FLAG_US = "🇺🇸"
    FLAG_RU = "🇷🇺"
