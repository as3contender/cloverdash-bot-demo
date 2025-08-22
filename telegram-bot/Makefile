.PHONY: help build up down logs clean restart shell local-build local-up local-start local-down local-logs local-shell test test-unit test-integration test-cov install-dev

# Переменные
COMPOSE_FILE = docker-compose.yml
COMPOSE_LOCAL_FILE = docker-compose.local.yml
SERVICE_BOT = telegram-bot

# Помощь
help:
	@echo "Доступные команды для Telegram Bot:"
	@echo ""
	@echo "=== Production команды ==="
	@echo "  build        - Собрать образ telegram-bot (production)"
	@echo "  up           - Запустить telegram-bot (production)"
	@echo "  down         - Остановить telegram-bot (production)"
	@echo "  logs         - Показать логи telegram-bot (production)"
	@echo "  restart      - Перезапустить telegram-bot (production)"
	@echo "  clean        - Остановить и удалить контейнер (production)"
	@echo "  shell        - Войти в контейнер telegram-bot (production)"
	@echo "  status       - Показать статус сервиса"
	@echo ""
	@echo "=== Local Development команды ==="
	@echo "  local-build  - Собрать образ telegram-bot (local development)"
	@echo "  local-up     - Собрать и запустить telegram-bot (local development)"
	@echo "  local-start  - Запустить telegram-bot без сборки (local development)"
	@echo "  local-down   - Остановить telegram-bot (local development)"
	@echo "  local-logs   - Показать логи telegram-bot (local development)"
	@echo "  local-shell  - Войти в контейнер telegram-bot (local development)"
	@echo "  local-rebuild- Полная пересборка для локальной разработки"
	@echo ""
	@echo "=== Testing команды ==="
	@echo "  install-dev  - Установить зависимости для разработки"
	@echo "  test         - Запустить все тесты"
	@echo "  test-unit    - Запустить unit тесты"
	@echo "  test-integration - Запустить integration тесты"
	@echo "  test-cov     - Запустить тесты с отчетом о покрытии"

# Команды для управления
build:
	docker-compose -f $(COMPOSE_FILE) build

up:
	docker-compose -f $(COMPOSE_FILE) up -d

down:
	docker-compose -f $(COMPOSE_FILE) down

logs:
	docker-compose -f $(COMPOSE_FILE) logs -f

restart:
	docker-compose -f $(COMPOSE_FILE) restart

clean:
	docker-compose -f $(COMPOSE_FILE) down
	docker system prune -f

shell:
	docker-compose -f $(COMPOSE_FILE) exec $(SERVICE_BOT) bash

status:
	docker-compose -f $(COMPOSE_FILE) ps

# Полная пересборка и запуск (production)
rebuild:
	docker-compose -f $(COMPOSE_FILE) down
	docker-compose -f $(COMPOSE_FILE) build --no-cache
	docker-compose -f $(COMPOSE_FILE) up -d 

# === Local Development команды ===
local-build:
	docker-compose -f $(COMPOSE_LOCAL_FILE) build

local-up:
	docker-compose -f $(COMPOSE_LOCAL_FILE) build
	docker-compose -f $(COMPOSE_LOCAL_FILE) up -d

local-start:
	docker-compose -f $(COMPOSE_LOCAL_FILE) up -d

local-down:
	docker-compose -f $(COMPOSE_LOCAL_FILE) down

local-logs:
	docker-compose -f $(COMPOSE_LOCAL_FILE) logs -f

local-shell:
	docker-compose -f $(COMPOSE_LOCAL_FILE) exec $(SERVICE_BOT) bash

local-restart:
	docker-compose -f $(COMPOSE_LOCAL_FILE) restart

local-status:
	docker-compose -f $(COMPOSE_LOCAL_FILE) ps

local-clean:
	docker-compose -f $(COMPOSE_LOCAL_FILE) down
	docker system prune -f

# Полная пересборка для локальной разработки
local-rebuild:
	docker-compose -f $(COMPOSE_LOCAL_FILE) down
	docker-compose -f $(COMPOSE_LOCAL_FILE) build --no-cache
	docker-compose -f $(COMPOSE_LOCAL_FILE) up -d

# === Testing команды ===
install-dev:
	pip install -r requirements.txt

test:
	python -m pytest

test-unit:
	python -m pytest -m unit

test-integration:
	python -m pytest -m integration

test-cov:
	python -m pytest --cov=. --cov-report=html --cov-report=term-missing

test-fast:
	python -m pytest -x --tb=short

test-verbose:
	python -m pytest -v --tb=long 