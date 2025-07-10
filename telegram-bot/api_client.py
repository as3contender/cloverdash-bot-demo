import logging
import aiohttp
import asyncio
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from models import UserData
from exceptions import APIError, AuthenticationError, NetworkError
from config import BotConfig

logger = logging.getLogger(__name__)


class APIClient:
    """Клиент для работы с Backend API с retry логикой и улучшенной обработкой ошибок"""

    def __init__(self, backend_url: str, config: BotConfig = None):
        self.backend_url = backend_url
        self.config = config
        self.user_tokens: Dict[str, str] = {}  # Кэш токенов пользователей
        self.user_settings: Dict[str, Dict[str, Any]] = {}  # Кэш настроек пользователей

        # Настройки retry
        self.max_retries = config.max_retries if config else 3
        self.request_timeout = config.request_timeout if config else 30

    def _create_session(self) -> aiohttp.ClientSession:
        """Создание сессии с настройками таймаута"""
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        return aiohttp.ClientSession(timeout=timeout)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True,
    )
    async def authenticate_user(self, user_id: str, user_data: Dict[str, Any]) -> str:
        """Аутентификация пользователя через Telegram с retry логикой"""
        if user_id in self.user_tokens:
            return self.user_tokens[user_id]

        try:
            auth_payload = {
                "telegram_id": user_id,
                "telegram_username": user_data.get("username"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
            }

            async with self._create_session() as session:
                url = f"{self.backend_url}/auth/telegram"
                logger.info(f"Authenticating user {user_id} at {url}")

                async with session.post(url, json=auth_payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        token = result.get("access_token")
                        if not token:
                            raise AuthenticationError("No access token in response", user_id)

                        self.user_tokens[user_id] = token
                        logger.info(f"User {user_id} authenticated successfully")
                        return token
                    elif response.status == 401:
                        error_text = await response.text()
                        logger.error(f"Authentication failed for user {user_id}: {error_text}")
                        raise AuthenticationError(f"Authentication failed: {error_text}", user_id)
                    else:
                        error_text = await response.text()
                        logger.error(f"API error during authentication: {response.status} - {error_text}")
                        raise APIError(f"API error: {response.status} - {error_text}", response.status)

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Network error authenticating user {user_id}: {e}")
            raise NetworkError(f"Network error during authentication: {e}")
        except Exception as e:
            logger.error(f"Unexpected error authenticating user {user_id}: {e}")
            raise APIError(f"Unexpected error: {e}")

    def invalidate_token(self, user_id: str) -> None:
        """Инвалидация токена пользователя"""
        self.user_tokens.pop(user_id, None)
        self.user_settings.pop(user_id, None)  # Также очищаем кэш настроек
        logger.info(f"Token and settings cache invalidated for user {user_id}")

    def clear_settings_cache(self, user_id: str) -> None:
        """Очистка кэша настроек пользователя"""
        self.user_settings.pop(user_id, None)
        logger.info(f"Settings cache cleared for user {user_id}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True,
    )
    async def get_user_settings(self, user_id: str, token: str) -> Dict[str, Any]:
        """Получение настроек пользователя с retry логикой"""
        if user_id in self.user_settings:
            return self.user_settings[user_id]

        try:
            async with self._create_session() as session:
                headers = {"Authorization": f"Bearer {token}"}
                url = f"{self.backend_url}/settings"

                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.user_settings[user_id] = data
                        logger.info(f"Settings retrieved for user {user_id}")
                        return data
                    elif response.status == 401:
                        self.invalidate_token(user_id)
                        error_text = await response.text()
                        raise AuthenticationError(f"Token expired: {error_text}", user_id)
                    else:
                        error_text = await response.text()
                        logger.error(f"Settings API error: {response.status} - {error_text}")
                        raise APIError(f"Failed to get settings: {error_text}", response.status)

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Network error getting settings for user {user_id}: {e}")
            raise NetworkError(f"Network error: {e}")
        except (AuthenticationError, APIError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting settings for user {user_id}: {e}")
            raise APIError(f"Unexpected error: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True,
    )
    async def update_user_settings(self, user_id: str, token: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновление настроек пользователя с retry логикой"""
        try:
            async with self._create_session() as session:
                headers = {"Authorization": f"Bearer {token}"}
                url = f"{self.backend_url}/settings"

                async with session.patch(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        updated = await response.json()
                        # Обновляем кэш настроек
                        self.user_settings[user_id] = updated
                        logger.info(f"Settings updated for user {user_id}: {data}")
                        return updated
                    elif response.status == 401:
                        self.invalidate_token(user_id)
                        error_text = await response.text()
                        raise AuthenticationError(f"Token expired: {error_text}", user_id)
                    else:
                        error_text = await response.text()
                        logger.error(f"Settings update failed: {response.status} - {error_text}")
                        raise APIError(f"Failed to update settings: {error_text}", response.status)

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Network error updating settings for user {user_id}: {e}")
            raise NetworkError(f"Network error: {e}")
        except (AuthenticationError, APIError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating settings for user {user_id}: {e}")
            raise APIError(f"Unexpected error: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True,
    )
    async def get_tables(self, token: str) -> Dict[str, Any]:
        """Получение списка таблиц с retry логикой"""
        try:
            async with self._create_session() as session:
                headers = {"Authorization": f"Bearer {token}"}
                url = f"{self.backend_url}/database/tables"

                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("Tables list retrieved successfully")
                        return result
                    elif response.status == 401:
                        error_text = await response.text()
                        raise AuthenticationError(f"Token expired: {error_text}")
                    else:
                        error_text = await response.text()
                        logger.error(f"Tables API error: {response.status} - {error_text}")
                        raise APIError(f"Failed to get tables: {error_text}", response.status)

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Network error getting tables: {e}")
            raise NetworkError(f"Network error: {e}")
        except (AuthenticationError, APIError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting tables: {e}")
            raise APIError(f"Unexpected error: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True,
    )
    async def get_table_sample(self, table_name: str, token: str, limit: int = 3) -> Dict[str, Any]:
        """Получение образца данных из таблицы с retry логикой"""
        try:
            async with self._create_session() as session:
                headers = {"Authorization": f"Bearer {token}"}
                url = f"{self.backend_url}/database/table/{table_name}/sample?limit={limit}"

                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Sample data retrieved for table {table_name}")
                        return result
                    elif response.status == 401:
                        error_text = await response.text()
                        raise AuthenticationError(f"Token expired: {error_text}")
                    else:
                        error_text = await response.text()
                        logger.error(f"Sample API error: {response.status} - {error_text}")
                        raise APIError(f"Failed to get sample data: {error_text}", response.status)

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Network error getting sample for {table_name}: {e}")
            raise NetworkError(f"Network error: {e}")
        except (AuthenticationError, APIError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting sample for {table_name}: {e}")
            raise APIError(f"Unexpected error: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True,
    )
    async def execute_query(self, query: str, user_id: str, token: str) -> Dict[str, Any]:
        """Выполнение запроса к базе данных с retry логикой"""
        try:
            async with self._create_session() as session:
                payload = {"query": query, "user_id": user_id}
                headers = {"Authorization": f"Bearer {token}"}
                url = f"{self.backend_url}/database/query"

                logger.info(f"Executing query for user {user_id}: {query[:100]}...")

                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Query executed successfully for user {user_id}")
                        return result
                    elif response.status == 401:
                        self.invalidate_token(user_id)
                        error_text = await response.text()
                        raise AuthenticationError(f"Token expired: {error_text}", user_id)
                    else:
                        error_text = await response.text()
                        logger.error(f"Query API error: {response.status} - {error_text}")
                        raise APIError(f"Failed to execute query: {error_text}", response.status)

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Network error executing query for user {user_id}: {e}")
            raise NetworkError(f"Network error: {e}")
        except (AuthenticationError, APIError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing query for user {user_id}: {e}")
            raise APIError(f"Unexpected error: {e}")

    async def health_check(self) -> bool:
        """Проверка состояния backend API"""
        try:
            async with self._create_session() as session:
                url = f"{self.backend_url}/health"
                async with session.get(url) as response:
                    if response.status == 200:
                        logger.info("Backend health check passed")
                        return True
                    else:
                        logger.warning(f"Backend health check failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Backend health check error: {e}")
            return False
