# 🚀 CloverdashBot - Production Deployment

Автоматическое развертывание полного стека CloverdashBot (Backend API + Telegram Bot) на удаленном сервере.

## ✨ Возможности

- 🚀 **Полный автоматический деплой** - одна команда развертывает весь стек
- 🐳 **Автоматическая установка Docker** - проверка и установка Docker/docker-compose
- 🔧 **Гибкая конфигурация** - настройка через файл или параметры командной строки  
- 🎯 **Селективный деплой** - можно развертывать только backend или только bot
- 🔐 **Безопасное SSH подключение** - поддержка SSH ключей и стандартной конфигурации
- 📊 **Health checks** - автоматическая проверка работоспособности сервисов
- 🧹 **Автоочистка** - удаление старых контейнеров и образов перед деплоем
- 📝 **Подробное логирование** - цветной вывод с детальной информацией
- 🔍 **Диагностика Docker** - отдельный скрипт для тестирования Docker установки

## 🎯 Один скрипт для развертывания всего

### 1. Настройка конфигурации развертывания:
```bash
# Создайте файл конфигурации развертывания
cp deploy.env.example deploy.env

# Отредактируйте deploy.env под ваши нужды
nano deploy.env
```

### 2. Варианты развертывания:

#### Полное развертывание (Backend + Bot):
```bash
./deploy_all.sh
```

#### Только Backend API:
```bash
./deploy_all.sh --backend-only
```

#### Только Telegram Bot:
```bash
./deploy_all.sh --bot-only
```

#### Переопределение параметров из командной строки:
```bash
./deploy_all.sh -h your-server.com -u ubuntu -k ~/.ssh/custom_key
```

#### Тестирование Docker установки перед развертыванием:
```bash
# Проверить Docker/docker-compose на сервере
./test_docker_installation.sh

# С custom параметрами
./test_docker_installation.sh -h your-server.com -u ubuntu
```

## 📦 Что включает в себя развертывание

### 🔧 Backend API (`backend/`)
- **FastAPI** приложение с аутентификацией
- **PostgreSQL** подключение к двум базам данных:
  - App Database (пользователи, настройки)
  - Data Database (пользовательские данные для запросов)
- **OpenAI API** интеграция для генерации SQL запросов
- **JWT Authentication** для безопасности
- **Health checks** и мониторинг
- **Порт**: 8000

### 🤖 Telegram Bot (`telegram-bot/`)
- **Python Telegram Bot** (python-telegram-bot)
- **Подключение к Backend API** через localhost:8000
- **Автоматическая аутентификация** пользователей через Telegram
- **Команды**: /start, /help, /tables, /sample
- **Обработка запросов** на естественном языке
- **Автоматический перезапуск** при сбоях

## 🔧 Требования

### На локальной машине:
- ✅ SSH доступ к серверу с ключом (по умолчанию `id_ed25519_do_cloverdash-bot`)
- ✅ Настроенный файл `deploy.env` с параметрами сервера
- ✅ Настроенные `.env` файлы в папках `backend/` и `telegram-bot/`

### На сервере:
- ✅ Ubuntu/Debian Linux
- ✅ PostgreSQL уже установлен и настроен (две базы данных)
- ✅ Открытый порт 8000 для API
- ✅ Docker и Docker Compose (будут установлены автоматически)

### Файлы конфигурации:
- ✅ `deploy.env` - параметры развертывания (сервер, ключи, настройки)
- ✅ `backend/.env` - конфигурация backend приложения
- ✅ `telegram-bot/.env` - конфигурация Telegram бота

## ⚙️ Конфигурация

### Deployment Config (`deploy.env`):
```env
# Server Configuration
REMOTE_HOST=64.227.69.138
REMOTE_USER=root
SSH_KEY_PATH=~/.ssh/id_ed25519_do_cloverdash-bot

# Deployment Options
DEPLOY_BACKEND=true
DEPLOY_BOT=true

# Optional: Custom deployment directory on server
REMOTE_DEPLOY_DIR=/opt/cloverdash-bot

# Optional: Docker Registry (если используете приватный реестр)
# DOCKER_REGISTRY=your-registry.com
# DOCKER_USERNAME=your-username
# DOCKER_PASSWORD=your-password
```

