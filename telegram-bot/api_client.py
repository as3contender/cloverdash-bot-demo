import logging
import aiohttp
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class APIClient:
    """Клиент для работы с Backend API"""

    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.user_tokens = {}  # Кэш токенов пользователей
        self.user_settings = {}  # Кэш настроек пользователей

    async def authenticate_user(self, user_id: str, user_data: dict) -> str:
        """Аутентификация пользователя через Telegram"""
        if user_id in self.user_tokens:
            return self.user_tokens[user_id]

        try:
            auth_payload = {
                "telegram_id": user_id,
                "telegram_username": user_data.get("username"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.backend_url}/auth/telegram", json=auth_payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        token = result["access_token"]
                        self.user_tokens[user_id] = token
                        logger.info(f"User {user_id} authenticated successfully")
                        return token
                    else:
                        error_text = await response.text()
                        logger.error(f"Authentication failed for user {user_id}: {error_text}")
                        raise Exception(f"Authentication failed: {response.status}")

        except Exception as e:
            logger.error(f"Error authenticating user {user_id}: {e}")
            raise

    def invalidate_token(self, user_id: str) -> None:
        """Инвалидация токена пользователя"""
        self.user_tokens.pop(user_id, None)
        self.user_settings.pop(user_id, None)  # Также очищаем кэш настроек
        logger.info(f"Token and settings cache invalidated for user {user_id}")

    def clear_settings_cache(self, user_id: str) -> None:
        """Очистка кэша настроек пользователя"""
        self.user_settings.pop(user_id, None)
        logger.info(f"Settings cache cleared for user {user_id}")

    async def get_user_settings(self, user_id: str, token: str) -> dict:
        """Получение настроек пользователя"""
        if user_id in self.user_settings:
            return self.user_settings[user_id]

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.get(f"{self.backend_url}/settings", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.user_settings[user_id] = data
                    return data
        return {}

    async def update_user_settings(self, user_id: str, token: str, data: dict) -> dict:
        """Обновление настроек пользователя"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.patch(f"{self.backend_url}/settings", json=data, headers=headers) as resp:
                if resp.status == 200:
                    updated = await resp.json()
                    # Обновляем кэш настроек
                    self.user_settings[user_id] = updated
                    logger.info(f"Settings updated for user {user_id}: {data}")
                    return updated
                else:
                    error_text = await resp.text()
                    logger.error(f"Settings update failed: {resp.status} - {error_text}")
                    raise Exception(f"Failed to update settings: {resp.status}")
        return {}

    async def get_tables(self, token: str) -> Dict[str, Any]:
        """Получение списка таблиц"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.get(f"{self.backend_url}/database/tables", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Tables API error: {response.status} - {error_text}")
                    raise Exception(f"Failed to get tables: {response.status}")

    async def get_table_sample(self, table_name: str, token: str, limit: int = 3) -> Dict[str, Any]:
        """Получение образца данных из таблицы"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}
            url = f"{self.backend_url}/database/table/{table_name}/sample?limit={limit}"
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Sample API error: {response.status} - {error_text}")
                    raise Exception(f"Failed to get sample data: {response.status}")

    async def execute_query(self, query: str, user_id: str, token: str) -> Dict[str, Any]:
        """Выполнение запроса к базе данных"""
        async with aiohttp.ClientSession() as session:
            payload = {"query": query, "user_id": user_id}
            headers = {"Authorization": f"Bearer {token}"}

            async with session.post(f"{self.backend_url}/database/query", json=payload, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Query API error: {response.status} - {error_text}")
                    raise Exception(f"Failed to execute query: {response.status}")
