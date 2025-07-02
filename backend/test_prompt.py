#!/usr/bin/env python3
"""
Тестовый скрипт для проверки промпта LLM
"""

import asyncio
import logging
import sys
from pathlib import Path

# Добавляем путь к backend для импорта модулей
sys.path.append(str(Path(__file__).parent))

from services.llm_service import llm_service
from services.data_database import data_database_service
from services.app_database import app_database_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_prompt():
    """Тест генерации промпта для LLM"""

    try:
        # Инициализируем сервисы
        logger.info("Initializing services...")
        await app_database_service.initialize()
        await data_database_service.initialize()

        # Тестовый запрос
        test_query = "Покажи сумму продаж по товарам"

        logger.info(f"Test query: {test_query}")
        logger.info("=" * 80)

        # Получаем схему базы данных напрямую
        logger.info("Getting database schema...")
        db_schema = await llm_service._get_database_schema()

        print("\n=== DATABASE SCHEMA ===")
        print(f"Found {len(db_schema)} objects:")
        for name, info in db_schema.items():
            object_type = info.get("object_type", "table")
            schema_name = info.get("schema_name", "public")
            description = info.get("description", "No description")
            columns_count = len(info.get("columns", []))
            print(f"  - {schema_name}.{name} ({object_type}) - {columns_count} columns")
            print(f"    Description: {description[:100]}...")

        # Форматируем схему для промпта
        logger.info("Formatting schema for prompt...")
        schema_description = llm_service._format_schema_for_prompt(db_schema)

        print("\n=== FORMATTED SCHEMA FOR PROMPT ===")
        print(schema_description)

        # Создаем полный промпт
        logger.info("Creating full prompt...")
        full_prompt = await llm_service._create_sql_prompt(test_query)

        print("\n=== FULL LLM PROMPT ===")
        print(full_prompt)

        print("\n=== PROMPT ANALYSIS ===")
        lines = full_prompt.split("\n")
        print(f"Prompt length: {len(full_prompt)} characters")
        print(f"Prompt lines: {len(lines)}")

        # Ищем описания колонок
        description_lines = [line for line in lines if "описание" in line.lower()]
        print(f"Lines with column descriptions: {len(description_lines)}")

        # Ищем datatype информацию
        datatype_lines = [
            line
            for line in lines
            if any(dt in line for dt in ["varchar", "integer", "date", "numeric", "character varying"])
        ]
        print(f"Lines with data types: {len(datatype_lines)}")

        logger.info("Prompt test completed successfully!")

    except Exception as e:
        logger.error(f"Prompt test failed: {str(e)}")
        raise
    finally:
        # Закрываем соединения
        await app_database_service.close()
        await data_database_service.close()


if __name__ == "__main__":
    asyncio.run(test_prompt())
