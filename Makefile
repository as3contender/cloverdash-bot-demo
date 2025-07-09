.PHONY: help backend-local-up backend-local-down backend-local-logs backend-up backend-down backend-logs bot-up bot-down bot-logs

# Переменные
BACKEND_DIR = backend
BOT_DIR = telegram-bot

# Помощь
help:
	@echo "🚀 CloverdashBot Demo - Команды управления проектом"
	@echo ""
	@echo "=== Backend (FastAPI) ==="
	@echo "  backend-local-up     - Запустить backend для локальной разработки"
	@echo "  backend-local-down   - Остановить backend (локальная разработка)"
	@echo "  backend-local-logs   - Логи backend (локальная разработка)"
	@echo "  backend-up           - Запустить backend (production)"
	@echo "  backend-down         - Остановить backend (production)"
	@echo "  backend-logs         - Логи backend (production)"
	@echo ""
	@echo "=== Telegram Bot ==="
	@echo "  bot-up               - Запустить telegram bot"
	@echo "  bot-down             - Остановить telegram bot"
	@echo "  bot-logs             - Логи telegram bot"
	@echo ""
	@echo "=== Полный стек ==="
	@echo "  local-up             - Запустить весь стек для локальной разработки"
	@echo "  local-down           - Остановить весь стек (локальная разработка)"
	@echo "  up                   - Запустить весь стек (production)"
	@echo "  down                 - Остановить весь стек (production)"
	@echo "  logs                 - Показать логи всех сервисов"
	@echo ""
	@echo "=== Утилиты ==="
	@echo "  status               - Статус всех сервисов"
	@echo "  clean                - Очистка всех контейнеров и образов"

# === Backend команды ===
backend-local-up:
	@echo "🚀 Запуск Backend (локальная разработка)..."
	cd $(BACKEND_DIR) && make local-up

backend-local-down:
	@echo "🛑 Остановка Backend (локальная разработка)..."
	cd $(BACKEND_DIR) && make local-down

backend-local-logs:
	@echo "📋 Логи Backend (локальная разработка)..."
	cd $(BACKEND_DIR) && make local-logs

backend-up:
	@echo "🚀 Запуск Backend (production)..."
	cd $(BACKEND_DIR) && make up

backend-down:
	@echo "🛑 Остановка Backend (production)..."
	cd $(BACKEND_DIR) && make down

backend-logs:
	@echo "📋 Логи Backend (production)..."
	cd $(BACKEND_DIR) && make logs

# === Telegram Bot команды ===
bot-up:
	@echo "🤖 Запуск Telegram Bot..."
	cd $(BOT_DIR) && make local-up

bot-down:
	@echo "🛑 Остановка Telegram Bot..."
	cd $(BOT_DIR) && make local-down

bot-logs:
	@echo "📋 Логи Telegram Bot..."
	cd $(BOT_DIR) && make local-logs

# === Полный стек ===
local-up: backend-local-up
	@echo "⏳ Ожидание запуска Backend..."
	@sleep 5
	@echo "🤖 Запуск Telegram Bot..."
	cd $(BOT_DIR) && make up
	@echo "✅ Весь стек запущен для локальной разработки!"

local-down: bot-down backend-local-down
	@echo "✅ Весь стек остановлен (локальная разработка)"

up: backend-up
	@echo "⏳ Ожидание запуска Backend..."
	@sleep 5
	@echo "🤖 Запуск Telegram Bot..."
	cd $(BOT_DIR) && make up
	@echo "✅ Весь стек запущен (production)!"

down: bot-down backend-down
	@echo "✅ Весь стек остановлен (production)"

logs:
	@echo "📋 Логи всех сервисов..."
	@echo "=== Backend ==="
	cd $(BACKEND_DIR) && make logs &
	@echo "=== Telegram Bot ==="
	cd $(BOT_DIR) && make logs &
	@wait

# === Утилиты ===
status:
	@echo "📊 Статус всех сервисов..."
	@echo "=== Backend ==="
	cd $(BACKEND_DIR) && make status
	@echo ""
	@echo "=== Telegram Bot ==="
	cd $(BOT_DIR) && make status

clean:
	@echo "🧹 Очистка всех контейнеров и образов..."
	cd $(BACKEND_DIR) && make clean
	cd $(BOT_DIR) && make clean
	docker system prune -f
	@echo "✅ Очистка завершена"

# Алиасы для удобства
local: local-up
dev: local-up
start: up
stop: down 