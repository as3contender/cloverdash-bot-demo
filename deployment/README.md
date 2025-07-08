# 🚀 CloverdashBot Deployment

Скрипты для развертывания CloverdashBot на удаленном сервере с исправленными сетевыми настройками.

## 📁 Структура папки

### 🔧 Основные скрипты
- **`deploy_all.sh`** - Полное развертывание (Backend API + Telegram Bot)
- **`deploy_bot_only.sh`** - Развертывание только Telegram Bot

### ⚙️ Конфигурация
- **`deploy.env`** - Рабочая конфигурация развертывания
- **`deploy.env.example`** - Пример конфигурации

### 🛠️ Вспомогательные скрипты
- **`logs.sh`** - Просмотр логов сервисов
- **`secure_cleanup.sh`** - Безопасная очистка контейнеров

### 📦 Архив
- **`archive_debug_scripts/`** - Отладочные скрипты (сохранены на случай необходимости)

## 🚀 Быстрый старт

### 1. Настройка конфигурации
```bash
# Скопируйте пример конфигурации
cp deploy.env.example deploy.env

# Отредактируйте под ваш сервер
nano deploy.env
```

### 2. Полное развертывание
```bash
# Развертывание backend + bot
./deploy_all.sh
```

### 3. Развертывание только бота
```bash
# Если backend уже работает
./deploy_bot_only.sh
```

## ⚙️ Конфигурация (deploy.env)

```bash
# SSH настройки
REMOTE_HOST=your-server.com
REMOTE_USER=root
SSH_KEY_PATH=~/.ssh/your-key

# Развертывание
REMOTE_DEPLOY_DIR=/opt/cloverdash-bot
DEPLOY_BACKEND=true
DEPLOY_BOT=true
```

## 🌐 Сетевая архитектура

После развертывания создается общая Docker сеть `cloverdash-network`:

```
┌─────────────────────────────────────────────────────┐
│                cloverdash-network                   │
│                                                     │
│  ┌─────────────────────────┐  ┌─────────────────────┐  │
│  │   cloverdash_backend    │  │ cloverdash_telegram │  │
│  │   172.19.0.2:8000       │◄─┤ _bot 172.19.0.3    │  │
│  │   (FastAPI + DB)        │  │ (Python Bot)        │  │
│  └─────────────────────────┘  └─────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
                           │
                    ┌─────────────┐
                    │ Host:8000   │ ← External Access
                    └─────────────┘
```

## 🔍 Мониторинг

### Просмотр логов
```bash
# Все логи
./logs.sh

# Логи backend
ssh user@server 'cd /opt/cloverdash-bot/backend && docker-compose logs -f'

# Логи bot
ssh user@server 'cd /opt/cloverdash-bot/telegram-bot && docker-compose logs -f'
```

### Проверка статуса
```bash
# Статус всех контейнеров
ssh user@server 'docker ps'

# Health check backend
curl http://your-server:8000/health/
```

## 🛠️ Устранение неполадок

### Перезапуск сервисов
```bash
# Перезапуск backend
ssh user@server 'cd /opt/cloverdash-bot/backend && docker-compose restart'

# Перезапуск bot
ssh user@server 'cd /opt/cloverdash-bot/telegram-bot && docker-compose restart'
```

### Очистка системы
```bash
# Безопасная очистка
./secure_cleanup.sh
```

## 📋 Требования

- ✅ Настроенный SSH доступ к серверу
- ✅ Ubuntu/Debian/CentOS сервер
- ✅ Минимум 2GB RAM (рекомендуется 4GB)
- ✅ Docker устанавливается автоматически

## 🎯 Готовые endpoints

После успешного развертывания доступны:

- **API:** `http://your-server:8000`
- **Документация:** `http://your-server:8000/docs`
- **Health Check:** `http://your-server:8000/health/`
- **Telegram Bot:** готов принимать сообщения

## 🔧 Особенности

### ✅ Исправления в этой версии
- 🌐 **Исправлены сетевые настройки** - контейнеры теперь используют общую сеть
- 🔗 **Правильный BACKEND_URL** - `http://cloverdash_backend:8000`
- 📦 **Оптимизированный RSYNC** - исправлены ошибки копирования файлов
- 🚀 **Автоматическое создание сети** - `cloverdash-network` создается автоматически

### 🛡️ Безопасность
- SSH ключи для доступа
- Изолированные Docker контейнеры
- Минимальная поверхность атаки

---

**📝 Примечание:** Отладочные скрипты сохранены в `archive_debug_scripts/` на случай необходимости. 