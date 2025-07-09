import uuid
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from services.app_database import app_database_service
from services.security import security_service
from models.auth import UserCreate, User, TelegramAuth, UserSettings

logger = logging.getLogger(__name__)


class UserService:
    """Сервис для работы с пользователями"""

    @staticmethod
    def _convert_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Конвертирует UUID объекты в строки для совместимости с Pydantic моделями"""
        if user_data and "id" in user_data:
            # Конвертируем UUID в строку если необходимо
            if hasattr(user_data["id"], "hex"):  # Проверяем что это UUID объект
                user_data = user_data.copy()  # Создаем копию чтобы не изменять оригинал
                user_data["id"] = str(user_data["id"])
        return user_data

    @staticmethod
    async def create_user_table():
        """Создание таблицы пользователей и других таблиц приложения"""
        try:
            await app_database_service.create_app_tables()
            logger.info("User tables created successfully")
        except Exception as e:
            logger.error(f"Error creating user tables: {e}")
            raise

    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[User]:
        """Получение пользователя по ID"""
        query = "SELECT * FROM users WHERE id = $1 AND is_active = true"

        try:
            result = await app_database_service.execute_query(query, [user_id])
            if result.data:
                user_data = UserService._convert_user_data(result.data[0])
                return User(**user_data)
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[User]:
        """Получение пользователя по email"""
        query = "SELECT * FROM users WHERE email = $1 AND is_active = true"

        try:
            result = await app_database_service.execute_query(query, [email])
            if result.data:
                user_data = UserService._convert_user_data(result.data[0])
                return User(**user_data)
            return None
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None

    @staticmethod
    async def get_user_by_username(username: str) -> Optional[User]:
        """Получение пользователя по username"""
        query = "SELECT * FROM users WHERE username = $1 AND is_active = true"

        try:
            result = await app_database_service.execute_query(query, [username])
            if result.data:
                user_data = UserService._convert_user_data(result.data[0])
                return User(**user_data)
            return None
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None

    @staticmethod
    async def get_user_by_telegram_id(telegram_id: str) -> Optional[User]:
        """Получение пользователя по Telegram ID"""
        query = "SELECT * FROM users WHERE telegram_id = $1 AND is_active = true"

        try:
            result = await app_database_service.execute_query(query, [telegram_id])
            if result.data:
                user_data = UserService._convert_user_data(result.data[0])
                return User(**user_data)
            return None
        except Exception as e:
            logger.error(f"Error getting user by Telegram ID {telegram_id}: {e}")
            return None

    @staticmethod
    async def create_user(user_create: UserCreate) -> User:
        """Создание нового пользователя"""
        user_id = str(uuid.uuid4())
        hashed_password = None

        if user_create.password:
            hashed_password = security_service.get_password_hash(user_create.password)

        query = """
        INSERT INTO users (id, username, email, full_name, hashed_password, telegram_id, telegram_username)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """

        values = [
            user_id,
            user_create.username,
            user_create.email,
            user_create.full_name,
            hashed_password,
            user_create.telegram_id,
            user_create.telegram_username,
        ]

        try:
            result = await app_database_service.execute_query(query, values)
            if result.data:
                user_data = UserService._convert_user_data(result.data[0])
                logger.info(f"User created successfully: {user_id}")
                await UserService.create_default_settings(user_id)
                return User(**user_data)
            else:
                raise Exception("Failed to create user")
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    @staticmethod
    async def create_telegram_user(telegram_auth: TelegramAuth) -> User:
        """Создание пользователя через Telegram"""
        user_create = UserCreate(
            telegram_id=telegram_auth.telegram_id,
            telegram_username=telegram_auth.telegram_username,
            full_name=f"{telegram_auth.first_name or ''} {telegram_auth.last_name or ''}".strip() or None,
        )

        return await UserService.create_user(user_create)

    @staticmethod
    async def authenticate_user(username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя по username/email и паролю"""
        # Пытаемся найти пользователя по email или username
        user = await UserService.get_user_by_email(username)
        if not user:
            user = await UserService.get_user_by_username(username)

        if not user:
            return None

        # Получаем хэшированный пароль из базы
        query = "SELECT hashed_password FROM users WHERE id = $1"
        try:
            result = await app_database_service.execute_query(query, [user.id])
            if not result.data or not result.data[0].get("hashed_password"):
                return None

            hashed_password = result.data[0]["hashed_password"]
            if not security_service.verify_password(password, hashed_password):
                return None

            return user
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None

    @staticmethod
    async def authenticate_telegram_user(telegram_id: str) -> Optional[User]:
        """Аутентификация пользователя через Telegram ID"""
        return await UserService.get_user_by_telegram_id(telegram_id)

    @staticmethod
    async def get_user_query_history(user_id: str, limit: int = 50) -> list:
        """Получение истории запросов пользователя"""
        try:
            return await app_database_service.get_user_query_history(user_id, limit)
        except Exception as e:
            logger.error(f"Error getting user query history: {e}")
            return []

    @staticmethod
    async def save_user_query_history(
        user_id: str,
        query: str,
        sql_query: str,
        result_count: int,
        execution_time: float,
        success: bool,
        error_message: Optional[str] = None,
    ):
        """Сохранение истории запросов пользователя"""
        try:
            await app_database_service.save_query_history(
                user_id, query, sql_query, result_count, execution_time, success, error_message
            )
        except Exception as e:
            logger.error(f"Error saving user query history: {e}")

    @staticmethod
    async def create_default_settings(user_id: str) -> None:
        """Создает настройки по умолчанию для пользователя"""
        try:
            query = """
                INSERT INTO user_settings (user_id, preferred_language, timezone, query_limit, settings_json) 
                VALUES ($1, $2, $3, $4, $5) 
                ON CONFLICT (user_id) DO NOTHING
            """
            import json

            default_settings = {"show_explanation": True, "show_sql": False}
            await app_database_service.execute_query(
                query,
                [
                    user_id,
                    "en",  # preferred_language
                    "UTC",  # timezone
                    100,  # query_limit
                    json.dumps(default_settings),  # Конвертируем в JSON строку
                ],
            )
            logger.info(f"Default settings created for user {user_id}")
        except Exception as e:
            logger.error(f"Error creating default settings for {user_id}: {e}")

    @staticmethod
    async def get_user_settings(user_id: str) -> Optional[UserSettings]:
        """Получение настроек пользователя"""
        try:
            query = """
            SELECT user_id, preferred_language, timezone,
                   query_limit, settings_json
            FROM user_settings WHERE user_id = $1
            """
            result = await app_database_service.execute_query(query, [user_id])
            if result.data:
                import json

                row = result.data[0]
                settings_json = row.get("settings_json") or "{}"
                # Парсим JSON строку в словарь
                settings = json.loads(settings_json) if isinstance(settings_json, str) else settings_json
                row["show_explanation"] = settings.get("show_explanation", True)
                row["show_sql"] = settings.get("show_sql", False)
                # Убираем settings_json из словаря, так как его нет в модели UserSettings
                row.pop("settings_json", None)
                return UserSettings(**row)
            else:
                # Если настроек нет, создаем их по умолчанию
                logger.info(f"Creating default settings for user {user_id}")
                await UserService.create_default_settings(user_id)
                # Повторно получаем созданные настройки
                result = await app_database_service.execute_query(query, [user_id])
                if result.data:
                    import json

                    row = result.data[0]
                    settings_json = row.get("settings_json") or "{}"
                    # Парсим JSON строку в словарь
                    settings = json.loads(settings_json) if isinstance(settings_json, str) else settings_json
                    row["show_explanation"] = settings.get("show_explanation", True)
                    row["show_sql"] = settings.get("show_sql", False)
                    # Убираем settings_json из словаря, так как его нет в модели UserSettings
                    row.pop("settings_json", None)
                    return UserSettings(**row)
            return None
        except Exception as e:
            logger.error(f"Error getting settings for user {user_id}: {e}")
            return None

    @staticmethod
    async def update_user_settings(
        user_id: str,
        preferred_language: Optional[str] = None,
        show_explanation: Optional[bool] = None,
        show_sql: Optional[bool] = None,
    ) -> Optional[UserSettings]:
        """Обновление настроек пользователя"""
        try:
            logger.info(
                f"Updating settings for user {user_id}: lang={preferred_language}, explanation={show_explanation}, sql={show_sql}"
            )
            # Получаем текущие настройки JSON
            import json

            get_query = "SELECT settings_json FROM user_settings WHERE user_id = $1"
            current = await app_database_service.execute_query(get_query, [user_id])
            if not current.data:
                return None
            settings_json_str = current.data[0].get("settings_json") or "{}"
            # Парсим JSON строку в словарь
            settings_json = json.loads(settings_json_str) if isinstance(settings_json_str, str) else settings_json_str

            if show_explanation is not None:
                settings_json["show_explanation"] = show_explanation
            if show_sql is not None:
                settings_json["show_sql"] = show_sql

            fields = []
            params = []
            if preferred_language is not None:
                params.append(preferred_language)
                fields.append(f"preferred_language = ${len(params)}")

            # Всегда обновляем settings_json если есть изменения
            if show_explanation is not None or show_sql is not None:
                import json

                params.append(json.dumps(settings_json))  # Конвертируем в JSON строку
                fields.append(f"settings_json = ${len(params)}")

            # Если нет полей для обновления, возвращаем текущие настройки
            if not fields:
                return await UserService.get_user_settings(user_id)

            params.append(user_id)
            query = (
                f"UPDATE user_settings SET {', '.join(fields)}, "
                "updated_at = CURRENT_TIMESTAMP WHERE user_id = $"
                + str(len(params))
                + " RETURNING user_id, preferred_language, timezone, query_limit, settings_json"
            )

            result = await app_database_service.execute_query(query, params)
            if result.data:
                import json

                row = result.data[0]
                settings_json = row.get("settings_json") or "{}"
                # Парсим JSON строку в словарь
                settings = json.loads(settings_json) if isinstance(settings_json, str) else settings_json
                row["show_explanation"] = settings.get("show_explanation", True)
                row["show_sql"] = settings.get("show_sql", False)
                # Убираем settings_json из словаря, так как его нет в модели UserSettings
                row.pop("settings_json", None)
                updated_settings = UserSettings(**row)
                logger.info(f"Settings updated successfully for user {user_id}: {updated_settings}")
                return updated_settings
            logger.warning(f"No data returned when updating settings for user {user_id}")
            return None
        except Exception as e:
            logger.error(f"Error updating settings for user {user_id}: {e}")
            return None


# Создаем экземпляр сервиса
user_service = UserService()
