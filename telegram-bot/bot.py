import logging
import os
from dotenv import load_dotenv
import aiohttp
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


class CloverdashBot:
    def __init__(self):
        self.session = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        user = update.effective_user
        welcome_message = f"""
Привет, {user.first_name}! 👋

Я - CloverdashBot, твой помощник для работы с базой данных! 

Я могу:
• Отвечать на вопросы о данных в естественной форме
• Строить SQL запросы автоматически
• Предоставлять результаты в удобном формате

Просто задай мне вопрос о данных, и я найду ответ! 

Примеры:
• "Покажи текущее время"
• "Какой объем продаж в январе?"
• "Какой самый продаваемый товар?"
        """
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help"""
        help_message = """
🤖 Доступные команды:

/start - Начать работу с ботом
/help - Показать это сообщение

📊 Как пользоваться:
Просто напиши свой вопрос о данных на русском языке, и я найду ответ!

Примеры вопросов:
• "Покажи текущее время и дату"
• "Какой объем продаж в январе?"
• "Покажи список таблиц в базе данных"

⚠️ Важно: Я работаю только с SELECT запросами для безопасности данных.
        """
        await update.message.reply_text(help_message)

    async def handle_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик текстовых сообщений (вопросов пользователя)"""
        user_question = update.message.text
        user_id = str(update.effective_user.id)

        # Отправляем уведомление о том, что запрос обрабатывается
        processing_message = await update.message.reply_text("🔍 Обрабатываю ваш запрос...")

        try:
            # Отправляем запрос к backend API (исправлено: query вместо question)
            async with aiohttp.ClientSession() as session:
                payload = {"query": user_question, "user_id": user_id}

                async with session.post(f"{BACKEND_URL}/query", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()

                        if result.get("success"):
                            # Формируем ответ для успешного запроса
                            reply_message = f"✅ *Результат:*\n"

                            # Добавляем данные если они есть
                            if result.get("data") and len(result["data"]) > 0:
                                data_count = len(result["data"])
                                reply_message += f"📊 Найдено записей: {data_count}\n\n"

                                # Показываем первые несколько записей
                                for i, row in enumerate(result["data"][:3]):  # Первые 3 записи
                                    reply_message += f"🔹 Запись {i+1}:\n"
                                    for key, value in row.items():
                                        reply_message += f"   • {key}: {value}\n"
                                    reply_message += "\n"

                                if data_count > 3:
                                    reply_message += f"... и ещё {data_count - 3} записей\n\n"

                            # Добавляем объяснение если есть
                            if result.get("explanation"):
                                reply_message += f"💬 *Объяснение:*\n{result['explanation']}\n\n"

                            # Добавляем SQL запрос
                            if result.get("sql_query"):
                                reply_message += f"📝 *SQL запрос:*\n```sql\n{result['sql_query']}\n```\n\n"

                            # Добавляем время выполнения
                            if result.get("execution_time"):
                                reply_message += f"⏱️ Время выполнения: {result['execution_time']:.2f}с"

                        else:
                            # Обработка ошибки от API
                            reply_message = f"❌ *Ошибка:*\n{result.get('message', 'Неизвестная ошибка')}"

                        # Удаляем сообщение о обработке и отправляем результат
                        await processing_message.delete()
                        await update.message.reply_text(reply_message, parse_mode="Markdown")

                    else:
                        error_text = await response.text()
                        await processing_message.edit_text("❌ Ошибка при обработке запроса. Попробуйте еще раз.")
                        logger.error(f"Backend API error: {response.status} - {error_text}")

        except Exception as e:
            await processing_message.edit_text("❌ Произошла ошибка. Попробуйте позже.")
            logger.error(f"Error processing query: {str(e)}")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик ошибок"""
        logger.error(f"Update {update} caused error {context.error}")

        if update and update.message:
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте еще раз.")


def main():
    """Запуск бота"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN not found in environment variables")
        print("❌ Ошибка: TELEGRAM_TOKEN не найден в переменных окружения")
        print("📝 Добавьте его в файл .env:")
        print("TELEGRAM_TOKEN=your_bot_token_here")
        return

    print(f"🚀 Запуск CloverdashBot...")
    print(f"🔗 Backend URL: {BACKEND_URL}")

    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    bot = CloverdashBot()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_query))
    application.add_error_handler(bot.error_handler)

    # Запускаем бота
    logger.info("Starting CloverdashBot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
