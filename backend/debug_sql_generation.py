#!/usr/bin/env python3
"""
Скрипт для диагностики генерации SQL запросов и проверки безопасности.
"""

import asyncio
import logging
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.app_database import app_database_service
from services.data_database import data_database_service
from services.llm_service import llm_service

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_sql_generation():
    """Диагностика генерации SQL запросов"""
    logger.info("🔍 Диагностика генерации SQL запросов")
    logger.info("=" * 60)
    
    # Инициализируем сервисы
    try:
        await app_database_service.initialize()
        await data_database_service.initialize()
        logger.info("✅ Все сервисы инициализированы")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации сервисов: {str(e)}")
        return
    
    # Тестируем с пользователем user_kirill
    user_id = "9c09aad1-d2c8-4a40-b2a0-d8ccbb514a0f"  # user_kirill
    test_query = "Show current time and date"
    
    logger.info(f"🧪 Тестируем запрос: '{test_query}'")
    logger.info(f"👤 Для пользователя: {user_id}")
    
    try:
        # 1. Получаем схему БД с правами пользователя
        logger.info("1️⃣ Получение схемы БД с правами пользователя...")
        schema = await llm_service._get_database_schema_with_user_permissions(user_id)
        logger.info(f"📊 Схема БД получена: {len(schema)} таблиц")
        
        for table_name, table_info in schema.items():
            logger.info(f"   • {table_name}: {table_info.get('object_type', 'table')}")
        
        # 2. Создаем промпт
        logger.info("2️⃣ Создание промпта...")
        prompt = await llm_service._create_sql_prompt_with_user_permissions(test_query, user_id, "en")
        logger.info(f"📝 Промпт создан (длина: {len(prompt)} символов)")
        
        # 3. Генерируем SQL через LLM
        logger.info("3️⃣ Генерация SQL через LLM...")
        llm_response = await llm_service.generate_sql_query_with_user_permissions(test_query, user_id, "en")
        
        if llm_response.sql_query:
            logger.info(f"✅ SQL запрос сгенерирован:")
            logger.info(f"📋 SQL: {llm_response.sql_query}")
            
            # 4. Проверяем безопасность SQL
            logger.info("4️⃣ Проверка безопасности SQL...")
            try:
                data_database_service._validate_sql_security(llm_response.sql_query)
                logger.info("✅ SQL запрос прошел проверку безопасности")
                
                # 5. Пытаемся выполнить запрос
                logger.info("5️⃣ Выполнение SQL запроса...")
                try:
                    result = await data_database_service.execute_query_with_user(llm_response.sql_query, user_id)
                    logger.info(f"✅ Запрос выполнен успешно: {result.row_count} строк")
                    if result.data:
                        logger.info("📊 Первые 3 строки результата:")
                        for i, row in enumerate(result.data[:3]):
                            logger.info(f"   {i+1}: {row}")
                except Exception as e:
                    logger.error(f"❌ Ошибка выполнения запроса: {str(e)}")
                    
            except Exception as e:
                logger.error(f"❌ SQL запрос НЕ прошел проверку безопасности: {str(e)}")
                
                # Дополнительная диагностика
                logger.info("🔍 Дополнительная диагностика:")
                cleaned_query = data_database_service._clean_sql_query(llm_response.sql_query)
                logger.info(f"🧹 Очищенный запрос: {cleaned_query}")
                
                # Проверяем каждое запрещенное слово
                dangerous_keywords = [
                    "DROP", "DELETE", "INSERT", "UPDATE", "CREATE", "ALTER", 
                    "TRUNCATE", "GRANT", "REVOKE", "MERGE", "REPLACE", "CALL",
                    "EXEC", "EXECUTE", "DECLARE", "CURSOR", "PROCEDURE", "FUNCTION",
                    "TRIGGER", "VIEW", "INDEX", "DATABASE", "SCHEMA", "TABLE", "COLUMN", "CONSTRAINT"
                ]
                
                import re
                for keyword in dangerous_keywords:
                    pattern = r"\b" + re.escape(keyword) + r"\b"
                    if re.search(pattern, cleaned_query, re.IGNORECASE):
                        logger.warning(f"⚠️  Найдено запрещенное слово: '{keyword}'")
        else:
            logger.error("❌ LLM не смог сгенерировать SQL запрос")
            logger.info(f"📝 Объяснение: {llm_response.explanation}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при диагностике: {str(e)}")
    
    # Закрываем сервисы
    await app_database_service.close()
    await data_database_service.close()
    logger.info("🔚 Диагностика завершена")

if __name__ == "__main__":
    asyncio.run(debug_sql_generation())
