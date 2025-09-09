TRANSLATIONS = {
   
    "ru": {
        "start": """Привет, {name}! 👋\n\nЯ CloverdashBot, твой ассистент по базе данных!\n\nЯ могу:\n• Отвечать на вопросы о данных на естественном языке\n• Строить SQL запросы автоматически\n• Предоставлять результаты в удобном формате\n\nПросто задайте мне вопрос о данных, и я найду ответ!\n\nПопробуйте эти примеры, нажав на кнопки ниже:""",
        "help": """🤖 Доступные команды:\n\n/start - Начать работу с ботом\n/help - Показать это сообщение\n/tables - Показать доступные таблицы и представления\n/sample <table_name> - Показать первые 3 записи из таблицы\n/settings - Показать или изменить настройки\n\n🌐 Быстрая смена языка:\n• /ru - Переключить на Русский 🇷🇺 (основной)\n• /en - Переключить на English 🇺🇸\n\n📊 Как пользоваться:\nПросто задайте вопрос о данных на естественном языке, и я найду ответ!\n\nПримеры вопросов:\n• \"Покажи текущее время и дату\"\n• \"Каков объем продаж в январе?\"\n• \"Покажи список таблиц в базе данных\"\n\nПример команды sample:\n• /sample bills_view\n• /sample demo1.bills_view\n• /sample public.users\n\n⚙️ Команды настроек:\n• /settings - Показать текущие настройки\n• /settings lang ru - Установить русский язык 🇷🇺 (основной)\n• /settings lang en - Установить английский язык 🇺🇸\n• /settings show_explanation on - Показывать объяснения\n• /settings show_sql on - Показывать SQL запросы""",
        "settings_saved": "Настройки обновлены ✅",
        "current_settings": "⚙️ Ваши настройки:\n\n🌐 Язык: {lang}\n💬 Показывать объяснение: {explanation}\n🔧 Показывать SQL: {sql}\n\n💡 Быстрые команды:\n• /settings lang ru - Русский язык (основной)\n• /settings lang en - English language",
        "invalid_language": "❌ Неподдерживаемый язык. Используйте:\n• /settings lang en - English 🇺🇸\n• /settings lang ru - Русский 🇷🇺",
        "unknown_setting": "❌ Неизвестная настройка. Доступные опции:\n• /settings lang <en|ru> - Изменить язык\n• /settings show_explanation <on|off> - Переключить объяснения\n• /settings show_sql <on|off> - Переключить показ SQL",
        "settings_usage": "Примеры использования:\n• /settings - Показать текущие настройки\n• /settings lang en - Установить английский язык\n• /settings lang ru - Установить русский язык\n• /settings show_explanation on - Включить объяснения\n• /settings show_sql on - Включить показ SQL",
        "processing_request": "🔍 Обрабатываю ваш запрос...",
        "query_result_title": "✅ Результат запроса",
        "records_found": "📊 Найдено записей: {count}",
        "record_number": "🔹 Запись {num}:",
        "more_records": "... и еще {count} записей",
        "explanation_title": "💬 Объяснение:",
        "sql_query_title": "🔧 SQL запрос:",
        "execution_time": "⏱️ Время выполнения: {time:.2f}с",
        "error_occurred": "❌ Произошла ошибка. Пожалуйста, попробуйте еще раз.",
        "empty_query_error": "Пожалуйста, введите ваш вопрос",
        "validation_error": "Ошибка валидации ввода",
    },
     "en": {
        "start": """Hello, {name}! 👋\n\nI'm CloverdashBot, your database assistant!\n\nI can:\n• Answer questions about data in natural language\n• Build SQL queries automatically\n• Provide results in a convenient format\n\nJust ask me a question about the data, and I'll find the answer!\n\nTry these examples by clicking the buttons below:""",
        "help": """🤖 Available commands:\n\n/start - Start working with the bot\n/help - Show this message\n/tables - Show available tables and views\n/sample <table_name> - Show sample data (first 3 records) from a table\n/settings - Show or change your preferences\n\n🌐 Quick language switch:\n• /ru - Switch to Russian 🇷🇺 (default)\n• /en - Switch to English 🇺🇸\n\n📊 How to use:\nJust write your question about the data in natural language, and I'll find the answer!\n\nExample questions:\n• \"Show current time and date\"\n• \"What is the total sales amount in January 2025?\"\n• \"Show list of tables in the database\"\n\nExample sample commands:\n• /sample bills_view\n• /sample demo1.bills_view\n• /sample public.users\n\n⚙️ Settings commands:\n• /settings - Show current settings\n• /settings lang ru - Set language to Russian 🇷🇺 (default)\n• /settings lang en - Set language to English 🇺🇸\n• /settings show_explanation on - Show explanations\n• /settings show_sql on - Show SQL queries""",
        "settings_saved": "Settings updated ✅",
        "current_settings": "⚙️ Your settings:\n\n🌐 Language: {lang}\n💬 Show explanation: {explanation}\n🔧 Show SQL: {sql}\n\n💡 Quick commands:\n• /settings lang ru - Русский язык (default)\n• /settings lang en - English language",
        "invalid_language": "❌ Unsupported language. Use:\n• /settings lang en - English 🇺🇸\n• /settings lang ru - Русский 🇷🇺",
        "unknown_setting": "❌ Unknown setting. Available options:\n• /settings lang <en|ru> - Change language\n• /settings show_explanation <on|off> - Toggle explanations\n• /settings show_sql <on|off> - Toggle SQL display",
        "settings_usage": "Usage examples:\n• /settings - Show current settings\n• /settings lang en - Set English language\n• /settings lang ru - Set Russian language\n• /settings show_explanation on - Enable explanations\n• /settings show_sql on - Enable SQL display",
        "processing_request": "🔍 Processing your request...",
        "query_result_title": "✅ Query Result",
        "records_found": "📊 Records found: {count}",
        "record_number": "🔹 Record {num}:",
        "more_records": "... and {count} more records",
        "explanation_title": "💬 Explanation:",
        "sql_query_title": "🔧 SQL Query:",
        "execution_time": "⏱️ Execution time: {time:.2f}s",
        "error_occurred": "❌ An error occurred. Please try again later.",
        "empty_query_error": "Please enter your question",
        "validation_error": "Input validation error",
    },
}


def get_translation(lang: str, key: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, "")