### Backend (.env в `backend/`):
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0

# Application Database Configuration (пользователи, история, настройки)
APP_DATABASE_URL=postgresql://app_user:app_password@localhost:5432/cloverdash_app
# или отдельно:
APP_DATABASE_HOST=64.227.69.138  # будет изменено на localhost при развертывании
APP_DATABASE_PORT=5432
APP_DATABASE_USER=app_user
APP_DATABASE_PASSWORD=app_password
APP_DATABASE_NAME=cloverdash_app

# Data Database Configuration (пользовательские данные для запросов)
DATA_DATABASE_URL=postgresql://data_user:data_password@localhost:5433/cloverdash_data
# или отдельно:
DATA_DATABASE_HOST=64.227.69.138  # будет изменено на localhost при развертывании
DATA_DATABASE_PORT=5433
DATA_DATABASE_USER=data_user
DATA_DATABASE_PASSWORD=data_password
DATA_DATABASE_NAME=cloverdash_data

# Security (будет автоматически сгенерирован новый ключ)
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ALLOWED_ORIGINS=["*"]
LOG_LEVEL=INFO
```

### Bot (.env в `telegram-bot/`):
```env
# Bot Token (получить от @BotFather в Telegram)
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# API URL (будет изменено на localhost при развертывании)
BACKEND_URL=http://64.227.69.138:8000
```

## 🚀 Процесс развертывания

### 1. Подготовка:
```bash
# 1. Создайте конфигурацию развертывания
cp deploy.env.example deploy.env
# Отредактируйте deploy.env с параметрами вашего сервера

# 2. Создайте .env файлы для приложений
cp backend/env_example.txt backend/.env
# Отредактируйте backend/.env с вашими настройками

# 3. Создайте .env файл для бота
echo "TELEGRAM_TOKEN=your_bot_token_here" > telegram-bot/.env
echo "BACKEND_URL=http://your-server-ip:8000" >> telegram-bot/.env
```

### 2. Автоматическое развертывание:
- ✅ Загрузка конфигурации из `deploy.env`
- ✅ Проверка SSH подключения с настроенным ключом
- ✅ Проверка наличия конфигурационных файлов (backend/.env, telegram-bot/.env)
- ✅ Очистка предыдущих развертываний
- ✅ Копирование файлов на сервер в указанную директорию
- ✅ Автоматическая настройка конфигураций для продакшена
- ✅ Установка Docker/Docker Compose (если нужно)
- ✅ Генерация нового SECRET_KEY для безопасности
- ✅ Сборка и запуск контейнеров
- ✅ Health checks и проверки

### 3. Результат:
- ✅ Backend API доступен на порту 8000
- ✅ Telegram Bot отвечает на сообщения
- ✅ Автоматический мониторинг и перезапуск
- ✅ Безопасная конфигурация для продакшена

## 🔍 Проверка после развертывания

### API:
```bash
# Загрузите переменные из deploy.env
source deploy.env 2>/dev/null || true
REMOTE_HOST=${REMOTE_HOST:-64.227.69.138}

# Health check
curl http://$REMOTE_HOST:8000/api/v1/health

# API документация
open http://$REMOTE_HOST:8000/docs
```

### Bot:
1. Найдите бота в Telegram по username
2. Отправьте `/start`
3. Попробуйте команды:
   - `/help` - справка
   - `/tables` - список таблиц
   - `/sample table_name` - примеры данных
   - Задайте вопрос на естественном языке

### Статус сервисов:
```bash
# Загрузите переменные из deploy.env или используйте значения по умолчанию
source deploy.env 2>/dev/null || true
SSH_KEY_PATH=${SSH_KEY_PATH:-~/.ssh/id_ed25519_do_cloverdash-bot}
REMOTE_USER=${REMOTE_USER:-root}
REMOTE_HOST=${REMOTE_HOST:-64.227.69.138}
REMOTE_DEPLOY_DIR=${REMOTE_DEPLOY_DIR:-/opt/cloverdash-bot}

