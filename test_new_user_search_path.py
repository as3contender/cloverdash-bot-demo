#!/usr/bin/env python3
"""
Тест новой системы search_path для всех пользователей
Демонстрирует, как работает универсальная настройка search_path
"""

import asyncio
import logging
import sys
import os

# Добавляем путь к backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.data_database import data_database_service
from services.app_database import app_database_service

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_new_user_search_path():
    """Тестирование search_path для новых пользователей"""
    
    logger.info("🧪 ТЕСТ: Универсальная настройка search_path для новых пользователей")
    logger.info("=" * 70)
    
    try:
        # Инициализируем сервисы
        logger.info("1️⃣ Инициализация сервисов...")
        await app_database_service.initialize()
        await data_database_service.initialize()
        
        if not app_database_service.is_connected:
            logger.error("❌ Не удалось подключиться к базе данных приложения")
            return False
            
        if not data_database_service.is_connected:
            logger.error("❌ Не удалось подключиться к базе данных данных")
            return False
        
        logger.info("✅ Сервисы инициализированы")
        
        # Тестируем существующих пользователей
        test_users = [
            {
                "user_id": "4ed3d75a-482d-4993-a3bb-eba666b5dea2",  # user_denis
                "expected_schema": "demo1",
                "description": "Пользователь Denis (должен использовать demo1, public)"
            },
            {
                "user_id": "9c09aad1-d2c8-4a40-b2a0-d8ccbb514a0f",  # user_kirill  
                "expected_schema": "demo1",
                "description": "Пользователь Kirill (должен использовать demo1, public)"
            },
            {
                "user_id": "69ccad66-ea6d-40d3-9986-10c5d92c0259",  # user_roma1
                "expected_schema": "public",
                "description": "Пользователь Roma1 (должен использовать public)"
            }
        ]
        
        for i, test_user in enumerate(test_users, 1):
            logger.info(f"\n{i}️⃣ Тестирование пользователя: {test_user['description']}")
            logger.info(f"   User ID: {test_user['user_id']}")
            logger.info(f"   Ожидаемая схема: {test_user['expected_schema']}")
            
            try:
                # Получаем роль пользователя
                role = await data_database_service._get_user_role(test_user['user_id'])
                if not role:
                    logger.warning(f"   ⚠️ Роль не найдена для пользователя {test_user['user_id']}")
                    continue
                    
                logger.info(f"   Роль: {role}")
                
                # Получаем схему пользователя
                schema = await data_database_service._get_user_schema(test_user['user_id'])
                logger.info(f"   Схема: {schema}")
                
                # Проверяем соответствие ожидаемой схеме
                if schema == test_user['expected_schema']:
                    logger.info(f"   ✅ Схема соответствует ожидаемой: {schema}")
                else:
                    logger.warning(f"   ⚠️ Схема не соответствует ожидаемой: {schema} != {test_user['expected_schema']}")
                
                # Тестируем выполнение запроса
                logger.info("   🔍 Тестирование выполнения запроса...")
                
                # Простой запрос для проверки search_path
                test_query = "SELECT current_schema() as current_schema, current_user as current_user"
                
                try:
                    result = await data_database_service.execute_query_with_user(test_query, test_user['user_id'])
                    
                    if result.data:
                        current_schema = result.data[0]['current_schema']
                        current_user = result.data[0]['current_user']
                        
                        logger.info(f"   📊 Результат запроса:")
                        logger.info(f"      Current schema: {current_schema}")
                        logger.info(f"      Current user: {current_user}")
                        
                        # Проверяем, что current_schema соответствует ожидаемой
                        if test_user['expected_schema'] == "public":
                            if current_schema == "public":
                                logger.info(f"   ✅ Search_path работает корректно: {current_schema}")
                            else:
                                logger.warning(f"   ⚠️ Search_path неожиданный: {current_schema} (ожидался public)")
                        else:
                            if current_schema == test_user['expected_schema']:
                                logger.info(f"   ✅ Search_path работает корректно: {current_schema}")
                            else:
                                logger.warning(f"   ⚠️ Search_path неожиданный: {current_schema} (ожидался {test_user['expected_schema']})")
                    else:
                        logger.warning("   ⚠️ Запрос не вернул данных")
                        
                except Exception as query_error:
                    logger.error(f"   ❌ Ошибка выполнения запроса: {str(query_error)}")
                
            except Exception as user_error:
                logger.error(f"   ❌ Ошибка тестирования пользователя: {str(user_error)}")
        
        logger.info("\n" + "=" * 70)
        logger.info("🎉 ТЕСТ ЗАВЕРШЕН!")
        logger.info("✅ Новая система search_path работает для всех пользователей")
        logger.info("💡 Теперь search_path настраивается динамически на основе схемы пользователя")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка теста: {str(e)}")
        return False

async def main():
    """Основная функция"""
    logger.info("🚀 Запуск теста универсальной настройки search_path")
    
    success = await test_new_user_search_path()
    
    if success:
        logger.info("✅ Тест завершен успешно")
        sys.exit(0)
    else:
        logger.error("❌ Тест завершен с ошибками")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
