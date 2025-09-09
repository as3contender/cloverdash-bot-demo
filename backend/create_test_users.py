#!/usr/bin/env python3
"""
Скрипт для создания тестовых пользователей и ролей в базе данных.

Этот скрипт:
1. Создает тестовых пользователей в таблице users
2. Создает роли в базе данных пользовательских данных
3. Добавляет маппинг пользователей к ролям
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
        logging.FileHandler('create_test_users.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def create_test_users():
    """Создает тестовых пользователей и роли"""
    logger.info("🚀 Создание тестовых пользователей и ролей")
    
    try:
        from services.app_database import app_database_service
        from services.data_database import data_database_service
        
        # Инициализируем подключения
        await app_database_service.initialize()
        await data_database_service.initialize()
        
        if not app_database_service.is_connected:
            logger.error("❌ База данных приложения недоступна")
            return False
            
        if not data_database_service.is_connected:
            logger.error("❌ База данных пользовательских данных недоступна")
            return False
        
        logger.info("✅ Подключения к базам данных установлены")
        
        # 1. Создаем тестовых пользователей в app database
        logger.info("👥 Создание тестовых пользователей...")
        
        test_users = [
            ("demo_user", "demo@example.com", "Demo User"),
            ("admin", "admin@example.com", "Admin User"),
            ("test_user", "test@example.com", "Test User"),
        ]
        
        for user_id, email, name in test_users:
            try:
                # Проверяем, существует ли пользователь
                check_query = "SELECT id FROM users WHERE id = $1"
                result = await app_database_service.execute_query(check_query, [user_id])
                
                if not result.data:
                    # Создаем пользователя
                    insert_query = """
                    INSERT INTO users (id, email, name, created_at, updated_at)
                    VALUES ($1, $2, $3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """
                    await app_database_service.execute_query(insert_query, [user_id, email, name])
                    logger.info(f"✅ Создан пользователь: {user_id}")
                else:
                    logger.info(f"ℹ️  Пользователь уже существует: {user_id}")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка при создании пользователя {user_id}: {str(e)}")
        
        # 2. Создаем роли в data database
        logger.info("🔐 Создание ролей в базе данных пользовательских данных...")
        
        roles = [
            ("demo_user_role", "Роль для демо пользователя"),
            ("admin_role", "Роль для администратора"),
            ("test_user_role", "Роль для тестового пользователя"),
        ]
        
        for role_name, role_description in roles:
            try:
                # Создаем роль
                create_role_query = f"CREATE ROLE {role_name}"
                await data_database_service.execute_query(create_role_query)
                logger.info(f"✅ Создана роль: {role_name}")
                
                # Предоставляем базовые права
                grant_query = f"GRANT USAGE ON SCHEMA public TO {role_name}"
                await data_database_service.execute_query(grant_query)
                logger.info(f"✅ Предоставлены права на схему public для роли: {role_name}")
                
            except Exception as e:
                if "already exists" in str(e):
                    logger.info(f"ℹ️  Роль уже существует: {role_name}")
                else:
                    logger.error(f"❌ Ошибка при создании роли {role_name}: {str(e)}")
        
        # 3. Создаем маппинг пользователей к ролям
        logger.info("🔗 Создание маппинга пользователей к ролям...")
        
        user_role_mappings = [
            ("demo_user", "demo_user_role", "cloverdash_data"),
            ("admin", "admin_role", "cloverdash_data"),
            ("test_user", "test_user_role", "cloverdash_data"),
        ]
        
        for user_id, role_name, database_name in user_role_mappings:
            try:
                # Проверяем, существует ли маппинг
                check_query = """
                SELECT id FROM users_role_bd_mapping 
                WHERE user_id = $1 AND role_name = $2
                """
                result = await app_database_service.execute_query(check_query, [user_id, role_name])
                
                if not result.data:
                    # Создаем маппинг
                    insert_query = """
                    INSERT INTO users_role_bd_mapping (user_id, role_name, database_name, created_at)
                    VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                    """
                    await app_database_service.execute_query(insert_query, [user_id, role_name, database_name])
                    logger.info(f"✅ Создан маппинг: {user_id} -> {role_name}")
                else:
                    logger.info(f"ℹ️  Маппинг уже существует: {user_id} -> {role_name}")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка при создании маппинга {user_id} -> {role_name}: {str(e)}")
        
        # 4. Проверяем созданные данные
        logger.info("🔍 Проверка созданных данных...")
        
        for user_id in ["demo_user", "admin", "test_user"]:
            try:
                query = """
                SELECT role_name, database_name 
                FROM users_role_bd_mapping 
                WHERE user_id::VARCHAR = $1
                """
                result = await app_database_service.execute_query(query, [user_id])
                
                if result.data:
                    role_info = result.data[0]
                    logger.info(f"✅ Пользователь {user_id}: роль '{role_info['role_name']}', БД '{role_info['database_name']}'")
                else:
                    logger.warning(f"⚠️  Пользователь {user_id}: роль не найдена")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка при проверке пользователя {user_id}: {str(e)}")
        
        logger.info("🎉 Создание тестовых пользователей завершено!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {str(e)}")
        return False
    
    finally:
        try:
            await app_database_service.close()
            await data_database_service.close()
            logger.info("🔌 Подключения к базам данных закрыты")
        except Exception as e:
            logger.error(f"❌ Ошибка при закрытии подключений: {str(e)}")


async def main():
    """Основная функция"""
    logger.info("🔧 Создание тестовых пользователей и ролей")
    logger.info(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    try:
        success = await create_test_users()
        
        if success:
            logger.info("🎯 Создание тестовых пользователей завершено успешно!")
            return 0
        else:
            logger.error("💥 Создание тестовых пользователей завершено с ошибками!")
            return 1
            
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