ssh -i $SSH_KEY_PATH $REMOTE_USER@$REMOTE_HOST \
  "cd $REMOTE_DEPLOY_DIR && find . -name 'docker-compose*.yml' -exec docker-compose -f {} ps \\;"
```

## 📊 Управление

### Просмотр логов:
```bash
# Загрузите переменные из deploy.env
source deploy.env 2>/dev/null || true
SSH_KEY_PATH=${SSH_KEY_PATH:-~/.ssh/id_ed25519_do_cloverdash-bot}
REMOTE_USER=${REMOTE_USER:-root}
REMOTE_HOST=${REMOTE_HOST:-64.227.69.138}
REMOTE_DEPLOY_DIR=${REMOTE_DEPLOY_DIR:-/opt/cloverdash-bot}

# Backend logs
ssh -i $SSH_KEY_PATH $REMOTE_USER@$REMOTE_HOST \
  "cd $REMOTE_DEPLOY_DIR/backend && docker-compose logs -f"

# Bot logs  
ssh -i $SSH_KEY_PATH $REMOTE_USER@$REMOTE_HOST \
  "cd $REMOTE_DEPLOY_DIR/telegram-bot && docker-compose logs -f"
```

### Перезапуск сервисов:
```bash
# Загрузите переменные из deploy.env
source deploy.env 2>/dev/null || true
SSH_KEY_PATH=${SSH_KEY_PATH:-~/.ssh/id_ed25519_do_cloverdash-bot}
REMOTE_USER=${REMOTE_USER:-root}
REMOTE_HOST=${REMOTE_HOST:-64.227.69.138}
REMOTE_DEPLOY_DIR=${REMOTE_DEPLOY_DIR:-/opt/cloverdash-bot}

# Backend
ssh -i $SSH_KEY_PATH $REMOTE_USER@$REMOTE_HOST \
  "cd $REMOTE_DEPLOY_DIR/backend && docker-compose restart"

# Bot
ssh -i $SSH_KEY_PATH $REMOTE_USER@$REMOTE_HOST \
  "cd $REMOTE_DEPLOY_DIR/telegram-bot && docker-compose restart"
```

### Обновление:
Просто запустите развертывание снова:
```bash
./deploy_all.sh
```

## 🔐 Безопасность

### ✅ Автоматически обеспечивается:
- **Новый SECRET_KEY** для JWT при каждом развертывании
- **Non-root контейнеры** для безопасности
- **JWT Authentication** для всех API запросов
- **Валидация конфигураций** перед запуском
- **Health monitoring** для стабильности
- **Раздельные базы данных** для приложения и данных

### ⚠️ Важные моменты:
- Используйте надежные пароли для PostgreSQL
- Регулярно обновляйте OpenAI API ключи
- Проверяйте логи на подозрительную активность

## 🛠 Отладка

### Диагностика Docker:
```bash
# Полная диагностика Docker на сервере
./test_docker_installation.sh

# С custom параметрами
./test_docker_installation.sh -h your-server.com -u ubuntu
```

Этот скрипт проверит:
- ✅ Установку и версию Docker
- ✅ Установку и версию docker-compose  
- ✅ Работоспособность Docker daemon
- ✅ Сетевое подключение для загрузки образов
- ✅ Права пользователя для работы с Docker
- ✅ Существующие контейнеры и образы

### Если Backend не запускается:
```bash
# Загрузите переменные из deploy.env
source deploy.env 2>/dev/null || true
SSH_KEY_PATH=${SSH_KEY_PATH:-~/.ssh/id_ed25519_do_cloverdash-bot}
REMOTE_USER=${REMOTE_USER:-root}
REMOTE_HOST=${REMOTE_HOST:-64.227.69.138}
REMOTE_DEPLOY_DIR=${REMOTE_DEPLOY_DIR:-/opt/cloverdash-bot}

# Проверьте логи
ssh -i $SSH_KEY_PATH $REMOTE_USER@$REMOTE_HOST \
  "cd $REMOTE_DEPLOY_DIR/backend && docker-compose logs"

# Проверьте подключение к базам данных
ssh -i $SSH_KEY_PATH $REMOTE_USER@$REMOTE_HOST \
  "cd $REMOTE_DEPLOY_DIR/backend && docker-compose exec backend python -c \"
