import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Dict, Any

# Новые импорты
from models import UserData, UserSettings, Language
from services import UserService, DatabaseService, KeyboardService, MessageService
from exceptions import AuthenticationError, ValidationError, BotException
from config import CallbackData, Emoji

# Старые импорты (пока оставляем для совместимости)
from api_client import APIClient
from formatters import MessageFormatter
from translations import get_translation

logger = logging.getLogger(__name__)


class CommandHandlers:
    """Хендлеры команд Telegram бота"""

    def __init__(self, api_client: APIClient, query_handler=None, user_service=None, database_service=None):
        self.api_client = api_client
        self.query_handler = query_handler

        # Новые сервисы
        self.user_service = user_service or UserService(api_client)
        self.database_service = database_service or DatabaseService(api_client)
        self.keyboard_service = KeyboardService()
        self.message_service = MessageService()

    def _get_user_data(self, update: Update) -> UserData:
        """Получение данных пользователя из update"""
        user = update.effective_user
        return UserData.from_telegram_user(user)

    def _get_user_data_dict(self, update: Update) -> Dict[str, Any]:
        """Получение данных пользователя как словарь (для совместимости)"""
        user = update.effective_user
        return {
            "user_id": str(user.id),
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start с новой архитектурой"""
        user_data = self._get_user_data(update)

        try:
            # Аутентификация и получение настроек через UserService
            token, settings = await self.user_service.authenticate_and_get_settings(user_data)

            # Создаем приветственное сообщение
            welcome_message = self.message_service.get_welcome_message(
                settings.preferred_language, user_data.first_name
            )

            # Создаем клавиатуру с примерами через KeyboardService
            keyboard = self.keyboard_service.create_examples_keyboard(settings.preferred_language)

            await update.message.reply_text(welcome_message, reply_markup=keyboard)

        except AuthenticationError as e:
            logger.error(f"Authentication error in start_command: {e}")
            await update.message.reply_text(f"{Emoji.ERROR} Authentication failed. Please try again.")
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await update.message.reply_text(f"{Emoji.ERROR} Error starting bot. Please try again.")

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

        try:
            # Получаем настройки пользователя
            user_settings = await self.user_service.authenticate_and_get_settings(user_data)

            if not context.args:
                # Показываем текущие настройки
                msg = get_translation(user_settings.preferred_language, "current_settings").format(
                    lang=user_settings.preferred_language,
                    explanation=user_settings.show_explanation,
                    sql=user_settings.show_sql,
                )
                await update.message.reply_text(msg)
                return

            if len(context.args) >= 2:
                option = context.args[0].lower()
                value = context.args[1].lower()

                # Валидация и обновление настроек через UserService
                try:
                    updated_settings = await self.user_service.update_settings(user_data, option, value)

                    # Форматируем сообщение об успехе
                    if option == "lang":
                        flag = Emoji.FLAG_US if value == "en" else Emoji.FLAG_RU
                        lang_name = "English" if value == "en" else "Русский"
                        success_msg = get_translation(updated_settings.preferred_language, "settings_saved")
                        success_msg += f"\n{Emoji.GLOBE} Language: {lang_name} {flag}"
                        await update.message.reply_text(success_msg)
                    else:
                        await update.message.reply_text(
                            get_translation(updated_settings.preferred_language, "settings_saved")
                        )

                except ValueError as e:
                    # Обрабатываем ошибки валидации
                    error_msg = get_translation(user_settings.preferred_language, str(e))
                    await update.message.reply_text(error_msg)

            else:
                # Показываем help сообщение
                await update.message.reply_text(get_translation(user_settings.preferred_language, "settings_usage"))

        except AuthenticationError as e:
            logger.error(f"Authentication error in settings_command: {e}")
            await update.message.reply_text(f"{Emoji.CROSS} Authentication failed. Please try /start")
        except Exception as e:
            logger.error(f"Error in settings_command: {e}")
            await update.message.reply_text(f"{Emoji.CROSS} Error updating settings. Please try again.")

    async def quick_lang_en_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Быстрое переключение на английский язык"""
        user_data = self._get_user_data(update)

        try:
            await self.user_service.update_language(user_data, Language.ENGLISH)
            await update.message.reply_text(
                f"Settings updated {Emoji.CHECK}\n{Emoji.GLOBE} Language: English {Emoji.FLAG_US}"
            )
        except AuthenticationError as e:
            logger.error(f"Authentication error in quick_lang_en_command: {e}")
            await update.message.reply_text(f"{Emoji.CROSS} Authentication failed. Please try /start")
        except Exception as e:
            logger.error(f"Error in quick_lang_en_command: {e}")
            await update.message.reply_text(f"{Emoji.CROSS} Error changing language. Please try again.")

    async def quick_lang_ru_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Быстрое переключение на русский язык"""
        user_data = self._get_user_data(update)

        try:
            await self.user_service.update_language(user_data, Language.RUSSIAN)
            await update.message.reply_text(
                f"Настройки обновлены {Emoji.CHECK}\n{Emoji.GLOBE} Язык: Русский {Emoji.FLAG_RU}"
            )
        except AuthenticationError as e:
            logger.error(f"Authentication error in quick_lang_ru_command: {e}")
            await update.message.reply_text(f"{Emoji.CROSS} Authentication failed. Please try /start")
        except Exception as e:
            logger.error(f"Error in quick_lang_ru_command: {e}")
            await update.message.reply_text(f"{Emoji.CROSS} Ошибка при смене языка. Попробуйте еще раз.")

    async def handle_example_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик callback'ов от кнопок с примерами"""
        logger.info(f"=== CALLBACK RECEIVED ===")
        query = update.callback_query
        logger.info(f"Callback data: {query.data}")
        logger.info(f"User: {query.from_user.id}")

        await query.answer()  # Подтверждаем получение callback

        if query.data.startswith("ex:"):
            # Маппинг коротких идентификаторов на полные запросы
            examples = {
                "time_ru": "Покажи текущее время",
                "sales_ru": "Каков объем продаж в январе?",
                "bestseller_ru": "Какой товар продается лучше всего?",
                "time_en": "Show current time",
                "sales_en": "What is the sales volume in January?",
                "bestseller_en": "What is the best-selling product?",
            }

            # Извлекаем идентификатор из callback_data
            example_id = query.data[3:]  # Убираем "ex:" префикс
            example_query = examples.get(example_id, "Unknown example")

            logger.info(f"Example button clicked by user {query.from_user.id}: {example_id} -> {example_query}")

            # Отправляем сообщение пользователю что выбран пример
            await query.message.reply_text(f"🎯 Вы выбрали: {example_query}\n\n💡 Сейчас выполню этот запрос...")

            # Проверяем что query_handler доступен
            if self.query_handler is None:
                logger.error("QueryHandler не доступен")
                await query.message.reply_text("❌ Ошибка: обработчик запросов недоступен")
                return

                # Вместо создания fake Update, выполняем запрос напрямую через API
            # Для callback query нужно получить данные пользователя из query.from_user
            user_data = {
                "user_id": str(query.from_user.id),
                "username": query.from_user.username,
                "first_name": query.from_user.first_name,
                "last_name": query.from_user.last_name,
            }
            user_id = user_data["user_id"]

            try:
                # Отправляем уведомление о том, что запрос обрабатывается
                processing_msg = await query.message.reply_text("🔍 Обрабатываю ваш запрос...")

                # Получаем токен аутентификации
                token = await self.api_client.authenticate_user(user_id, user_data)

                # Получаем настройки пользователя
                settings = await self.api_client.get_user_settings(user_id, token)

                # Выполняем запрос к API
                result = await self.api_client.execute_query(example_query, user_id, token)

                if result.get("success"):
                    # Форматируем ответ для успешного запроса
                    from formatters import MessageFormatter

                    reply_message = MessageFormatter.format_query_result(result, settings)
                else:
                    # Обрабатываем ошибку API
                    error_message = result.get("message", "Unknown error")
                    from formatters import MessageFormatter

                    safe_error = MessageFormatter.escape_markdown(error_message)
                    reply_message = f"❌ *Ошибка:*\n{safe_error}"

                # Отправляем результат
                try:
                    await query.message.reply_text(reply_message, parse_mode="Markdown")
                except Exception as markdown_error:
                    logger.error(f"Markdown parsing error: {markdown_error}")
                    from formatters import MessageFormatter

                    clean_message = MessageFormatter.clean_markdown(reply_message)
                    await query.message.reply_text(clean_message)

            except Exception as e:
                logger.error(f"Error processing example query: {e}")
                await query.message.reply_text("❌ Произошла ошибка при обработке запроса. Попробуйте еще раз.")
