#!/usr/bin/env python3
"""
Простой тестовый скрипт для проверки работы Telegram бота
"""

import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TELEGRAM_TOKEN = "7380855161:AAGSyOP8hT-0lk4b2emmN7CGTP34sd7M97w"

async def start_command(update: Update, context) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f'Привет, {user.first_name}! 👋\n\n'
        'Я CloverdashBot - бот для работы с базой данных через естественный язык.\n\n'
        'Доступные команды:\n'
        '/start - Начать работу\n'
        '/help - Показать справку\n'
        '/test - Тестовая команда\n\n'
        'Просто напишите мне вопрос на естественном языке!'
    )

async def help_command(update: Update, context) -> None:
    """Обработчик команды /help"""
    await update.message.reply_text(
        '📚 Справка по CloverdashBot:\n\n'
        'Я могу помочь вам:\n'
        '• Отвечать на вопросы о данных\n'
        '• Генерировать SQL запросы\n'
        '• Показывать доступные таблицы\n\n'
        'Просто напишите ваш вопрос, например:\n'
        '"Сколько пользователей в системе?"\n'
        '"Покажи последние заказы"\n\n'
        'Команды:\n'
        '/start - Начать работу\n'
        '/help - Эта справка\n'
        '/test - Тестовая команда'
    )

async def test_command(update: Update, context) -> None:
    """Обработчик команды /test"""
    await update.message.reply_text(
        '✅ Тест прошел успешно!\n\n'
        'Бот работает корректно.\n'
        'Backend URL: http://localhost:8000\n'
        'Статус: Активен'
    )

async def handle_message(update: Update, context) -> None:
    """Обработчик обычных сообщений"""
    user_message = update.message.text
    user = update.effective_user
    
    logger.info(f"Получено сообщение от {user.first_name}: {user_message}")
    
    # Простой ответ
    response = (
        f'Получил ваше сообщение: "{user_message}"\n\n'
        'К сожалению, backend пока не подключен, но бот работает!\n'
        'Для полной функциональности нужно:\n'
        '1. Запустить backend сервер\n'
        '2. Настроить подключение к базе данных\n\n'
        'Попробуйте команду /test для проверки'
    )
    
    await update.message.reply_text(response)

async def error_handler(update: Update, context) -> None:
    """Обработчик ошибок"""
    logger.error(f"Ошибка при обработке обновления: {context.error}")

def main():
    """Основная функция"""
    print("🤖 Запуск CloverdashBot...")
    print(f"📡 Токен: {TELEGRAM_TOKEN[:10]}...")
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    print("✅ Бот запущен! Нажмите Ctrl+C для остановки")
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
