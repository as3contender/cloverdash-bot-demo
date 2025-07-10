"""
Тесты для конфигурации
"""

import os
import pytest
from unittest.mock import patch
from config import Config, BotConfig, CallbackData, Emoji
from exceptions import ConfigurationError


class TestBotConfig:
    """Тесты для BotConfig"""

    def test_bot_config_creation(self):
        """Тест создания конфигурации"""
        config = BotConfig(telegram_token="123:ABC", backend_url="http://localhost:8000")

        assert config.telegram_token == "123:ABC"
        assert config.backend_url == "http://localhost:8000"
        assert config.log_level == "INFO"
        assert config.max_retries == 3
        assert config.request_timeout == 30
        assert config.cache_ttl == 300
        assert config.max_query_length == 2000
        assert config.max_records_display == 5
        assert config.max_sample_records == 3

    def test_bot_config_with_custom_values(self):
        """Тест создания конфигурации с кастомными значениями"""
        config = BotConfig(
            telegram_token="456:DEF",
            backend_url="http://example.com",
            log_level="DEBUG",
            max_retries=5,
            request_timeout=60,
            cache_ttl=600,
            max_query_length=3000,
            max_records_display=10,
            max_sample_records=5,
        )

        assert config.telegram_token == "456:DEF"
        assert config.backend_url == "http://example.com"
        assert config.log_level == "DEBUG"
        assert config.max_retries == 5
        assert config.request_timeout == 60
        assert config.cache_ttl == 600
        assert config.max_query_length == 3000
        assert config.max_records_display == 10
        assert config.max_sample_records == 5


class TestConfig:
    """Тесты для Config"""

    @patch.dict(
        os.environ,
        {
            "TELEGRAM_TOKEN": "123:ABC",
            "BACKEND_URL": "http://localhost:8000",
            "LOG_LEVEL": "DEBUG",
            "MAX_RETRIES": "5",
            "REQUEST_TIMEOUT": "60",
            "CACHE_TTL": "600",
            "MAX_QUERY_LENGTH": "3000",
            "MAX_RECORDS_DISPLAY": "10",
            "MAX_SAMPLE_RECORDS": "5",
        },
    )
    def test_load_from_env_full(self):
        """Тест загрузки полной конфигурации из переменных окружения"""
        config = Config.load_from_env()

        assert config.telegram_token == "123:ABC"
        assert config.backend_url == "http://localhost:8000"
        assert config.log_level == "DEBUG"
        assert config.max_retries == 5
        assert config.request_timeout == 60
        assert config.cache_ttl == 600
        assert config.max_query_length == 3000
        assert config.max_records_display == 10
        assert config.max_sample_records == 5

    @patch.dict(os.environ, {"TELEGRAM_TOKEN": "456:DEF"}, clear=True)
    def test_load_from_env_minimal(self):
        """Тест загрузки минимальной конфигурации с defaults"""
        config = Config.load_from_env()

        assert config.telegram_token == "456:DEF"
        assert config.backend_url == "http://localhost:8000"  # default
        assert config.log_level == "INFO"  # default
        assert config.max_retries == 3  # default
        assert config.request_timeout == 30  # default

    @patch.dict(os.environ, {}, clear=True)
    def test_load_from_env_missing_token(self):
        """Тест ошибки при отсутствующем токене"""
        with pytest.raises(ValueError, match="TELEGRAM_TOKEN not found"):
            Config.load_from_env()

    @patch.dict(
        os.environ,
        {
            "TELEGRAM_TOKEN": "",
        },
        clear=True,
    )
    def test_load_from_env_empty_token(self):
        """Тест ошибки при пустом токене"""
        with pytest.raises(ValueError, match="TELEGRAM_TOKEN not found"):
            Config.load_from_env()


class TestCallbackData:
    """Тесты для CallbackData"""

    def test_constants(self):
        """Тест констант для callback данных"""
        assert CallbackData.EXAMPLE_PREFIX == "ex:"
        assert CallbackData.TIME_RU == "time_ru"
        assert CallbackData.SALES_RU == "sales_ru"
        assert CallbackData.BESTSELLER_RU == "bestseller_ru"
        assert CallbackData.TIME_EN == "time_en"
        assert CallbackData.SALES_EN == "sales_en"
        assert CallbackData.BESTSELLER_EN == "bestseller_en"

    def test_examples_map(self):
        """Тест маппинга примеров"""
        assert CallbackData.EXAMPLES_MAP[CallbackData.TIME_RU] == "Покажи текущее время"
        assert CallbackData.EXAMPLES_MAP[CallbackData.SALES_RU] == "Каков объем продаж в январе?"
        assert CallbackData.EXAMPLES_MAP[CallbackData.BESTSELLER_RU] == "Какой товар продается лучше всего?"

        assert CallbackData.EXAMPLES_MAP[CallbackData.TIME_EN] == "Show current time"
        assert CallbackData.EXAMPLES_MAP[CallbackData.SALES_EN] == "What is the sales volume in January?"
        assert CallbackData.EXAMPLES_MAP[CallbackData.BESTSELLER_EN] == "What is the best-selling product?"

    def test_examples_map_completeness(self):
        """Тест полноты маппинга примеров"""
        # Все константы должны быть в маппинге
        expected_keys = {
            CallbackData.TIME_RU,
            CallbackData.SALES_RU,
            CallbackData.BESTSELLER_RU,
            CallbackData.TIME_EN,
            CallbackData.SALES_EN,
            CallbackData.BESTSELLER_EN,
        }

        actual_keys = set(CallbackData.EXAMPLES_MAP.keys())
        assert actual_keys == expected_keys


class TestEmoji:
    """Тесты для Emoji"""

    def test_emoji_constants(self):
        """Тест emoji констант"""
        assert Emoji.SEARCH == "🔍"
        assert Emoji.SUCCESS == "✅"
        assert Emoji.ERROR == "❌"
        assert Emoji.DATABASE == "📊"
        assert Emoji.TABLE == "📋"
        assert Emoji.VIEW == "👁️"
        assert Emoji.RECORD == "🔹"
        assert Emoji.FOLDER == "🗂️"
        assert Emoji.LIGHTBULB == "💡"
        assert Emoji.GEAR == "⚙️"
        assert Emoji.GLOBE == "🌐"
        assert Emoji.SPEECH == "💬"
        assert Emoji.TOOL == "🔧"
        assert Emoji.NULL_VALUE == "∅"
        assert Emoji.TIME == "⏱️"

    def test_emoji_are_strings(self):
        """Тест что все emoji являются строками"""
        import inspect

        for name, value in inspect.getmembers(Emoji):
            if not name.startswith("_"):
                assert isinstance(value, str), f"Emoji.{name} should be a string"
                assert len(value) > 0, f"Emoji.{name} should not be empty"
