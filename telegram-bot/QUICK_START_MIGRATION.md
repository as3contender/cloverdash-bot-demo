# 🚀 Быстрый старт миграции

Это краткое руководство поможет вам начать миграцию к улучшенной архитектуре.

## ✅ Этап 1: Подготовка (СЕЙЧАС)

### 1.1. Проверка новых модулей
```bash
cd telegram-bot

# Проверяем что новые модули импортируются без ошибок
python3 -c "
try:
    import config
    import models  
    import exceptions
    import services
    print('✅ Все новые модули успешно импортированы!')
    
    # Проверяем базовую функциональность
    from config import Config, CallbackData, Emoji
    from models import Language, UserData, UserSettings
    from exceptions import BotException
    
    print('✅ Основные классы доступны!')
    print('✅ Готовы к миграции!')
    
except ImportError as e:
    print(f'❌ Ошибка импорта: {e}')
except Exception as e:
    print(f'❌ Ошибка: {e}')
"
```

### 1.2. Установка новых зависимостей
```bash
# Установка новых пакетов
make install-dev

# Или вручную
pip install -r requirements.txt
```

### 1.3. Запуск тестов
```bash
# Базовые тесты
make test-fast

# Полные тесты с покрытием  
make test-cov
```

### 1.4. Проверка что текущий бот работает
```bash
# Запуск с текущим кодом
make local-up
make local-logs

# Тест команды /start в Telegram
# Если все работает - переходим к следующему этапу
```

## 🔧 Этап 2: Миграция bot.py (СЛЕДУЮЩИЙ)

### 2.1. Создание резервной копии
```bash
cp bot.py bot.py.backup
cp -r . ../telegram-bot-backup  # Полная резервная копия
```

### 2.2. Создание ветки для миграции
```bash
git checkout -b feature/architecture-improvements
git add config.py models.py exceptions.py services.py requirements.txt
git add tests/ pytest.ini MIGRATION_PLAN.md QUICK_START_MIGRATION.md
git commit -m "feat: add new architecture components and tests"
```

### 2.3. Обновление bot.py (готовый код)
Замените содержимое `bot.py` на:

```python
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
        
        # Инициализируем хендлеры
        self.query_handler = QueryHandler(self.api_client)
        self.command_handlers = CommandHandlers(self.api_client, self.query_handler)
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
```

### 2.4. Тестирование обновленного bot.py
```bash
# Пересборка с новым кодом
make local-rebuild

# Проверка логов
make local-logs

# Должны увидеть:
# "Starting CloverdashBot with new architecture..."
# "Config: retries=3, timeout=30s"

# Тестирование в Telegram:
# /start - должен работать как раньше
# /help - должен работать
# /settings - должен работать
```

### 2.5. Коммит изменений
```bash
git add bot.py
git commit -m "feat: migrate bot.py to new architecture"
```

## ✅ Проверочный чеклист

### Этап 1 ✅
- [ ] Новые модули импортируются без ошибок
- [ ] Тесты проходят успешно  
- [ ] Текущий бот работает корректно
- [ ] Создана резервная копия
- [ ] Создана ветка для миграции

### Этап 2 (После обновления bot.py)
- [ ] Бот запускается без ошибок
- [ ] В логах видно "new architecture"
- [ ] Команда /start работает
- [ ] Команда /help работает
- [ ] Команда /settings работает
- [ ] Inline кнопки работают
- [ ] Обработка запросов работает

## 🚨 Что делать если что-то пошло не так

### Быстрый откат
```bash
# Вернуться к рабочей версии
cp bot.py.backup bot.py
make local-rebuild

# Или откат через git
git checkout main
make local-rebuild
```

### Отладка проблем
```bash
# Проверка импортов
python3 -c "import config, models, exceptions, services"

# Проверка конфигурации
python3 -c "
from config import Config
try:
    config = Config.load_from_env()
    print('✅ Config loaded successfully')
    print(f'Backend URL: {config.backend_url}')
except Exception as e:
    print(f'❌ Config error: {e}')
"

# Детальные логи
make local-logs | grep -E "(ERROR|WARN|Starting)"
```

## 🎉 Следующие шаги

После успешного завершения этапа 2:

1. **Этап 3**: Миграция handlers.py (один handler за раз)
2. **Этап 4**: Миграция query_handler.py  
3. **Этап 5**: Миграция api_client.py
4. **Этап 6**: Финализация и документация

**Общее время миграции**: 3-5 дней работы
**Риски**: Минимальные благодаря поэтапному подходу

---

*Следуйте плану пошагово, тестируйте после каждого изменения, и не торопитесь!* 