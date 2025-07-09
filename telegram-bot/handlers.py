import logging
from telegram import Update
from telegram.ext import ContextTypes
from typing import Dict, Any

from api_client import APIClient
from formatters import MessageFormatter
from translations import get_translation

logger = logging.getLogger(__name__)


class CommandHandlers:
    """Хендлеры команд Telegram бота"""

    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    def _get_user_data(self, update: Update) -> Dict[str, Any]:
        """Получение данных пользователя из update"""
        user = update.effective_user
        return {
            "user_id": str(user.id),
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        user_data = self._get_user_data(update)
        user_id = user_data["user_id"]

        try:
            token = await self.api_client.authenticate_user(user_id, user_data)
            settings = await self.api_client.get_user_settings(user_id, token)
            lang = settings.get("preferred_language", "en")
            welcome_message = get_translation(lang, "start").format(name=user_data["first_name"] or "")
            await update.message.reply_text(welcome_message)
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await update.message.reply_text("❌ Error starting bot. Please try again.")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help"""
        user_data = self._get_user_data(update)
        user_id = user_data["user_id"]

        try:
            token = await self.api_client.authenticate_user(user_id, user_data)
            settings = await self.api_client.get_user_settings(user_id, token)
            lang = settings.get("preferred_language", "en")
            help_message = (
                get_translation(lang, "help") + "\n\n⚠️ Important: I only work with SELECT queries for data security."
            )
            await update.message.reply_text(help_message)
        except Exception as e:
            logger.error(f"Error in help_command: {e}")
            await update.message.reply_text("❌ Error getting help. Please try again.")

    async def tables_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /tables для показа доступных таблиц"""
        user_data = self._get_user_data(update)
        user_id = user_data["user_id"]

        logger.info(f"Tables list requested by user {user_id}")

        try:
            # Отправляем сообщение о обработке
            processing_msg = await update.message.reply_text("🔍 Getting list of available tables...")

            # Получаем токен аутентификации
            token = await self.api_client.authenticate_user(user_id, user_data)

            # Получаем список таблиц
            result = await self.api_client.get_tables(token)

            if result.get("success") and result.get("tables"):
                tables = result["tables"]
                database_name = result.get("database_name", "unknown")

                # Форматируем ответ
                reply_message = MessageFormatter.format_tables_list(tables, database_name)

            else:
                reply_message = "📊 No tables found in the database"

            # Отправляем результат
            try:
                await update.message.reply_text(reply_message, parse_mode="Markdown")
            except Exception as markdown_error:
                logger.error(f"Markdown parsing error in tables: {markdown_error}")
                # Отправляем как обычный текст если markdown не работает
                clean_message = MessageFormatter.clean_markdown(reply_message)
                await update.message.reply_text(clean_message)

        except Exception as e:
            logger.error(f"Error in tables_command: {e}")
            await update.message.reply_text("❌ An error occurred getting tables list. Please try again.")

    async def sample_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /sample для показа образца данных из таблицы"""
        user_data = self._get_user_data(update)
        user_id = user_data["user_id"]

        # Получаем имя таблицы из аргументов команды
        if not context.args:
            await update.message.reply_text(
                "❌ Please specify a table name!\n\n" "Usage: /sample <table_name>\n" "Example: /sample bills_view"
            )
            return

        table_name = " ".join(context.args)  # Обрабатываем имена таблиц с пробелами/точками

        logger.info(f"Sample command requested by user {user_id} for table: {table_name}")

        try:
            # Отправляем сообщение о обработке
            processing_msg = await update.message.reply_text(f"🔍 Getting sample data from `{table_name}`...")

            # Получаем токен аутентификации
            token = await self.api_client.authenticate_user(user_id, user_data)

            # Получаем образец данных
            result = await self.api_client.get_table_sample(table_name, token)

            if result.get("success") and result.get("data"):
                data = result["data"]
                reply_message = MessageFormatter.format_sample_data(data, table_name)

            elif result.get("success") and not result.get("data"):
                reply_message = f"📊 Table `{table_name}` is empty (no records found)"

            else:
                error_msg = result.get("message", "Unknown error")
                safe_error = MessageFormatter.escape_markdown(error_msg)
                reply_message = f"❌ *Error:*\n{safe_error}"

            # Отправляем результат
            try:
                await update.message.reply_text(reply_message, parse_mode="Markdown")
            except Exception as markdown_error:
                logger.error(f"Markdown parsing error in sample: {markdown_error}")
                # Отправляем как обычный текст если markdown не работает
                clean_message = MessageFormatter.clean_markdown(reply_message)
                await update.message.reply_text(clean_message)

        except Exception as e:
            logger.error(f"Error in sample_command: {e}")
            await update.message.reply_text("❌ An error occurred getting sample data. Please try again.")

    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /settings для изменения пользовательских настроек"""
        user_data = self._get_user_data(update)
        user_id = user_data["user_id"]

        try:
            token = await self.api_client.authenticate_user(user_id, user_data)

            if not context.args:
                # Показываем текущие настройки
                settings = await self.api_client.get_user_settings(user_id, token)
                lang = settings.get("preferred_language", "en")
                msg = get_translation(lang, "current_settings").format(
                    lang=settings.get("preferred_language", "en"),
                    explanation=settings.get("show_explanation", True),
                    sql=settings.get("show_sql", False),
                )
                await update.message.reply_text(msg)
                return

            if len(context.args) >= 2:
                option = context.args[0].lower()
                value = context.args[1].lower()
                update_data = {}

                if option == "lang":
                    # Валидация языка
                    if value not in ("en", "ru"):
                        # Получаем текущий язык для показа ошибки
                        settings = await self.api_client.get_user_settings(user_id, token)
                        current_lang = settings.get("preferred_language", "en")
                        await update.message.reply_text(get_translation(current_lang, "invalid_language"))
                        return
                    update_data["preferred_language"] = value
                elif option == "show_explanation":
                    update_data["show_explanation"] = value in ("on", "true", "1", "yes")
                elif option == "show_sql":
                    update_data["show_sql"] = value in ("on", "true", "1", "yes")
                else:
                    # Получаем текущий язык для показа ошибки
                    settings = await self.api_client.get_user_settings(user_id, token)
                    current_lang = settings.get("preferred_language", "en")
                    await update.message.reply_text(get_translation(current_lang, "unknown_setting"))
                    return

                settings = await self.api_client.update_user_settings(user_id, token, update_data)
                # Очищаем кэш настроек чтобы получить свежие данные
                self.api_client.clear_settings_cache(user_id)
                lang = settings.get("preferred_language", "en")

                # Добавляем флаги для изменения языка
                if option == "lang":
                    flag = "🇺🇸" if value == "en" else "🇷🇺"
                    lang_name = "English" if value == "en" else "Русский"
                    success_msg = get_translation(lang, "settings_saved") + f"\n🌐 Language: {lang_name} {flag}"
                    await update.message.reply_text(success_msg)
                else:
                    await update.message.reply_text(get_translation(lang, "settings_saved"))
            else:
                # Получаем текущий язык для показа help сообщения
                settings = await self.api_client.get_user_settings(user_id, token)
                current_lang = settings.get("preferred_language", "en")
                await update.message.reply_text(get_translation(current_lang, "settings_usage"))

        except Exception as e:
            logger.error(f"Error in settings_command: {e}")
            await update.message.reply_text("❌ Error updating settings. Please try again.")

    async def quick_lang_en_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Быстрое переключение на английский язык"""
        user_data = self._get_user_data(update)
        user_id = user_data["user_id"]

        try:
            token = await self.api_client.authenticate_user(user_id, user_data)
            update_data = {"preferred_language": "en"}
            settings = await self.api_client.update_user_settings(user_id, token, update_data)
            self.api_client.clear_settings_cache(user_id)

            await update.message.reply_text("Settings updated ✅\n🌐 Language: English 🇺🇸")
        except Exception as e:
            logger.error(f"Error in quick_lang_en_command: {e}")
            await update.message.reply_text("❌ Error changing language. Please try again.")

    async def quick_lang_ru_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Быстрое переключение на русский язык"""
        user_data = self._get_user_data(update)
        user_id = user_data["user_id"]

        try:
            token = await self.api_client.authenticate_user(user_id, user_data)
            update_data = {"preferred_language": "ru"}
            settings = await self.api_client.update_user_settings(user_id, token, update_data)
            self.api_client.clear_settings_cache(user_id)

            await update.message.reply_text("Настройки обновлены ✅\n🌐 Язык: Русский 🇷🇺")
        except Exception as e:
            logger.error(f"Error in quick_lang_ru_command: {e}")
            await update.message.reply_text("❌ Ошибка при смене языка. Попробуйте еще раз.")
