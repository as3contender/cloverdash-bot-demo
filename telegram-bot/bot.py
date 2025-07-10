import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Новые импорты
from config import Config, BotConfig
from models import UserData
from services import UserService, DatabaseService, KeyboardService, ValidationService, MessageService
from exceptions import ConfigurationError, BotException

# Остальные импорты
from api_client import APIClient
from handlers import CommandHandlers
from query_handler import QueryHandler
from error_handler import ErrorHandler

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


class CloverdashBot:
    def __init__(self, config: BotConfig):
        self.config = config

        # Инициализируем API клиент
        self.api_client = APIClient(config.backend_url)

        # Инициализируем сервисы
        self.user_service = UserService(self.api_client)
        self.database_service = DatabaseService(self.api_client)

        # Инициализируем хендлеры с сервисами
        self.query_handler = QueryHandler(self.api_client)
        self.command_handlers = CommandHandlers(
            self.api_client, self.query_handler, self.user_service, self.database_service
        )
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

        # Обработка callback'ов от inline кнопок
        application.add_handler(CallbackQueryHandler(self.command_handlers.handle_example_callback))

        # Обработка текстовых сообщений (запросы)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.query_handler.handle_query))

        # Обработка ошибок
        application.add_error_handler(self.error_handler.handle_error)


def main():
    """Запуск бота"""
    try:
        # Загружаем конфигурацию
        config = Config.load_from_env()

        print(f"🚀 Starting CloverdashBot...")
        print(f"🔗 Backend URL: {config.backend_url}")
        print(f"📊 Config: retries={config.max_retries}, timeout={config.request_timeout}s")

        # Создаем приложение
        application = Application.builder().token(config.telegram_token).build()

        # Создаем экземпляр бота
        bot = CloverdashBot(config)

        # Настраиваем хендлеры
        bot.setup_handlers(application)

        # Запускаем бота
        logger.info("Starting CloverdashBot with new architecture...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        print(f"❌ Configuration error: {e}")
        print("📝 Check your .env file and environment variables")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"❌ Failed to start bot: {e}")


if __name__ == "__main__":
    main()