from services.app_database import get_app_database;
from services.data_database import get_data_database;
print('Testing connections...');
app_db = get_app_database();
data_db = get_data_database();
print('Connections OK')
\""
```

### Если Bot не отвечает:
```bash
# Загрузите переменные из deploy.env
source deploy.env 2>/dev/null || true
SSH_KEY_PATH=${SSH_KEY_PATH:-~/.ssh/id_ed25519_do_cloverdash-bot}
REMOTE_USER=${REMOTE_USER:-root}
REMOTE_HOST=${REMOTE_HOST:-64.227.69.138}
REMOTE_DEPLOY_DIR=${REMOTE_DEPLOY_DIR:-/opt/cloverdash-bot}

# Проверьте логи бота
ssh -i $SSH_KEY_PATH $REMOTE_USER@$REMOTE_HOST \
  "cd $REMOTE_DEPLOY_DIR/telegram-bot && docker-compose logs"

# Проверьте доступность Backend API
ssh -i $SSH_KEY_PATH $REMOTE_USER@$REMOTE_HOST \
  "curl -s http://localhost:8000/api/v1/health"
```

### Если SSH ключ не работает:
```bash
# Загрузите переменные из deploy.env
source deploy.env 2>/dev/null || true
SSH_KEY_PATH=${SSH_KEY_PATH:-~/.ssh/id_ed25519_do_cloverdash-bot}
REMOTE_USER=${REMOTE_USER:-root}
REMOTE_HOST=${REMOTE_HOST:-64.227.69.138}

# Проверьте права доступа к ключу
chmod 600 $SSH_KEY_PATH

# Добавьте ключ в ssh-agent
ssh-add $SSH_KEY_PATH

# Проверьте подключение
ssh -i $SSH_KEY_PATH $REMOTE_USER@$REMOTE_HOST 'echo "Connection OK"'
```

### Ручное управление базами данных:
```bash
# Загрузите переменные из deploy.env
source deploy.env 2>/dev/null || true
SSH_KEY_PATH=${SSH_KEY_PATH:-~/.ssh/id_ed25519_do_cloverdash-bot}
REMOTE_USER=${REMOTE_USER:-root}
REMOTE_HOST=${REMOTE_HOST:-64.227.69.138}

# Подключение к app database
ssh -i $SSH_KEY_PATH $REMOTE_USER@$REMOTE_HOST \
  "psql -h localhost -U app_user -d cloverdash_app"

# Подключение к data database
ssh -i $SSH_KEY_PATH $REMOTE_USER@$REMOTE_HOST \
  "psql -h localhost -U data_user -d cloverdash_data"
```

## 🎯 Структура развертывания

```
${REMOTE_DEPLOY_DIR:-/opt/cloverdash-bot}/
├── backend/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── .env                    # Автоматически настроен для продакшена
│   ├── main.py
│   ├── requirements.txt
│   └── ...                     # Все файлы backend
│
├── telegram-bot/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── .env                    # Автоматически настроен для продакшена
│   ├── bot.py
│   ├── requirements.txt
│   └── ...                     # Все файлы telegram-bot
```

**Примечание**: Путь развертывания настраивается в `deploy.env` файле через переменную `REMOTE_DEPLOY_DIR`.

## 🎉 Готово!

После успешного развертывания у вас будет:

- 🔗 **Backend API**: `http://${REMOTE_HOST}:8000`
- 📚 **API Docs**: `http://${REMOTE_HOST}:8000/docs`
- 🤖 **Telegram Bot**: Работает и отвечает на сообщения
- 🔐 **JWT Authentication**: Автоматическая аутентификация через Telegram
- 🗄️ **Database Integration**: Подключение к двум PostgreSQL базам
- 🧠 **AI Integration**: OpenAI для генерации SQL запросов
- 🔄 **Auto-restart**: Автоматический перезапуск при сбоях

**Время развертывания**: 5-8 минут для полного стека

**Команда для запуска**:
```bash
./deploy_all.sh
```

🎯 **Production Ready!** 