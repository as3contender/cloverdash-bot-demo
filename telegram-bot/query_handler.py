import logging
from telegram import Update
from telegram.ext import ContextTypes

from api_client import APIClient
from formatters import MessageFormatter
from translations import TRANSLATIONS, get_translation
from models import UserData, Language
from config import Emoji
from services import UserService, DatabaseService
from exceptions import AuthenticationError, ValidationError

logger = logging.getLogger(__name__)


class QueryHandler:
    """Обработчик запросов пользователей"""

    def __init__(
        self, api_client: APIClient, user_service: UserService = None, database_service: DatabaseService = None
    ):
        self.api_client = api_client
        self.user_service = user_service or UserService(api_client)
        self.database_service = database_service or DatabaseService(api_client)

    def _get_user_data(self, update: Update) -> UserData:
        """Получение типизированных данных пользователя из update"""
        user = update.effective_user
        return UserData(
            user_id=str(user.id),
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )

    async def handle_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик текстовых сообщений (вопросы пользователей)"""
        user_question = update.message.text
        user_data = self._get_user_data(update)

        logger.info(f"=== STARTING QUERY PROCESSING ===")
        logger.info(f"User ID: {user_data.user_id}")
        logger.info(f"Question: {user_question}")
        logger.info(f"Message ID: {update.message.message_id}")

        # Инициализация переменных
        user_language = Language.ENGLISH
        processing_msg = None

        try:
            # Получаем настройки пользователя для определения языка
            logger.info("Getting user authentication and settings...")
            token, user_settings = await self.user_service.authenticate_and_get_settings(user_data)
            user_language = user_settings.preferred_language

            # Добавляем детальную отладку настроек пользователя
            logger.error(f"=== USER SETTINGS DEBUG ===")
            logger.error(f"user_settings type: {type(user_settings)}")
            logger.error(f"user_settings object: {user_settings}")
            logger.error(f"preferred_language type: {type(user_settings.preferred_language)}")
            logger.error(f"preferred_language value: {user_settings.preferred_language}")
            if hasattr(user_settings.preferred_language, "value"):
                logger.error(f"preferred_language.value: {user_settings.preferred_language.value}")
            logger.error(f"show_explanation: {user_settings.show_explanation}")
            logger.error(f"show_sql: {user_settings.show_sql}")
            logger.error(f"=== END DEBUG ===")

            # Отправляем уведомление о том, что запрос обрабатывается
            logger.info("Sending processing message...")
            processing_text = get_translation(user_language.value, "processing_request")
            processing_msg = await update.message.reply_text(f"{Emoji.SEARCH} {processing_text}")
            logger.info(f"Processing message sent with ID: {processing_msg.message_id}")

        except AuthenticationError as e:
            logger.error(f"Authentication error in handle_query: {e}")
            await update.message.reply_text(f"{Emoji.CROSS} Authentication failed. Please try /start")
            return

        except Exception as e:
            logger.error(f"Error in handle_query setup: {e}")
            # Fallback к английскому если не можем получить настройки пользователя
            processing_msg = await update.message.reply_text(f"{Emoji.SEARCH} Processing your request...")
            logger.info(f"Fallback processing message sent with ID: {processing_msg.message_id}")

        try:
            logger.info("Starting backend API request...")

            # Валидация запроса
            if not user_question or not user_question.strip():
                error_msg = get_translation(user_language.value, "empty_query_error")
                await update.message.reply_text(f"{Emoji.CROSS} {error_msg}")
                return

            # Выполняем запрос через DatabaseService
            query_result = await self.database_service.execute_query(user_data, token, user_question.strip())
            logger.info(f"Backend response success: {query_result.success}")

            if query_result.success:
                # Форматируем ответ для успешного запроса - преобразуем настройки для правильной работы с языком
                # Исправленное извлечение значения языка из enum'а
                lang_value = user_settings.preferred_language.value

                settings_dict = {
                    "preferred_language": lang_value,
                    "show_explanation": user_settings.show_explanation,
                    "show_sql": user_settings.show_sql,
                }
                logger.error(f"=== FORMATTING DEBUG ===")
                logger.error(f"lang_value extracted: '{lang_value}' (type: {type(lang_value)})")
                logger.error(f"settings_dict: {settings_dict}")
                logger.error(f"=== END FORMATTING DEBUG ===")

                reply_message = MessageFormatter.format_query_result(query_result.__dict__, settings_dict)
            else:
                # Обрабатываем ошибку API - экранируем сообщение об ошибке
                safe_error = MessageFormatter.escape_markdown(query_result.message or "Unknown error")
                error_text = get_translation(user_language.value, "error_occurred")
                reply_message = f"{Emoji.CROSS} *{error_text}:*\n{safe_error}"

            # Отправляем результат как новое сообщение
            logger.info("Sending result message...")
            try:
                result_msg = await update.message.reply_text(reply_message, parse_mode="Markdown")
                logger.info(f"Result message sent with ID: {result_msg.message_id}")
            except Exception as markdown_error:
                logger.error(f"Markdown parsing error: {markdown_error}")
                # Очищаем сообщение от Markdown форматирования и отправляем как обычный текст
                clean_message = MessageFormatter.clean_markdown(reply_message)
                result_msg = await update.message.reply_text(clean_message)
                logger.info(f"Result message sent without markdown, ID: {result_msg.message_id}")

        except ValidationError as e:
            logger.error(f"Validation error in query processing: {e}")
            error_msg = get_translation(user_language.value, "validation_error")
            await update.message.reply_text(f"{Emoji.CROSS} {error_msg}: {str(e)}")

        except AuthenticationError as e:
            logger.error(f"Authentication error during query processing: {e}")
            await update.message.reply_text(f"{Emoji.CROSS} Authentication failed. Please try /start")

        except Exception as e:
            logger.error(f"Exception in query processing: {str(e)}")
            logger.info("Sending exception message...")
            try:
                error_text = get_translation(user_language.value, "error_occurred")
                exception_msg = await update.message.reply_text(f"{Emoji.CROSS} {error_text}. Please try again later.")
                logger.info(f"Exception message sent with ID: {exception_msg.message_id}")
            except Exception as send_error:
                logger.error(f"Error sending exception message: {send_error}")

        logger.info("=== QUERY PROCESSING COMPLETED ===")
 