import logging
from telegram import Update
from telegram.ext import ContextTypes
from typing import Dict, Any

from api_client import APIClient
from formatters import MessageFormatter
from translations import TRANSLATIONS

logger = logging.getLogger(__name__)


class QueryHandler:
    """Обработчик запросов пользователей"""

    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    def _get_user_data(self, update: Update) -> Dict[str, Any]:
        """Получение данных пользователя из update"""
        user = update.effective_user
        return {
            "user_id": str(user.id),
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

    async def handle_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик текстовых сообщений (вопросы пользователей)"""
        user_question = update.message.text
        user_data = self._get_user_data(update)
        user_id = user_data["user_id"]

        logger.info(f"=== STARTING QUERY PROCESSING ===")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Question: {user_question}")
        logger.info(f"Message ID: {update.message.message_id}")

        try:
            # Get user settings to determine language preference
            logger.info("Getting user authentication token...")
            token = await self.api_client.authenticate_user(user_id, user_data)
            settings = await self.api_client.get_user_settings(user_id, token)
            user_lang = settings.get("language", "en")

            # Отправляем уведомление о том, что запрос обрабатывается
            logger.info("Sending processing message...")
            processing_text = TRANSLATIONS[user_lang]["processing_request"]
            processing_msg = await update.message.reply_text(f"🔍 {processing_text}")
            logger.info(f"Processing message sent with ID: {processing_msg.message_id}")

        except Exception as e:
            logger.error(f"Error in handle_query setup: {e}")
            # Fallback to English if we can't get user settings
            processing_msg = await update.message.reply_text("🔍 Processing your request...")
            logger.info(f"Fallback processing message sent with ID: {processing_msg.message_id}")
            user_lang = "en"
            settings = {"language": "en"}

        try:
            logger.info("Starting backend API request...")
            # Отправляем запрос к backend API
            result = await self.api_client.execute_query(user_question, user_id, token)
            logger.info(f"Backend response: {result}")

            if result.get("success"):
                # Форматируем ответ для успешного запроса
                reply_message = MessageFormatter.format_query_result(result, settings)

            else:
                # Обрабатываем ошибку API - экранируем сообщение об ошибке
                error_message = result.get("message", "Unknown error")
                safe_error = MessageFormatter.escape_markdown(error_message)
                error_text = TRANSLATIONS[user_lang]["error_occurred"]
                reply_message = f"❌ *{error_text}:*\n{safe_error}"

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

        except Exception as e:
            logger.error(f"Exception in query processing: {str(e)}")
            logger.info("Sending exception message...")
            try:
                error_text = TRANSLATIONS[user_lang]["error_occurred"]
                exception_msg = await update.message.reply_text(f"❌ {error_text}. Please try again later.")
                logger.info(f"Exception message sent with ID: {exception_msg.message_id}")
            except Exception as send_error:
                logger.error(f"Error sending exception message: {send_error}")

        logger.info("=== QUERY PROCESSING COMPLETED ===")
