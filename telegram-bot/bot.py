import logging
import os
from dotenv import load_dotenv
import aiohttp
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from translations import get_translation

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


class CloverdashBot:
    def __init__(self):
        self.session = None
        self.user_tokens = {}  # Кэш токенов пользователей
        self.user_settings = {}  # Кэш настроек пользователей

    async def get_or_create_user_token(self, user_id: str, user_data: dict) -> str:
        """Получает или создает токен для пользователя"""
        if user_id in self.user_tokens:
            return self.user_tokens[user_id]

        try:
            # Аутентификация через Telegram
            auth_payload = {
                "telegram_id": user_id,
                "telegram_username": user_data.get("username"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(f"{BACKEND_URL}/auth/telegram", json=auth_payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        token = result["access_token"]
                        self.user_tokens[user_id] = token
                        logger.info(f"User {user_id} authenticated successfully")
                        return token
                    else:
                        error_text = await response.text()
                        logger.error(f"Authentication failed for user {user_id}: {error_text}")
                        raise Exception(f"Authentication failed: {response.status}")

        except Exception as e:
            logger.error(f"Error authenticating user {user_id}: {e}")
            raise

    async def get_user_settings(self, user_id: str, token: str) -> dict:
        """Получает настройки пользователя"""
        if user_id in self.user_settings:
            return self.user_settings[user_id]

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.get(f"{BACKEND_URL}/settings", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.user_settings[user_id] = data
                    return data
        return {}

    async def update_user_settings_backend(self, user_id: str, token: str, data: dict) -> dict:
        """Обновляет настройки пользователя"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.patch(f"{BACKEND_URL}/settings", json=data, headers=headers) as resp:
                if resp.status == 200:
                    updated = await resp.json()
                    self.user_settings[user_id] = updated
                    return updated
        return {}

    def _clean_markdown(self, text: str) -> str:
        """Remove Markdown formatting from text for plain text display"""
        import re

        # Remove code blocks first (multiline)
        text = re.sub(r"```[\w]*\n?(.*?)\n?```", r"\1", text, flags=re.DOTALL)

        # Remove inline code
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # Remove bold formatting
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)

        # Remove italic formatting (both * and _)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        text = re.sub(r"_([^_]+)_", r"\1", text)

        # Remove strikethrough
        text = re.sub(r"~~([^~]+)~~", r"\1", text)

        # Remove headers
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

        # Remove links but keep the text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # Remove escaped characters
        text = text.replace("\\*", "*")
        text = text.replace("\\_", "_")
        text = text.replace("\\`", "`")
        text = text.replace("\\#", "#")
        text = text.replace("\\[", "[")
        text = text.replace("\\]", "]")
        text = text.replace("\\(", "(")
        text = text.replace("\\)", ")")

        # Clean up extra whitespace
        text = re.sub(r"\n\s*\n", "\n\n", text)  # Multiple newlines to double newlines
        text = text.strip()

        return text

    def _escape_markdown(self, text: str) -> str:
        """Escape special Markdown characters for safe display"""
        if not text:
            return ""

        # Convert to string if not already
        text = str(text)

        # Escape only the most problematic Markdown characters
        # These are the ones that most commonly cause parsing errors
        text = text.replace("_", "\\_")
        text = text.replace("*", "\\*")
        text = text.replace("`", "\\`")
        text = text.replace("[", "\\[")
        text = text.replace("]", "\\]")

        return text

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /start command"""
        user = update.effective_user
        user_id = str(user.id)
        user_data = {"username": user.username, "first_name": user.first_name, "last_name": user.last_name}
        token = await self.get_or_create_user_token(user_id, user_data)
        settings = await self.get_user_settings(user_id, token)
        lang = settings.get("preferred_language", "en")
        welcome_message = get_translation(lang, "start").format(name=user.first_name or "")
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /help command"""
        user = update.effective_user
        user_id = str(user.id)
        user_data = {"username": user.username, "first_name": user.first_name, "last_name": user.last_name}
        token = await self.get_or_create_user_token(user_id, user_data)
        settings = await self.get_user_settings(user_id, token)
        lang = settings.get("preferred_language", "en")
        help_message = get_translation(lang, "help") + "\n\n⚠️ Important: I only work with SELECT queries for data security."
        await update.message.reply_text(help_message)

    async def tables_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /tables command to show available tables"""
        try:
            user = update.effective_user
            user_id = str(user.id)

            logger.info(f"Tables list requested by user {user_id}")

            # Send processing message
            processing_msg = await update.message.reply_text("🔍 Getting list of available tables...")

            user_data = {"username": user.username, "first_name": user.first_name, "last_name": user.last_name}

            # Get authentication token
            token = await self.get_or_create_user_token(user_id, user_data)

            # Make API request to get available tables
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {token}"}

                async with session.get(f"{BACKEND_URL}/database/tables", headers=headers) as response:

                    if response.status == 200:
                        result = await response.json()

                        if result.get("success") and result.get("tables"):
                            tables = result["tables"]
                            database_name = result.get("database_name", "unknown")

                            # Format tables list response
                            reply_message = f"📊 *Available tables in {database_name}*\n\n"
                            reply_message += f"🔢 Total: {len(tables)} objects\n\n"

                            # Group by schema
                            schemas = {}
                            for table in tables:
                                schema = table["schema_name"]
                                if schema not in schemas:
                                    schemas[schema] = {"tables": [], "views": []}

                                if table["object_type"] == "view":
                                    schemas[schema]["views"].append(table)
                                else:
                                    schemas[schema]["tables"].append(table)

                            # Show each schema
                            for schema_name, objects in schemas.items():
                                reply_message += f"🗂️ *Schema: {schema_name}*\n"

                                # Show tables
                                if objects["tables"]:
                                    reply_message += f"📋 Tables ({len(objects['tables'])}):\n"
                                    for table in objects["tables"]:
                                        safe_name = self._escape_markdown(table["full_name"])
                                        reply_message += f"   • `{safe_name}`\n"

                                # Show views
                                if objects["views"]:
                                    reply_message += f"👁️ Views ({len(objects['views'])}):\n"
                                    for view in objects["views"]:
                                        safe_name = self._escape_markdown(view["full_name"])
                                        reply_message += f"   • `{safe_name}`\n"

                                reply_message += "\n"

                            reply_message += "💡 *Usage:*\n"
                            reply_message += "• `/sample <table_name>` - show sample data\n"
                            reply_message += "• Ask questions in natural language!"

                        else:
                            reply_message = "📊 No tables found in the database"

                    elif response.status == 401:
                        # Token expired
                        self.user_tokens.pop(user_id, None)
                        reply_message = "🔄 Authentication expired, please try again."

                    else:
                        error_text = await response.text()
                        logger.error(f"Tables API error: {response.status} - {error_text}")
                        reply_message = "❌ Error getting tables list. Please try again."

            # Send result
            try:
                await update.message.reply_text(reply_message, parse_mode="Markdown")
            except Exception as markdown_error:
                logger.error(f"Markdown parsing error in tables: {markdown_error}")
                # Send as plain text if markdown fails
                clean_message = self._clean_markdown(reply_message)
                await update.message.reply_text(clean_message)

        except Exception as e:
            logger.error(f"Error in tables_command: {e}")
            await update.message.reply_text("❌ An error occurred getting tables list. Please try again.")

    async def sample_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /sample command to show sample data from table"""
        try:
            user = update.effective_user
            user_id = str(user.id)

            # Get table name from command arguments
            if not context.args:
                await update.message.reply_text(
                    "❌ Please specify a table name!\n\n" "Usage: /sample <table_name>\n" "Example: /sample bills_view"
                )
                return

            table_name = " ".join(context.args)  # Handle table names with spaces/dots

            logger.info(f"Sample command requested by user {user_id} for table: {table_name}")

            # Send processing message
            processing_msg = await update.message.reply_text(f"🔍 Getting sample data from `{table_name}`...")

            user_data = {"username": user.username, "first_name": user.first_name, "last_name": user.last_name}

            # Get authentication token
            token = await self.get_or_create_user_token(user_id, user_data)

            # Make API request to get sample data
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {token}"}

                # Use the table sample endpoint from backend
                async with session.get(
                    f"{BACKEND_URL}/database/table/{table_name}/sample?limit=3", headers=headers
                ) as response:

                    if response.status == 200:
                        result = await response.json()

                        if result.get("success") and result.get("data"):
                            data = result["data"]

                            # Format sample data response
                            reply_message = f"📊 *Sample data from `{table_name}`*\n\n"
                            reply_message += f"🔢 Records shown: {len(data)}/3\n\n"

                            # Show each record
                            for i, row in enumerate(data):
                                reply_message += f"🔹 *Record {i+1}:*\n"
                                for key, value in row.items():
                                    # Escape special Markdown characters
                                    safe_key = self._escape_markdown(str(key))
                                    safe_value = self._escape_markdown(str(value) if value is not None else "NULL")
                                    reply_message += f"   • {safe_key}: `{safe_value}`\n"
                                reply_message += "\n"

                        elif result.get("success") and not result.get("data"):
                            reply_message = f"📊 Table `{table_name}` is empty (no records found)"

                        else:
                            error_msg = result.get("message", "Unknown error")
                            safe_error = self._escape_markdown(error_msg)
                            reply_message = f"❌ *Error:*\n{safe_error}"

                    elif response.status == 404:
                        reply_message = f"❌ Table `{table_name}` not found or not accessible"

                    elif response.status == 401:
                        # Token expired
                        self.user_tokens.pop(user_id, None)
                        reply_message = "🔄 Authentication expired, please try again."

                    else:
                        error_text = await response.text()
                        logger.error(f"Sample API error: {response.status} - {error_text}")
                        reply_message = "❌ Error getting sample data. Please try again."

            # Send result
            try:
                await update.message.reply_text(reply_message, parse_mode="Markdown")
            except Exception as markdown_error:
                logger.error(f"Markdown parsing error in sample: {markdown_error}")
                # Send as plain text if markdown fails
                clean_message = self._clean_markdown(reply_message)
                await update.message.reply_text(clean_message)

        except Exception as e:
            logger.error(f"Error in sample_command: {e}")
            await update.message.reply_text("❌ An error occurred getting sample data. Please try again.")

    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Изменение пользовательских настроек"""
        user = update.effective_user
        user_id = str(user.id)
        user_data = {"username": user.username, "first_name": user.first_name, "last_name": user.last_name}
        token = await self.get_or_create_user_token(user_id, user_data)

        if not context.args:
            settings = await self.get_user_settings(user_id, token)
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
                update_data["preferred_language"] = value
            elif option == "show_explanation":
                update_data["show_explanation"] = value in ("on", "true", "1", "yes")
            elif option == "show_sql":
                update_data["show_sql"] = value in ("on", "true", "1", "yes")
            else:
                await update.message.reply_text("Unknown setting. Use lang, show_explanation or show_sql")
                return

            settings = await self.update_user_settings_backend(user_id, token, update_data)
            lang = settings.get("preferred_language", "en")
            await update.message.reply_text(get_translation(lang, "settings_saved"))
        else:
            await update.message.reply_text("Usage: /settings <lang|show_explanation|show_sql> <value>")

    async def handle_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for text messages (user questions)"""
        try:
            user_question = update.message.text
            user = update.effective_user
            user_id = str(user.id)

            user_data = {"username": user.username, "first_name": user.first_name, "last_name": user.last_name}

            logger.info(f"=== STARTING QUERY PROCESSING ===")
            logger.info(f"User ID: {user_id}")
            logger.info(f"Question: {user_question}")
            logger.info(f"Message ID: {update.message.message_id}")

            # Send notification that the request is being processed
            logger.info("Sending processing message...")
            processing_msg = await update.message.reply_text("🔍 Processing your request...")
            logger.info(f"Processing message sent with ID: {processing_msg.message_id}")

        except Exception as e:
            logger.error(f"Error in handle_query setup: {e}")
            raise e

        try:
            logger.info("Getting user authentication token...")
            # Получаем токен аутентификации для пользователя
            token = await self.get_or_create_user_token(user_id, user_data)
            settings = await self.get_user_settings(user_id, token)

            logger.info("Starting backend API request...")
            # Send request to backend API
            async with aiohttp.ClientSession() as session:
                payload = {"query": user_question, "user_id": user_id}
                headers = {"Authorization": f"Bearer {token}"}
                logger.info(f"Payload: {payload}")

                async with session.post(f"{BACKEND_URL}/database/query", json=payload, headers=headers) as response:
                    logger.info(f"Backend response status: {response.status}")

                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Backend response: {result}")

                        if result.get("success"):
                            # Format response for successful request
                            reply_message = "✅ *Result:*\n"

                            # Add data if available
                            if result.get("data") and len(result["data"]) > 0:
                                data_count = len(result["data"])
                                reply_message += f"📊 Records found: {data_count}\n\n"

                                # Show first few records
                                for i, row in enumerate(result["data"][:3]):  # First 3 records
                                    reply_message += f"🔹 Record {i+1}:\n"
                                    for key, value in row.items():
                                        # Escape special Markdown characters in values
                                        safe_key = self._escape_markdown(key)
                                        safe_value = self._escape_markdown(value)
                                        reply_message += f"   • {safe_key}: {safe_value}\n"
                                    reply_message += "\n"

                                if data_count > 3:
                                    reply_message += f"... and {data_count - 3} more records\n\n"

                            # Add explanation if available and allowed
                            if settings.get("show_explanation", True) and result.get("explanation"):
                                safe_explanation = self._escape_markdown(result["explanation"])
                                reply_message += f"💬 *Explanation:*\n{safe_explanation}\n\n"

                            # Add SQL query if allowed
                            if settings.get("show_sql", False) and result.get("sql_query"):
                                # SQL code blocks don't need escaping inside ```
                                sql_query = result["sql_query"]
                                reply_message += f"📝 *SQL Query:*\n```sql\n{sql_query}\n```\n\n"

                            # Add execution time
                            if result.get("execution_time"):
                                reply_message += f"⏱️ Execution time: {result['execution_time']:.2f}s"

                        else:
                            # Handle API error - escape error message
                            error_message = result.get("message", "Unknown error")
                            safe_error = self._escape_markdown(error_message)
                            reply_message = f"❌ *Error:*\n{safe_error}"

                        # Send result as new message
                        logger.info("Sending result message...")
                        try:
                            result_msg = await update.message.reply_text(reply_message, parse_mode="Markdown")
                            logger.info(f"Result message sent with ID: {result_msg.message_id}")
                        except Exception as markdown_error:
                            logger.error(f"Markdown parsing error: {markdown_error}")
                            # Clean message from Markdown formatting and send as plain text
                            clean_message = self._clean_markdown(reply_message)
                            result_msg = await update.message.reply_text(clean_message)
                            logger.info(f"Result message sent without markdown, ID: {result_msg.message_id}")

                    elif response.status == 401:
                        # Token expired or invalid, remove from cache and retry
                        logger.info(f"Token expired for user {user_id}, removing from cache")
                        self.user_tokens.pop(user_id, None)
                        error_msg = await update.message.reply_text("🔄 Authentication expired, please try again.")
                        logger.info(f"Auth error message sent with ID: {error_msg.message_id}")

                    else:
                        error_text = await response.text()
                        logger.error(f"Backend API error: {response.status} - {error_text}")
                        logger.info("Sending error message...")
                        error_msg = await update.message.reply_text("❌ Error processing request. Please try again.")
                        logger.info(f"Error message sent with ID: {error_msg.message_id}")

        except Exception as e:
            logger.error(f"Exception in query processing: {str(e)}")
            logger.info("Sending exception message...")
            try:
                exception_msg = await update.message.reply_text("❌ An error occurred. Please try again later.")
                logger.info(f"Exception message sent with ID: {exception_msg.message_id}")
            except Exception as send_error:
                logger.error(f"Error sending exception message: {send_error}")

        logger.info("=== QUERY PROCESSING COMPLETED ===")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Error handler"""
        logger.error(f"=== ERROR HANDLER TRIGGERED ===")
        logger.error(f"Error type: {type(context.error)}")
        logger.error(f"Error message: {context.error}")
        logger.error(f"Update that caused error: {update}")

        # Log stack trace if available
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")

        if update and update.message:
            try:
                logger.info("Sending error handler message...")
                error_handler_msg = await update.message.reply_text("❌ An error occurred. Please try again.")
                logger.info(f"Error handler message sent with ID: {error_handler_msg.message_id}")
            except Exception as e:
                logger.error(f"Error sending error message in error_handler: {e}")

        logger.error(f"=== ERROR HANDLER COMPLETED ===")


def main():
    """Start the bot"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN not found in environment variables")
        print("❌ Error: TELEGRAM_TOKEN not found in environment variables")
        print("📝 Add it to the .env file:")
        print("TELEGRAM_TOKEN=your_bot_token_here")
        return

    print(f"🚀 Starting CloverdashBot...")
    print(f"🔗 Backend URL: {BACKEND_URL}")

    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    bot = CloverdashBot()

    # Add handlers
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("tables", bot.tables_command))
    application.add_handler(CommandHandler("sample", bot.sample_command))
    application.add_handler(CommandHandler("settings", bot.settings_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_query))
    application.add_error_handler(bot.error_handler)

    # Start the bot
    logger.info("Starting CloverdashBot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
