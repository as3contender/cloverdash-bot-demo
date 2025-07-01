# Быстрый запуск CloverdashBot с Docker

## 1. Подготовка

```bash
# Создайте файл .env в корне проекта
# Скопируйте содержимое из docker-setup.md и настройте параметры
OPENAI_API_KEY=your_actual_openai_api_key_here
TELEGRAM_TOKEN=your_telegram_bot_token_here

# Подключение к PostgreSQL
DATABASE_HOST=localhost  # или host.docker.internal для Docker базы
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_NAME=your_database_name

# Backend URL для бота
BACKEND_URL=http://localhost:8000
```

**Важно:** Убедитесь, что PostgreSQL база данных запущена и доступна!

## 2. Запуск

### Все сервисы сразу
```bash
# Собрать и запустить backend и telegram-bot
make build
make up

# Или одной командой
docker-compose up --build -d
```

### Раздельный запуск

**Только Backend:**
```bash
make build-backend
make up-backend
```

**Только Telegram Bot:**
```bash
make build-bot
make up-bot
```

## 3. Проверка

- Backend API: http://localhost:8000
- API документация: http://localhost:8000/docs
- Telegram Bot: найдите вашего бота в Telegram

## 4. Полезные команды

```bash
# Просмотр логов всех сервисов
make logs

# Просмотр логов конкретного сервиса
make logs-backend
make logs-bot

# Остановка всех сервисов
make down

# Остановка конкретного сервиса
make down-backend
make down-bot

# Перезапуск
make restart

# Вход в контейнеры
make shell        # backend
make shell-bot    # telegram-bot
```

## 5. Остановка и очистка

```bash
# Остановить все сервисы
make down

# Полная очистка
make clean
```

## Подключение к базе данных

- **Локальная PostgreSQL**: `DATABASE_HOST=localhost`
- **Docker PostgreSQL**: `DATABASE_HOST=host.docker.internal`
- **Удаленная база**: укажите IP или домен

## Сценарии использования

1. **Разработка backend**: `make up-backend`
2. **Тестирование бота**: `make up-bot` (backend должен быть запущен)
3. **Полная система**: `make up`

Подробная документация: [docker-setup.md](docker-setup.md) 