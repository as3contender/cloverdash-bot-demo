# 🚀 Развертывание CloverdashBot

## Быстрый старт

```bash
# 1. Перейти в папку развертывания
cd deployment

# 2. Настроить конфигурацию
./setup_deploy.sh

# 3. Развернуть на сервере
./deploy_all.sh
```

## Что будет развернуто

- ✅ **Backend API** на порту 8000
- ✅ **Telegram Bot** подключенный к API
- ✅ **Docker/docker-compose** (установятся автоматически)
- ✅ **Автоматические health checks**
- ✅ **Production конфигурация**

## Требования

- SSH доступ к серверу
- PostgreSQL уже настроен на сервере
- Файлы `.env` в папках `backend/` и `telegram-bot/`

## Управление

```bash
cd deployment

# Просмотр логов
./logs.sh backend
./logs.sh bot

# Диагностика Docker
./test_docker_installation.sh

# Исправление проблем
./fix_docker_compose.sh
```

## Подробная документация

📚 **[deployment/README.md](deployment/README.md)** - быстрый старт  
📚 **[deployment/DEPLOYMENT_README.md](deployment/DEPLOYMENT_README.md)** - полная документация

---

⏱️ **Время развертывания**: 5-8 минут  
🎯 **Команда**: `cd deployment && ./deploy_all.sh` 