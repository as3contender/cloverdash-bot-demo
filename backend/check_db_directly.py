#!/usr/bin/env python3
"""
Скрипт для прямой проверки данных в database_descriptions
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from services.app_database import app_database_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_db_content():
    """Прямая проверка содержимого таблицы database_descriptions"""

    try:
        await app_database_service.initialize()

        # Проверяем все записи в таблице
        query = """
        SELECT database_name, schema_name, table_name, object_type, 
               table_description::text as description_text
        FROM database_descriptions 
        ORDER BY database_name, schema_name, object_type, table_name
        """

        result = await app_database_service.execute_query(query)

        logger.info(f"Found {len(result.data)} records in database_descriptions:")
        logger.info("-" * 80)

        for row in result.data:
            logger.info(f"Database: {row['database_name']}")
            logger.info(f"Schema: {row['schema_name']}")
            logger.info(f"Object: {row['table_name']} ({row['object_type']})")

            # Парсим JSON описание
            try:
                desc_data = json.loads(row["description_text"])
                logger.info(f"Description: {desc_data.get('description', 'N/A')}")
                if "columns" in desc_data:
                    logger.info(f"Columns: {len(desc_data['columns'])}")
                if "notes" in desc_data:
                    logger.info(f"Notes: {desc_data['notes']}")
            except json.JSONDecodeError:
                logger.info(f"Raw data: {row['description_text'][:100]}...")

            logger.info("-" * 40)

    except Exception as e:
        logger.error(f"Failed to check database content: {str(e)}")

    finally:
        await app_database_service.close()


if __name__ == "__main__":
    asyncio.run(check_db_content())
