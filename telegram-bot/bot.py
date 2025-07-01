import logging
import os
from dotenv import load_dotenv
import aiohttp
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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

    def _clean_markdown(self, text: str) -> str:
        """Remove Markdown formatting from text for plain text display"""
        import re

        # Remove bold and italic formatting
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # Remove **bold**
        text = re.sub(r"\*(.*?)\*", r"\1", text)  # Remove *italic*
        text = re.sub(r"_(.*?)_", r"\1", text)  # Remove _italic_

        # Remove code blocks
        text = re.sub(r"```[\w]*\n(.*?)\n```", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"`(.*?)`", r"\1", text)  # Remove `inline code`

        # Remove escaped characters
        text = text.replace("\\*", "*")
        text = text.replace("\\_", "_")
        text = text.replace("\\`", "`")

        return text

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /start command"""
        user = update.effective_user
        welcome_message = f"""
Hello, {user.first_name}! 👋

I'm CloverdashBot, your database assistant!

I can:
• Answer questions about data in natural language
• Build SQL queries automatically
• Provide results in a convenient format

Just ask me a question about the data, and I'll find the answer!

Examples:
• "Show current time"
• "What is the sales volume in January?"
• "What is the best-selling product?"
        """
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /help command"""
        help_message = """
🤖 Available commands:

/start - Start working with the bot
/help - Show this message

📊 How to use:
Just write your question about the data in natural language, and I'll find the answer!

Example questions:
• "Show current time and date"
• "What is the sales volume in January?"
• "Show list of tables in the database"

⚠️ Important: I only work with SELECT queries for data security.
        """
        await update.message.reply_text(help_message)

    async def handle_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for text messages (user questions)"""
        try:
            user_question = update.message.text
            user_id = str(update.effective_user.id)

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
            logger.info("Starting backend API request...")
            # Send request to backend API
            async with aiohttp.ClientSession() as session:
                payload = {"query": user_question, "user_id": user_id}
                logger.info(f"Payload: {payload}")

                async with session.post(f"{BACKEND_URL}/query", json=payload) as response:
                    logger.info(f"Backend response status: {response.status}")

                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Backend response: {result}")

                        if result.get("success"):
                            # Format response for successful request
                            reply_message = f"✅ *Result:*\n"

                            # Add data if available
                            if result.get("data") and len(result["data"]) > 0:
                                data_count = len(result["data"])
                                reply_message += f"📊 Records found: {data_count}\n\n"

                                # Show first few records
                                for i, row in enumerate(result["data"][:3]):  # First 3 records
                                    reply_message += f"🔹 Record {i+1}:\n"
                                    for key, value in row.items():
                                        reply_message += f"   • {key}: {value}\n"
                                    reply_message += "\n"

                                if data_count > 3:
                                    reply_message += f"... and {data_count - 3} more records\n\n"

                            # Add explanation if available
                            if result.get("explanation"):
                                reply_message += f"💬 *Explanation:*\n{result['explanation']}\n\n"

                            # Add SQL query
                            if result.get("sql_query"):
                                # For SQL code blocks, we don't need to escape characters inside ```
                                # because they are treated as literal text
                                sql_query = result["sql_query"]
                                reply_message += f"📝 *SQL Query:*\n```sql\n{sql_query}\n```\n\n"

                            # Add execution time
                            if result.get("execution_time"):
                                reply_message += f"⏱️ Execution time: {result['execution_time']:.2f}s"

                        else:
                            # Handle API error
                            reply_message = f"❌ *Error:*\n{result.get('message', 'Unknown error')}"

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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_query))
    application.add_error_handler(bot.error_handler)

    # Start the bot
    logger.info("Starting CloverdashBot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
