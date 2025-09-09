#!/usr/bin/env python3
"""
Скрипт для поиска правильного user_id для пользователя с ролью user_kirill.
"""

import asyncio
import logging
import sys
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('find_correct_user_id.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def find_correct_user_id():
    """Ищет правильный user_id для пользователя с ролью user_kirill"""
    logger.info("🔍 Поиск правильного user_id для пользователя с ролью user_kirill")
    
    try:
        from services.app_database import app_database_service
        
        # Инициализируем подключение
        await app_database_service.initialize()
        
        if not app_database_service.is_connected:
            logger.error("❌ База данных приложения недоступна")
            return False
        
        logger.info("✅ Подключение к базе данных приложения установлено")
        
        # 1. Ищем все записи с ролью user_kirill
        logger.info("🔍 Поиск всех записей с ролью user_kirill...")
        
        try:
            query = """
            SELECT user_id, role_name, database_name, schema_name, created_at 
            FROM users_role_bd_mapping 
            WHERE role_name = 'user_kirill'
            """
            result = await app_database_service.execute_query(query)
            
            logger.info(f"📊 Найдено записей с ролью user_kirill: {result.row_count}")
            
            if result.data:
                logger.info("📋 Записи с ролью user_kirill:")
                for i, mapping in enumerate(result.data, 1):
                    logger.info(f"   {i}. User ID: {mapping['user_id']}")
                    logger.info(f"      Role: {mapping.get('role_name', 'N/A')}")
                    logger.info(f"      Database: {mapping.get('database_name', 'N/A')}")
                    logger.info(f"      Schema: {mapping.get('schema_name', 'N/A')}")
                    logger.info(f"      Created: {mapping.get('created_at', 'N/A')}")
                    logger.info("")
                    
                    # Проверяем, есть ли этот пользователь в таблице users
                    user_query = "SELECT id, email, name FROM users WHERE id = $1"
                    user_result = await app_database_service.execute_query(user_query, [mapping['user_id']])
                    
                    if user_result.data:
                        user = user_result.data[0]
                        logger.info(f"   ✅ Пользователь найден в таблице users:")
                        logger.info(f"      ID: {user['id']}")
                        logger.info(f"      Email: {user.get('email', 'N/A')}")
                        logger.info(f"      Name: {user.get('name', 'N/A')}")
                    else:
                        logger.info(f"   ❌ Пользователь НЕ найден в таблице users")
                    logger.info("")
            else:
                logger.info("ℹ️  Записей с ролью user_kirill не найдено")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при поиске записей с ролью user_kirill: {str(e)}")
        
        # 2. Ищем все записи, содержащие "639c-40bd-a645-31dcaa68871b"
        logger.info("🔍 Поиск записей, содержащих '639c-40bd-a645-31dcaa68871b'...")
        
        try:
            query = """
            SELECT user_id, role_name, database_name, schema_name, created_at 
            FROM users_role_bd_mapping 
            WHERE user_id::VARCHAR LIKE '%639c-40bd-a645-31dcaa68871b%'
            """
            result = await app_database_service.execute_query(query)
            
            logger.info(f"📊 Найдено записей, содержащих '639c-40bd-a645-31dcaa68871b': {result.row_count}")
            
            if result.data:
                logger.info("📋 Записи, содержащие '639c-40bd-a645-31dcaa68871b':")
                for i, mapping in enumerate(result.data, 1):
                    logger.info(f"   {i}. User ID: {mapping['user_id']}")
                    logger.info(f"      Role: {mapping.get('role_name', 'N/A')}")
                    logger.info(f"      Database: {mapping.get('database_name', 'N/A')}")
                    logger.info(f"      Schema: {mapping.get('schema_name', 'N/A')}")
                    logger.info(f"      Created: {mapping.get('created_at', 'N/A')}")
                    logger.info("")
            else:
                logger.info("ℹ️  Записей, содержащих '639c-40bd-a645-31dcaa68871b', не найдено")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при поиске записей с частичным UUID: {str(e)}")
        
        # 3. Показываем все записи в users_role_bd_mapping
        logger.info("📋 Все записи в users_role_bd_mapping:")
        
        try:
            query = """
            SELECT user_id, role_name, database_name, schema_name, created_at 
            FROM users_role_bd_mapping 
            ORDER BY created_at DESC
            """
            result = await app_database_service.execute_query(query)
            
            logger.info(f"📊 Всего записей в users_role_bd_mapping: {result.row_count}")
            
            if result.data:
                for i, mapping in enumerate(result.data, 1):
                    logger.info(f"   {i}. User ID: {mapping['user_id']}")
                    logger.info(f"      Role: {mapping.get('role_name', 'N/A')}")
                    logger.info(f"      Database: {mapping.get('database_name', 'N/A')}")
                    logger.info(f"      Schema: {mapping.get('schema_name', 'N/A')}")
                    logger.info(f"      Created: {mapping.get('created_at', 'N/A')}")
                    logger.info("")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка при получении всех записей: {str(e)}")
        
        logger.info("🎉 Поиск user_id завершен!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {str(e)}")
        return False
    
    finally:
        try:
            await app_database_service.close()
            logger.info("🔌 Подключение к базе данных приложения закрыто")
        except Exception as e:
            logger.error(f"❌ Ошибка при закрытии подключения: {str(e)}")


async def main():
    """Основная функция"""
    logger.info("🔧 Поиск правильного user_id")
    logger.info(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    try:
        success = await find_correct_user_id()
        
        if success:
            logger.info("🎯 Поиск завершен успешно!")
            return 0
        else:
            logger.error("💥 Поиск завершен с ошибками!")
            return 1
            
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

