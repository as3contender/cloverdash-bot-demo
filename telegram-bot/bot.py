import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Импортируем новые модули
from api_client import APIClient
from handlers import CommandHandlers
from query_handler import QueryHandler
from error_handler import ErrorHandler

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


class CloverdashBot:
    def __init__(self):
        # Инициализируем API клиент
        self.api_client = APIClient(BACKEND_URL)

        # Инициализируем хендлеры
        self.command_handlers = CommandHandlers(self.api_client)
        self.query_handler = QueryHandler(self.api_client)
        self.error_handler = ErrorHandler(self.api_client)

    def setup_handlers(self, application: Application) -> None:
        """Настройка хендлеров для приложения"""
        # Команды
        application.add_handler(CommandHandler("start", self.command_handlers.start_command))
        application.add_handler(CommandHandler("help", self.command_handlers.help_command))
        application.add_handler(CommandHandler("tables", self.command_handlers.tables_command))
        application.add_handler(CommandHandler("sample", self.command_handlers.sample_command))
        application.add_handler(CommandHandler("settings", self.command_handlers.settings_command))
        
        # Быстрые команды для смены языка
        application.add_handler(CommandHandler("en", self.command_handlers.quick_lang_en_command))
        application.add_handler(CommandHandler("ru", self.command_handlers.quick_lang_ru_command))

        # Обработка текстовых сообщений (запросы)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.query_handler.handle_query))

        # Обработка ошибок
        application.add_error_handler(self.error_handler.handle_error)


def main():
    """Запуск бота"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN not found in environment variables")
        print("❌ Error: TELEGRAM_TOKEN not found in environment variables")
        print("📝 Add it to the .env file:")
        print("TELEGRAM_TOKEN=your_bot_token_here")
        return

    print(f"🚀 Starting CloverdashBot...")
    print(f"🔗 Backend URL: {BACKEND_URL}")

    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Создаем экземпляр бота
    bot = CloverdashBot()

    # Настраиваем хендлеры
    bot.setup_handlers(application)

    # Запускаем бота
    logger.info("Starting CloverdashBot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
