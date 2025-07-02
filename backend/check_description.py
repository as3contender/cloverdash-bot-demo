#!/usr/bin/env python3
"""
Скрипт для проверки конкретного описания
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


async def check_description(database_name, schema_name, table_name):
    """Проверка конкретного описания"""

    try:
        await app_database_service.initialize()

        description = await app_database_service.get_table_description(database_name, table_name, schema_name)

        if description:
            logger.info(f"Description for {database_name}.{schema_name}.{table_name}:")

            if isinstance(description, dict):
                logger.info(f"  Description: {description.get('description', 'N/A')}")
                logger.info(f"  Object type: {description.get('object_type', 'N/A')}")
                logger.info(f"  Schema: {description.get('schema_name', 'N/A')}")
                logger.info(f"  Notes: {description.get('notes', 'N/A')}")
                logger.info(f"  Imported from: {description.get('imported_from', 'N/A')}")

                if "columns" in description:
                    columns = description["columns"]
                    logger.info(f"  Columns ({len(columns)}):")
                    for col_name, col_info in list(columns.items())[:5]:  # Показываем первые 5
                        if isinstance(col_info, dict):
                            logger.info(f"    {col_name}: {col_info.get('описание', 'No description')}")
                    if len(columns) > 5:
                        logger.info(f"    ... и еще {len(columns) - 5} колонок")
            else:
                logger.info(f"  Raw data: {str(description)[:200]}...")

        else:
            logger.info(f"No description found for {database_name}.{schema_name}.{table_name}")

    except Exception as e:
        logger.error(f"Failed to check description: {str(e)}")

    finally:
        await app_database_service.close()


if __name__ == "__main__":
    if len(sys.argv) == 4:
        database_name = sys.argv[1]
        schema_name = sys.argv[2]
        table_name = sys.argv[3]
        asyncio.run(check_description(database_name, schema_name, table_name))
    else:
        print("Usage: python check_description.py <database_name> <schema_name> <table_name>")
        print("Example: python check_description.py test1 demo1 bills_view")
