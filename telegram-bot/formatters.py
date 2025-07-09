import re
from typing import Dict, Any, List
from translations import get_translation


class MessageFormatter:
    """Класс для форматирования сообщений Telegram"""

    @staticmethod
    def clean_markdown(text: str) -> str:
        """Удаление Markdown форматирования из текста для отображения как обычный текст"""
        if not text:
            return ""

        # Удаляем блоки кода (многострочные)
        text = re.sub(r"```[\w]*\n?(.*?)\n?```", r"\1", text, flags=re.DOTALL)

        # Удаляем встроенный код
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # Удаляем жирный текст
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)

        # Удаляем курсив (и * и _)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        text = re.sub(r"_([^_]+)_", r"\1", text)

        # Удаляем зачеркнутый текст
        text = re.sub(r"~~([^~]+)~~", r"\1", text)

        # Удаляем заголовки
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

        # Удаляем ссылки, но оставляем текст
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # Удаляем экранированные символы
        text = text.replace("\\*", "*")
        text = text.replace("\\_", "_")
        text = text.replace("\\`", "`")
        text = text.replace("\\#", "#")
        text = text.replace("\\[", "[")
        text = text.replace("\\]", "]")
        text = text.replace("\\(", "(")
        text = text.replace("\\)", ")")

        # Очищаем лишние пробелы
        text = re.sub(r"\n\s*\n", "\n\n", text)  # Множественные переносы строк в двойные
        text = text.strip()

        return text

    @staticmethod
    def escape_markdown(text: str) -> str:
        """Экранирование специальных символов Markdown для безопасного отображения"""
        if not text:
            return ""

        # Преобразуем в строку если еще не строка
        text = str(text)

        # Экранируем только самые проблемные символы Markdown
        # Это те, которые чаще всего вызывают ошибки парсинга
        text = text.replace("_", "\\_")
        text = text.replace("*", "\\*")
        text = text.replace("`", "\\`")
        text = text.replace("[", "\\[")
        text = text.replace("]", "\\]")

        return text

    @staticmethod
    def format_tables_list(tables: List[Dict[str, Any]], database_name: str) -> str:
        """Форматирование списка таблиц"""
        reply_message = f"📊 *Available tables in {database_name}*\n\n"
        reply_message += f"🔢 Total: {len(tables)} objects\n\n"

        # Группируем по схеме
        schemas = {}
        for table in tables:
            schema = table["schema_name"]
            if schema not in schemas:
                schemas[schema] = {"tables": [], "views": []}

            if table["object_type"] == "view":
                schemas[schema]["views"].append(table)
            else:
                schemas[schema]["tables"].append(table)

        # Показываем каждую схему
        for schema_name, objects in schemas.items():
            reply_message += f"🗂️ *Schema: {schema_name}*\n"

            # Показываем таблицы
            if objects["tables"]:
                reply_message += f"📋 Tables ({len(objects['tables'])}):\n"
                for table in objects["tables"]:
                    safe_name = MessageFormatter.escape_markdown(table["full_name"])
                    reply_message += f"   • `{safe_name}`\n"

            # Показываем представления
            if objects["views"]:
                reply_message += f"👁️ Views ({len(objects['views'])}):\n"
                for view in objects["views"]:
                    safe_name = MessageFormatter.escape_markdown(view["full_name"])
                    reply_message += f"   • `{safe_name}`\n"

            reply_message += "\n"

        reply_message += "💡 *Usage:*\n"
        reply_message += "• `/sample <table_name>` - show sample data\n"
        reply_message += "• Ask questions in natural language!"

        return reply_message

    @staticmethod
    def format_sample_data(data: List[Dict[str, Any]], table_name: str) -> str:
        """Форматирование образца данных из таблицы"""
        reply_message = f"📊 *Sample data from `{table_name}`*\n\n"
        reply_message += f"🔢 Records shown: {len(data)}/3\n\n"

        # Показываем каждую запись
        for i, row in enumerate(data):
            reply_message += f"🔹 *Record {i+1}:*\n"
            for key, value in row.items():
                # Экранируем специальные символы Markdown
                safe_key = MessageFormatter.escape_markdown(str(key))
                safe_value = MessageFormatter.escape_markdown(str(value) if value is not None else "NULL")
                reply_message += f"   • {safe_key}: `{safe_value}`\n"
            reply_message += "\n"

        return reply_message

    @staticmethod
    def format_query_result(result: Dict[str, Any], settings: Dict[str, Any]) -> str:
        """Форматирование результата запроса с поддержкой многоязычности"""
        lang = settings.get("preferred_language", "en")
        
        # Заголовок результата
        reply_message = f"*{get_translation(lang, 'query_result_title')}*\n\n"

        # Добавляем данные если доступны
        if result.get("data") and len(result["data"]) > 0:
            data_count = len(result["data"])
            reply_message += get_translation(lang, "records_found").format(count=data_count) + "\n\n"

            # Показываем первые несколько записей (до 5 для лучшей читаемости)
            max_records = min(5, data_count)
            for i, row in enumerate(result["data"][:max_records]):
                reply_message += get_translation(lang, "record_number").format(num=i+1) + "\n"
                
                # Форматируем поля более красиво
                for key, value in row.items():
                    safe_key = MessageFormatter.escape_markdown(str(key))
                    
                    # Улучшаем отображение значений
                    if value is None:
                        safe_value = "∅"  # Красивый символ для NULL
                    elif isinstance(value, (int, float)):
                        safe_value = f"`{value}`"  # Числа в моноширинном шрифте
                    elif isinstance(value, str) and len(value) > 50:
                        # Длинные строки сокращаем
                        truncated = value[:47] + "..." if len(value) > 50 else value
                        safe_value = f"_{MessageFormatter.escape_markdown(truncated)}_"
                    else:
                        safe_value = f"_{MessageFormatter.escape_markdown(str(value))}_"
                    
                    reply_message += f"   • *{safe_key}*: {safe_value}\n"
                reply_message += "\n"

            # Показываем сколько еще записей
            if data_count > max_records:
                remaining = data_count - max_records
                reply_message += get_translation(lang, "more_records").format(count=remaining) + "\n\n"

        elif result.get("data") is not None and len(result["data"]) == 0:
            # Если запрос выполнился, но данных нет
            reply_message += "📋 " + ("No records found" if lang == "en" else "Записи не найдены") + "\n\n"

        # Добавляем объяснение если доступно и разрешено
        if settings.get("show_explanation", True) and result.get("explanation"):
            safe_explanation = MessageFormatter.escape_markdown(result["explanation"])
            reply_message += f"*{get_translation(lang, 'explanation_title')}*\n"
            reply_message += f"_{safe_explanation}_\n\n"

        # Добавляем SQL запрос если разрешено
        if settings.get("show_sql", False) and result.get("sql_query"):
            sql_query = result["sql_query"]
            reply_message += f"*{get_translation(lang, 'sql_query_title')}*\n"
            reply_message += f"```sql\n{sql_query}\n```\n\n"

        # Добавляем время выполнения
        if result.get("execution_time"):
            execution_time = result["execution_time"]
            reply_message += get_translation(lang, "execution_time").format(time=execution_time)

        return reply_message
