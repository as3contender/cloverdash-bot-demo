# Настройка Docker Compose для CloverdashBot

## Предварительные требования

1. Установленный Docker и Docker Compose
2. OpenAI API ключ
3. **Запущенная PostgreSQL база данных** (локально или удаленно)
4. **Telegram Bot Token** (для запуска бота)

## Настройка

### 1. Создайте файл .env

Создайте файл `.env` в корне проекта со следующим содержимым:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_actual_openai_api_key_here

# Database Configuration (подключение к внешней PostgreSQL)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_NAME=your_database_name

# Telegram Bot Configuration
TELEGRAM_TOKEN=your_telegram_bot_token_here
BACKEND_URL=http://localhost:8000

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_TITLE=CloverdashBot Backend
API_VERSION=1.0.0

# Security
ALLOWED_ORIGINS=["*"]

# Logging
LOG_LEVEL=INFO
```

**Важно:** 
- Замените `your_actual_openai_api_key_here` на ваш реальный OpenAI API ключ
- Замените `your_telegram_bot_token_here` на ваш Telegram Bot Token
- Настройте параметры подключения к вашей PostgreSQL базе данных

### 2. Запуск сервисов

#### Запуск всех сервисов
```bash
# Запуск backend и telegram-bot
docker-compose up -d

# Просмотр логов всех сервисов
docker-compose logs -f

# Остановка всех сервисов
docker-compose down
```

#### Раздельный запуск сервисов

**Только Backend:**
```bash
# Собрать и запустить только backend
make build-backend
make up-backend

# Или через docker-compose
docker-compose up -d backend
```

**Только Telegram Bot:**
```bash
# Собрать и запустить только telegram-bot
make build-bot
make up-bot

# Или через docker-compose
docker-compose up -d telegram-bot
```

### 3. Проверка работы

После запуска:
- Backend API будет доступен по адресу: http://localhost:8000
- Документация API: http://localhost:8000/docs
- Telegram Bot будет работать в Telegram

## Структура сервисов

- **backend**: FastAPI приложение (порт 8000)
- **telegram-bot**: Telegram Bot (без внешних портов)

## Подключение к базе данных

Backend настроен для подключения к внешней PostgreSQL базе данных:

- **Локальная база**: используйте `DATABASE_HOST=localhost`
- **Удаленная база**: укажите IP адрес или домен
- **Docker база**: используйте `DATABASE_HOST=host.docker.internal` (для macOS/Windows)

## Полезные команды

### Общие команды
```bash
# Пересборка и запуск всех сервисов
docker-compose up --build -d

# Просмотр логов всех сервисов
docker-compose logs -f

# Остановка всех сервисов
docker-compose down

# Статус сервисов
docker-compose ps
```

### Backend команды
```bash
# Сборка и запуск только backend
make build-backend
make up-backend

# Просмотр логов backend
make logs-backend

# Вход в контейнер backend
make shell

# Запуск тестов
make test
```

### Telegram Bot команды
```bash
# Сборка и запуск только telegram-bot
make build-bot
make up-bot

# Просмотр логов telegram-bot
make logs-bot

# Вход в контейнер telegram-bot
make shell-bot
```

## Устранение неполадок

1. **Проблемы с подключением к базе данных**: 
   - Убедитесь, что PostgreSQL запущен и доступен
   - Проверьте правильность параметров подключения в .env
   - Для локальной базы на macOS/Windows используйте `host.docker.internal`

2. **Проблемы с API ключом**: Проверьте, что в .env файле указан правильный OpenAI API ключ

3. **Проблемы с Telegram Bot**: 
   - Убедитесь, что TELEGRAM_TOKEN указан правильно
   - Проверьте, что BACKEND_URL доступен для бота

4. **Проблемы с портами**: Убедитесь, что порт 8000 не занят другими приложениями

## Примеры конфигурации

### Локальная PostgreSQL
```bash
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=password
DATABASE_NAME=cloverdash_db
```

### Удаленная PostgreSQL
```bash
DATABASE_HOST=your-db-server.com
DATABASE_PORT=5432
DATABASE_USER=db_user
DATABASE_PASSWORD=db_password
DATABASE_NAME=production_db
```

### PostgreSQL в Docker (отдельный контейнер)
```bash
DATABASE_HOST=host.docker.internal
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=password
DATABASE_NAME=cloverdash_db
```

### Telegram Bot конфигурация
```bash
# Для локального backend
BACKEND_URL=http://localhost:8000

# Для backend в Docker
BACKEND_URL=http://backend:8000
``` 