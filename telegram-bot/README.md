# Telegram Bot для CloverdashBot

Telegram бот для взаимодействия с пользователями и отправки запросов к backend API.

## Создание Telegram Bot

### 1. Получение токена

1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Введите имя бота (например: "CloverdashBot")
   - Введите username бота (например: "cloverdash_bot")
4. Получите токен бота (выглядит как: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Настройка переменных окружения

Создайте файл `.env` в папке `telegram-bot/`:

```bash
TELEGRAM_TOKEN=ваш_токен_бота
BACKEND_URL=http://localhost:8000
```

## Запуск

### Docker запуск (рекомендуется)

```bash
cd telegram-bot

# Собрать и запустить
make build
make up

# Или одной командой
make rebuild
```

### Доступные команды

```bash
make help      # Показать все доступные команды
make build     # Собрать образ telegram-bot
make up        # Запустить telegram-bot
make down      # Остановить telegram-bot
make logs      # Показать логи telegram-bot
make restart   # Перезапустить telegram-bot
make clean     # Остановить и удалить контейнер
make shell     # Войти в контейнер telegram-bot
make status    # Показать статус сервиса
```

### Локальный запуск

```bash
cd telegram-bot
pip install -r requirements.txt
python bot.py
```

## Использование

1. Найдите вашего бота в Telegram по username
2. Отправьте команду `/start`
3. Задавайте вопросы о данных на естественном языке

### Примеры вопросов:

- "Покажи топ-10 клиентов по объему продаж"
- "Сколько новых пользователей зарегистрировалось на этой неделе?"
- "Какой средний чек в разрезе по регионам?"

## Структура файлов

```
telegram-bot/
├── bot.py                 # Основной файл бота
├── test_bot.py           # Тесты бота
├── requirements.txt      # Зависимости Python
├── docker-compose.yml    # Docker Compose для бота
├── Makefile             # Команды управления
├── Dockerfile           # Docker образ
├── .dockerignore        # Исключения для Docker
└── README.md            # Документация
```

## Команды бота

- `/start` - Начало работы с ботом
- `/help` - Справка по использованию

## Логирование

Бот логирует все взаимодействия с пользователями и ошибки подключения к backend.

## Устранение неполадок

1. **Бот не отвечает**: Проверьте, что backend запущен и доступен по адресу `http://localhost:8000`
2. **Ошибки подключения**: Убедитесь, что BACKEND_URL указан правильно в `.env`
3. **Неверный токен**: Проверьте TELEGRAM_TOKEN в .env файле
4. **Проблемы с Docker**: 
   - Остановите старые контейнеры: `make down`
   - Для полной очистки: `make clean`
   - Пересборка: `make rebuild` 