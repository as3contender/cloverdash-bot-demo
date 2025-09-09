#!/usr/bin/env python3
"""
Диагностика и исправление проблемы с ролью user_denis
"""

import asyncio
import logging
import asyncpg
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Параметры подключения к базе данных test1
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/test1")

async def diagnose_user_denis():
    """Диагностика проблемы с ролью user_denis"""
    logger.info("🔍 Диагностика проблемы с ролью user_denis")
    logger.info("=" * 60)
    
    connection = None
    
    try:
        # Подключаемся к базе данных test1
        logger.info("🔌 Подключение к базе данных test1...")
        connection = await asyncpg.connect(DATABASE_URL)
        logger.info("✅ Подключение установлено")
        
        # 1. Проверяем существование роли user_denis
        logger.info("\n1️⃣ Проверка существования роли user_denis...")
        role_check = await connection.fetchrow("""
            SELECT rolname, rolconfig, rolcanlogin, rolsuper 
            FROM pg_roles 
            WHERE rolname = 'user_denis'
        """)
        
        if role_check:
            logger.info("✅ Роль user_denis существует:")
            logger.info(f"   - Имя: {role_check['rolname']}")
            logger.info(f"   - Конфигурация: {role_check['rolconfig']}")
            logger.info(f"   - Может логиниться: {role_check['rolcanlogin']}")
            logger.info(f"   - Суперпользователь: {role_check['rolsuper']}")
        else:
            logger.error("❌ Роль user_denis НЕ существует!")
            return False
        
        # 2. Проверяем права на схему demo1
        logger.info("\n2️⃣ Проверка прав на схему demo1...")
        schema_privileges = await connection.fetch("""
            SELECT privilege_type 
            FROM information_schema.usage_privileges 
            WHERE grantee = 'user_denis' AND object_name = 'demo1'
        """)
        
        if schema_privileges:
            logger.info("✅ Права на схему demo1:")
            for priv in schema_privileges:
                logger.info(f"   - {priv['privilege_type']}")
        else:
            logger.warning("⚠️ Нет прав на схему demo1")
        
        # 3. Проверяем права на bills_view
        logger.info("\n3️⃣ Проверка прав на bills_view...")
        table_privileges = await connection.fetch("""
            SELECT privilege_type 
            FROM information_schema.table_privileges 
            WHERE grantee = 'user_denis' AND schemaname = 'demo1' AND tablename = 'bills_view'
        """)
        
        if table_privileges:
            logger.info("✅ Права на bills_view:")
            for priv in table_privileges:
                logger.info(f"   - {priv['privilege_type']}")
        else:
            logger.warning("⚠️ Нет прав на bills_view")
        
        # 4. Проверяем search_path
        logger.info("\n4️⃣ Проверка search_path...")
        search_path = await connection.fetchval("""
            SELECT rolconfig 
            FROM pg_roles 
            WHERE rolname = 'user_denis' AND rolconfig IS NOT NULL
        """)
        
        if search_path:
            logger.info(f"✅ Search_path настроен: {search_path}")
        else:
            logger.warning("⚠️ Search_path не настроен")
        
        # 5. Тестируем доступ к bills_view
        logger.info("\n5️⃣ Тестирование доступа к bills_view...")
        try:
            # Устанавливаем роль user_denis
            await connection.execute("SET ROLE user_denis")
            logger.info("✅ Роль user_denis установлена")
            
            # Проверяем текущего пользователя
            current_user = await connection.fetchval("SELECT current_user")
            logger.info(f"   Текущий пользователь: {current_user}")
            
            # Проверяем search_path
            current_search_path = await connection.fetchval("SHOW search_path")
            logger.info(f"   Текущий search_path: {current_search_path}")
            
            # Пробуем получить данные из bills_view
            count = await connection.fetchval("SELECT COUNT(*) FROM bills_view")
            logger.info(f"✅ Доступ к bills_view работает! Записей: {count}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка доступа к bills_view: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка диагностики: {e}")
        return False
    finally:
        if connection:
            await connection.close()

async def fix_user_denis_role():
    """Исправление роли user_denis"""
    logger.info("\n🔧 Исправление роли user_denis")
    logger.info("=" * 60)
    
    connection = None
    
    try:
        # Подключаемся к базе данных test1
        logger.info("🔌 Подключение к базе данных test1...")
        connection = await asyncpg.connect(DATABASE_URL)
        logger.info("✅ Подключение установлено")
        
        # Команды для исправления роли
        fix_commands = [
            # 1. Устанавливаем search_path для роли user_denis
            "ALTER ROLE user_denis SET search_path TO demo1, public",
            
            # 2. Предоставляем права на схему demo1
            "GRANT USAGE ON SCHEMA demo1 TO user_denis",
            
            # 3. Предоставляем права на все таблицы в схеме demo1
            "GRANT SELECT ON ALL TABLES IN SCHEMA demo1 TO user_denis",
            
            # 4. Предоставляем права на будущие объекты
            "ALTER DEFAULT PRIVILEGES IN SCHEMA demo1 GRANT SELECT ON TABLES TO user_denis"
        ]
        
        for i, command in enumerate(fix_commands, 1):
            try:
                logger.info(f"{i}️⃣ Выполнение: {command}")
                await connection.execute(command)
                logger.info("   ✅ Успешно")
            except Exception as e:
                logger.error(f"   ❌ Ошибка: {e}")
        
        # Проверяем результат
        logger.info("\n🔍 Проверка результата...")
        role_config = await connection.fetchval("""
            SELECT rolconfig 
            FROM pg_roles 
            WHERE rolname = 'user_denis'
        """)
        
        if role_config:
            logger.info(f"✅ Search_path установлен: {role_config}")
        else:
            logger.warning("⚠️ Search_path не установлен")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка исправления: {e}")
        return False
    finally:
        if connection:
            await connection.close()

async def main():
    """Основная функция"""
    logger.info("🚀 Запуск диагностики и исправления роли user_denis")
    
    # Сначала диагностируем
    diagnosis_ok = await diagnose_user_denis()
    
    if not diagnosis_ok:
        logger.info("\n🔧 Запуск исправления...")
        fix_ok = await fix_user_denis_role()
        
        if fix_ok:
            logger.info("\n🔍 Повторная диагностика после исправления...")
            await diagnose_user_denis()
        else:
            logger.error("❌ Исправление не удалось")
    else:
        logger.info("✅ Роль user_denis работает корректно!")
    
    logger.info("\n🎉 Диагностика завершена!")

if __name__ == "__main__":
    asyncio.run(main())

