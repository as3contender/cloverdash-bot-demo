import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Обработчик ошибок Telegram бота"""

    def __init__(self, api_client=None):
        self.api_client = api_client

    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик ошибок"""
        logger.error(f"=== ERROR HANDLER TRIGGERED ===")
        logger.error(f"Error type: {type(context.error)}")
        logger.error(f"Error message: {context.error}")
        logger.error(f"Update that caused error: {update}")

        # Логируем stack trace если доступен
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Если ошибка связана с истекшим токеном, инвалидируем его
        if self.api_client and update and update.effective_user:
            user_id = str(update.effective_user.id)
            if "401" in str(context.error) or "authentication" in str(context.error).lower():
                logger.info(f"Invalidating token for user {user_id} due to auth error")
                self.api_client.invalidate_token(user_id)

        if update and update.message:
            try:
                logger.info("Sending error handler message...")
                error_handler_msg = await update.message.reply_text("❌ An error occurred. Please try again.")
                logger.info(f"Error handler message sent with ID: {error_handler_msg.message_id}")
            except Exception as e:
                logger.error(f"Error sending error message in error_handler: {e}")

        logger.error(f"=== ERROR HANDLER COMPLETED ===")
