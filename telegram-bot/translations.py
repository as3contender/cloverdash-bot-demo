TRANSLATIONS = {
    "en": {
        "start": """Hello, {name}! 👋\n\nI'm CloverdashBot, your database assistant!\n\nI can:\n• Answer questions about data in natural language\n• Build SQL queries automatically\n• Provide results in a convenient format\n\nJust ask me a question about the data, and I'll find the answer!\n\nExamples:\n• \"Show current time\"\n• \"What is the sales volume in January?\"\n• \"What is the best-selling product?\"""",
        "help": """🤖 Available commands:\n\n/start - Start working with the bot\n/help - Show this message\n/tables - Show available tables and views\n/sample <table_name> - Show sample data (first 3 records) from a table\n\n📊 How to use:\nJust write your question about the data in natural language, and I'll find the answer!\n\nExample questions:\n• \"Show current time and date\"\n• \"What is the sales volume in January?\"\n• \"Show list of tables in the database\"\n\nExample sample commands:\n• /sample bills_view\n• /sample demo1.bills_view\n• /sample public.users""",
        "settings_saved": "Settings updated",
        "current_settings": "Your settings:\nLanguage: {lang}\nShow explanation: {explanation}\nShow SQL: {sql}",
    },
    "ru": {
        "start": """Привет, {name}! 👋\n\nЯ CloverdashBot, твой ассистент по базе данных!\n\nЯ могу:\n• Отвечать на вопросы о данных на естественном языке\n• Строить SQL запросы автоматически\n• Предоставлять результаты в удобном формате\n\nПросто задайте мне вопрос о данных, и я найду ответ!\n\nПримеры:\n• \"Покажи текущее время\"\n• \"Каков объем продаж в январе?\"\n• \"Какой товар продается лучше всего?\"""",
        "help": """🤖 Доступные команды:\n\n/start - Начать работу с ботом\n/help - Показать это сообщение\n/tables - Показать доступные таблицы и представления\n/sample <table_name> - Показать первые 3 записи из таблицы\n\n📊 Как пользоваться:\nПросто задайте вопрос о данных на естественном языке, и я найду ответ!\n\nПримеры вопросов:\n• \"Покажи текущее время и дату\"\n• \"Каков объем продаж в январе?\"\n• \"Покажи список таблиц в базе данных\"\n\nПример команды sample:\n• /sample bills_view\n• /sample demo1.bills_view\n• /sample public.users""",
        "settings_saved": "Настройки обновлены",
        "current_settings": "Ваши настройки:\nЯзык: {lang}\nПоказывать объяснение: {explanation}\nПоказывать SQL: {sql}",
    },
}


def get_translation(lang: str, key: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, "")

