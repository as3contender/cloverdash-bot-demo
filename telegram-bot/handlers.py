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
            welcome_message = MessageService.create_welcome_message(user_data, settings.preferred_language)

            # Создаем клавиатуру с примерами через KeyboardService
            keyboard = KeyboardService.create_example_keyboard(settings.preferred_language)

            await update.message.reply_text(welcome_message, reply_markup=keyboard)

        except AuthenticationError as e:
            logger.error(f"Authentication error in start_command: {e}")
            await update.message.reply_text(f"{Emoji.CROSS} Authentication failed. Please try again.")
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await update.message.reply_text(f"{Emoji.CROSS} Error starting bot. Please try again.")

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
        logger.info(f"Tables list requested by user {user_data.user_id}")

        try:
            # Отправляем сообщение о обработке
            processing_msg = await update.message.reply_text(f"{Emoji.SEARCH} Getting list of available tables...")

            # Получаем токен и список таблиц через DatabaseService
            token, _ = await self.user_service.authenticate_and_get_settings(user_data)
            tables = await self.database_service.get_tables(user_data, token)

            if tables:
                # Форматируем ответ через MessageService
                reply_message = MessageFormatter.format_tables_list([table.__dict__ for table in tables], "database")
            else:
                reply_message = f"{Emoji.DATABASE} No tables found in the database"

            # Отправляем результат с обработкой markdown ошибок
            try:
                await update.message.reply_text(reply_message, parse_mode="Markdown")
            except Exception as markdown_error:
                logger.error(f"Markdown parsing error in tables: {markdown_error}")
                # Отправляем как обычный текст если markdown не работает
                clean_message = MessageFormatter.clean_markdown(reply_message)
                await update.message.reply_text(clean_message)

        except AuthenticationError as e:
            logger.error(f"Authentication error in tables_command: {e}")
            await update.message.reply_text(f"{Emoji.CROSS} Authentication failed. Please try /start")
        except Exception as e:
            logger.error(f"Error in tables_command: {e}")
            await update.message.reply_text(f"{Emoji.CROSS} An error occurred getting tables list. Please try again.")

    async def sample_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /sample для показа образца данных из таблицы"""
        user_data = self._get_user_data(update)

        # Получаем имя таблицы из аргументов команды
        if not context.args:
            await update.message.reply_text(
                f"{Emoji.CROSS} Please specify a table name!\n\n"
                "Usage: /sample <table_name>\n"
                "Example: /sample bills_view"
            )
            return

        table_name = " ".join(context.args)  # Обрабатываем имена таблиц с пробелами/точками

        try:
            # Валидация имени таблицы
            validated_table_name = ValidationService.validate_table_name(table_name)
            logger.info(f"Sample command requested by user {user_data.user_id} for table: {validated_table_name}")

            # Отправляем сообщение о обработке
            processing_msg = await update.message.reply_text(
                f"{Emoji.SEARCH} Getting sample data from `{validated_table_name}`..."
            )

            # Получаем токен и образец данных через DatabaseService
            token, _ = await self.user_service.authenticate_and_get_settings(user_data)
            query_result = await self.database_service.get_table_sample(user_data, token, validated_table_name)

            if query_result.success and query_result.data:
                reply_message = MessageFormatter.format_sample_data(query_result.data, validated_table_name)
            elif query_result.success and not query_result.data:
                reply_message = f"{Emoji.DATABASE} Table `{validated_table_name}` is empty (no records found)"
            else:
                safe_error = MessageFormatter.escape_markdown(query_result.message or "Unknown error")
                reply_message = f"{Emoji.CROSS} *Error:*\n{safe_error}"

            # Отправляем результат с обработкой markdown ошибок
            try:
                await update.message.reply_text(reply_message, parse_mode="Markdown")
            except Exception as markdown_error:
                logger.error(f"Markdown parsing error in sample: {markdown_error}")
                # Отправляем как обычный текст если markdown не работает
                clean_message = MessageFormatter.clean_markdown(reply_message)
                await update.message.reply_text(clean_message)

        except ValidationError as e:
            logger.error(f"Validation error in sample_command: {e}")
            await update.message.reply_text(f"{Emoji.CROSS} {str(e)}")
        except AuthenticationError as e:
            logger.error(f"Authentication error in sample_command: {e}")
            await update.message.reply_text(f"{Emoji.CROSS} Authentication failed. Please try /start")
        except Exception as e:
            logger.error(f"Error in sample_command: {e}")
            await update.message.reply_text(f"{Emoji.CROSS} An error occurred getting sample data. Please try again.")

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

        if query.data.startswith(CallbackData.EXAMPLE_PREFIX):
            try:
                # Получаем текст запроса через MessageService
                example_query = MessageService.get_example_query(query.data)
                if not example_query:
                    logger.warning(f"Unknown example ID: {query.data}")
                    await query.message.reply_text(f"{Emoji.CROSS} Unknown example selected")
                    return

                # Создаем UserData из callback query
                user_data = UserData(
                    user_id=str(query.from_user.id),
                    username=query.from_user.username,
                    first_name=query.from_user.first_name,
                    last_name=query.from_user.last_name,
                )

                logger.info(f"Example button clicked by user {user_data.user_id}: {example_query}")

                # Отправляем сообщение пользователю что выбран пример
                await query.message.reply_text(
                    f"{Emoji.TARGET} Вы выбрали: {example_query}\n\n{Emoji.LIGHTBULB} Сейчас выполню этот запрос..."
                )

                # Проверяем что query_handler доступен
                if self.query_handler is None:
                    logger.error("QueryHandler не доступен")
                    await query.message.reply_text(f"{Emoji.CROSS} Ошибка: обработчик запросов недоступен")
                    return

                # Отправляем уведомление о том, что запрос обрабатывается
                processing_msg = await query.message.reply_text(f"{Emoji.SEARCH} Обрабатываю ваш запрос...")

                # Получаем токен и настройки пользователя
                token, user_settings = await self.user_service.authenticate_and_get_settings(user_data)

                # Выполняем запрос через DatabaseService
                query_result = await self.database_service.execute_query(user_data, token, example_query)

                if query_result.success:
                    # Форматируем ответ для успешного запроса
                    from formatters import MessageFormatter

                    reply_message = MessageFormatter.format_query_result(query_result.__dict__, user_settings.__dict__)
                else:
                    # Обрабатываем ошибку API
                    from formatters import MessageFormatter

                    safe_error = MessageFormatter.escape_markdown(query_result.message or "Unknown error")
                    reply_message = f"{Emoji.CROSS} *Ошибка:*\n{safe_error}"

                # Отправляем результат с обработкой markdown ошибок
                try:
                    await query.message.reply_text(reply_message, parse_mode="Markdown")
                except Exception as markdown_error:
                    logger.error(f"Markdown parsing error: {markdown_error}")
                    from formatters import MessageFormatter

                    clean_message = MessageFormatter.clean_markdown(reply_message)
                    await query.message.reply_text(clean_message)

            except AuthenticationError as e:
                logger.error(f"Authentication error in handle_example_callback: {e}")
                await query.message.reply_text(f"{Emoji.CROSS} Authentication failed. Please try /start")
            except Exception as e:
                logger.error(f"Error processing example query: {e}")
                await query.message.reply_text(
                    f"{Emoji.CROSS} Произошла ошибка при обработке запроса. Попробуйте еще раз."
                )
