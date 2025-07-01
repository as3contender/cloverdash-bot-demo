.PHONY: help build up down logs clean restart shell

# Переменные
COMPOSE_FILE = docker-compose.yml
SERVICE_BOT = telegram-bot

# Помощь
help:
	@echo "Доступные команды для Telegram Bot:"
	@echo ""
	@echo "  build     - Собрать образ telegram-bot"
	@echo "  up        - Запустить telegram-bot"
	@echo "  down      - Остановить telegram-bot"
	@echo "  logs      - Показать логи telegram-bot"
	@echo "  restart   - Перезапустить telegram-bot"
	@echo "  clean     - Остановить и удалить контейнер"
	@echo "  shell     - Войти в контейнер telegram-bot"
	@echo "  status    - Показать статус сервиса"

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

# Полная пересборка и запуск
rebuild:
	docker-compose -f $(COMPOSE_FILE) down
	docker-compose -f $(COMPOSE_FILE) build --no-cache
	docker-compose -f $(COMPOSE_FILE) up -d 