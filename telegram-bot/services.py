"""
Сервисы для бизнес-логики Telegram бота
"""

import logging
from typing import List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from models import UserData, UserSettings, DatabaseTable, QueryResult, Language
from config import CallbackData, Emoji
from exceptions import ValidationError, AuthenticationError
from translations import get_translation
from api_client import APIClient

logger = logging.getLogger(__name__)


class UserService:
    """Сервис для работы с пользователями"""

    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    async def authenticate_and_get_settings(self, user_data: UserData) -> tuple[str, UserSettings]:
        """Аутентификация пользователя и получение настроек"""
        try:
            # Аутентификация
            token = await self.api_client.authenticate_user(user_data.user_id, user_data.__dict__)

            # Получение настроек
            settings_dict = await self.api_client.get_user_settings(user_data.user_id, token)
            settings = UserSettings.from_dict(settings_dict)

            return token, settings

        except Exception as e:
            logger.error(f"Authentication failed for user {user_data.user_id}: {e}")
            raise AuthenticationError(f"Failed to authenticate user: {e}", user_data.user_id)

    async def update_language(self, user_data: UserData, language: Language) -> UserSettings:
        """Обновление языка пользователя"""
        try:
            token, _ = await self.authenticate_and_get_settings(user_data)

            update_data = {"preferred_language": language.value}
            updated_settings = await self.api_client.update_user_settings(user_data.user_id, token, update_data)

            return UserSettings.from_dict(updated_settings)

        except Exception as e:
            logger.error(f"Failed to update language for user {user_data.user_id}: {e}")
            raise


class DatabaseService:
    """Сервис для работы с базой данных"""

    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    async def get_tables(self, user_data: UserData, token: str) -> List[DatabaseTable]:
        """Получение списка таблиц"""
        try:
            result = await self.api_client.get_tables(token)
            if not result.get("success"):
                raise Exception(result.get("message", "Failed to get tables"))

            tables_data = result.get("tables", [])
            return [DatabaseTable.from_dict(table) for table in tables_data]

        except Exception as e:
            logger.error(f"Failed to get tables for user {user_data.user_id}: {e}")
            raise

    async def get_table_sample(self, user_data: UserData, token: str, table_name: str, limit: int = 3) -> QueryResult:
        """Получение образца данных из таблицы"""
        try:
            result = await self.api_client.get_table_sample(table_name, token, limit)
            return QueryResult.from_dict(result)

        except Exception as e:
            logger.error(f"Failed to get sample for table {table_name}, user {user_data.user_id}: {e}")
            raise

    async def execute_query(self, user_data: UserData, token: str, query: str) -> QueryResult:
        """Выполнение запроса к базе данных"""
        # Валидация запроса
        if not query or not query.strip():
            raise ValidationError("Query cannot be empty", user_data.user_id)

        if len(query) > 2000:
            raise ValidationError("Query too long (max 2000 characters)", user_data.user_id)

        try:
            result = await self.api_client.execute_query(query, user_data.user_id, token)
            return QueryResult.from_dict(result)

        except Exception as e:
            logger.error(f"Failed to execute query for user {user_data.user_id}: {e}")
            raise


class KeyboardService:
    """Сервис для создания клавиатур"""

    @staticmethod
    def create_example_keyboard(language: Language) -> InlineKeyboardMarkup:
        """Создание клавиатуры с примерами запросов"""
        if language == Language.RUSSIAN:
            keyboard = [
                [
                    InlineKeyboardButton(
                        f"{Emoji.TIME} Покажи текущее время",
                        callback_data=f"{CallbackData.EXAMPLE_PREFIX}{CallbackData.TIME_RU}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"{Emoji.DATABASE} Каков объем продаж в январе?",
                        callback_data=f"{CallbackData.EXAMPLE_PREFIX}{CallbackData.SALES_RU}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"{Emoji.LIGHTBULB} Какой товар продается лучше всего?",
                        callback_data=f"{CallbackData.EXAMPLE_PREFIX}{CallbackData.BESTSELLER_RU}",
                    )
                ],
            ]
        else:
            keyboard = [
                [
                    InlineKeyboardButton(
                        f"{Emoji.TIME} Show current time",
                        callback_data=f"{CallbackData.EXAMPLE_PREFIX}{CallbackData.TIME_EN}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"{Emoji.DATABASE} What is the sales volume in January?",
                        callback_data=f"{CallbackData.EXAMPLE_PREFIX}{CallbackData.SALES_EN}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"{Emoji.LIGHTBULB} What is the best-selling product?",
                        callback_data=f"{CallbackData.EXAMPLE_PREFIX}{CallbackData.BESTSELLER_EN}",
                    )
                ],
            ]

        return InlineKeyboardMarkup(keyboard)


class ValidationService:
    """Сервис для валидации пользовательского ввода"""

    @staticmethod
    def validate_table_name(table_name: str) -> str:
        """Валидация имени таблицы"""
        if not table_name or not table_name.strip():
            raise ValidationError("Table name cannot be empty")

        # Очистка и нормализация
        cleaned_name = table_name.strip()

        # Базовая проверка на безопасность
        dangerous_chars = [";", "--", "/*", "*/", "DROP", "DELETE", "UPDATE", "INSERT"]
        for char in dangerous_chars:
            if char.upper() in cleaned_name.upper():
                raise ValidationError(f"Table name contains forbidden sequence: {char}")

        return cleaned_name

    @staticmethod
    def validate_settings_option(option: str, value: str) -> tuple[str, any]:
        """Валидация опций настроек"""
        option = option.lower().strip()
        value = value.lower().strip()

        if option == "lang":
            if value not in ("en", "ru"):
                raise ValidationError("Invalid language. Use 'en' or 'ru'")
            return "preferred_language", value

        elif option == "show_explanation":
            bool_value = value in ("on", "true", "1", "yes")
            return "show_explanation", bool_value

        elif option == "show_sql":
            bool_value = value in ("on", "true", "1", "yes")
            return "show_sql", bool_value

        else:
            raise ValidationError(f"Unknown setting: {option}")


class MessageService:
    """Сервис для создания сообщений"""

    @staticmethod
    def create_welcome_message(user_data: UserData, language: Language) -> str:
        """Создание приветственного сообщения"""
        name = user_data.first_name or ""
        return get_translation(language.value, "start").format(name=name)

    @staticmethod
    def create_settings_message(settings: UserSettings, language: Language) -> str:
        """Создание сообщения с текущими настройками"""
        return get_translation(language.value, "current_settings").format(
            lang=settings.preferred_language.value,
            explanation=settings.show_explanation,
            sql=settings.show_sql,
        )

    @staticmethod
    def get_example_query(callback_data: str) -> Optional[str]:
        """Получение текста запроса по callback данным"""
        if not callback_data.startswith(CallbackData.EXAMPLE_PREFIX):
            return None

        example_id = callback_data[len(CallbackData.EXAMPLE_PREFIX) :]
        return CallbackData.EXAMPLES_MAP.get(example_id)
