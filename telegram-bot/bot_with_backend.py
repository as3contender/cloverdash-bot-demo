#!/usr/bin/env python3
"""
Telegram бот с интеграцией backend API
"""

import os
import asyncio
import logging
import aiohttp
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
BACKEND_URL = "http://localhost:8000"

async def start_command(update: Update, context) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f'Привет, {user.first_name}! 👋\n\n'
        'Я CloverdashBot - бот для работы с базой данных через естественный язык.\n\n'
        '🚀 **Backend подключен!**\n'
        '✅ Система прав пользователей активна\n'
        '✅ LLM интеграция готова\n\n'
        'Доступные команды:\n'
        '/start - Начать работу\n'
        '/help - Показать справку\n'
        '/tables - Показать доступные таблицы\n'
        '/demo - Информация о системе\n\n'
        'Просто напишите мне вопрос на естественном языке!'
    )

async def help_command(update: Update, context) -> None:
    """Обработчик команды /help"""
    await update.message.reply_text(
        '📚 Справка по CloverdashBot:\n\n'
        'Я могу помочь вам:\n'
        '• Отвечать на вопросы о данных\n'
        '• Генерировать SQL запросы\n'
        '• Показывать доступные таблицы\n'
        '• Работать с правами пользователей\n\n'
        'Примеры вопросов:\n'
        '"Сколько пользователей в системе?"\n'
        '"Покажи последние заказы"\n'
        '"Какие таблицы доступны?"\n\n'
        'Команды:\n'
        '/start - Начать работу\n'
        '/help - Эта справка\n'
        '/tables - Доступные таблицы\n'
        '/demo - Информация о системе'
    )

async def tables_command(update: Update, context) -> None:
    """Обработчик команды /tables"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/tables") as response:
                if response.status == 200:
                    data = await response.json()
                    tables = data.get("tables", [])
                    
                    message = "📋 **Доступные таблицы:**\n\n"
                    for table in tables:
                        message += f"🔹 **{table['name']}**\n"
                        message += f"   Описание: {table['description']}\n"
                        message += f"   Колонки: {', '.join(table['columns'])}\n"
                        message += f"   Доступ: {'✅' if table['accessible'] else '❌'}\n\n"
                    
                    message += f"Всего таблиц: {data.get('total', 0)}"
                    await update.message.reply_text(message)
                else:
                    await update.message.reply_text("❌ Ошибка получения списка таблиц")
    except Exception as e:
        logger.error(f"Error in tables_command: {e}")
        await update.message.reply_text("❌ Ошибка подключения к backend")

async def demo_command(update: Update, context) -> None:
    """Обработчик команды /demo"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/demo") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    message = f"🚀 **{data['message']}**\n\n"
                    message += "**Функции:**\n"
                    for feature in data.get("features", []):
                        message += f"{feature}\n"
                    
                    message += "\n**Следующие шаги:**\n"
                    for step in data.get("next_steps", []):
                        message += f"{step}\n"
                    
                    message += f"\n**Статус:** {data.get('status', 'unknown')}"
                    await update.message.reply_text(message)
                else:
                    await update.message.reply_text("❌ Ошибка получения информации о системе")
    except Exception as e:
        logger.error(f"Error in demo_command: {e}")
        await update.message.reply_text("❌ Ошибка подключения к backend")

async def handle_message(update: Update, context) -> None:
    """Обработчик обычных сообщений"""
    user_message = update.message.text
    user = update.effective_user
    
    logger.info(f"Получено сообщение от {user.first_name}: {user_message}")
    
    try:
        # Отправляем запрос в backend
        async with aiohttp.ClientSession() as session:
            payload = {
                "question": user_message,
                "user_id": str(user.id)
            }
            
            async with session.post(f"{BACKEND_URL}/query", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Формируем ответ
                    answer = data.get("answer", "Нет ответа")
                    sql_query = data.get("sql_query", "")
                    success = data.get("success", False)
                    
                    response_message = f"🤖 **Ответ:**\n{answer}\n\n"
                    
                    if sql_query:
                        response_message += f"📊 **SQL запрос:**\n```sql\n{sql_query}\n```\n\n"
                    
                    if success:
                        response_message += "✅ Запрос выполнен успешно"
                    else:
                        response_message += "❌ Ошибка выполнения запроса"
                    
                    await update.message.reply_text(response_message, parse_mode='Markdown')
                else:
                    await update.message.reply_text("❌ Ошибка обработки запроса в backend")
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        await update.message.reply_text(
            "❌ Ошибка подключения к backend\n\n"
            "Проверьте, что backend запущен на http://localhost:8000"
        )

async def error_handler(update: Update, context) -> None:
    """Обработчик ошибок"""
    logger.error(f"Ошибка при обработке обновления: {context.error}")

def main():
    """Основная функция"""
    print("🤖 Запуск CloverdashBot с Backend интеграцией...")
    print(f"📡 Токен: {TELEGRAM_TOKEN[:10]}...")
    print(f"🔗 Backend URL: {BACKEND_URL}")
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tables", tables_command))
    application.add_handler(CommandHandler("demo", demo_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    print("✅ Бот запущен! Нажмите Ctrl+C для остановки")
    print("🔗 Backend должен быть запущен на http://localhost:8000")
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
