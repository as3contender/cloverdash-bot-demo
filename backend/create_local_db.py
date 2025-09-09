#!/usr/bin/env python3
"""
Скрипт для создания локальной базы данных с тестовыми данными
"""

import asyncio
import asyncpg
import sys
import time

async def wait_for_db():
    """Ждем пока PostgreSQL запустится"""
    url = "postgresql://postgres:password@localhost:5432/cloverdash_bot"
    
    print("⏳ Ожидаем запуск PostgreSQL...")
    
    for attempt in range(30):  # 30 попыток
        try:
            conn = await asyncpg.connect(url, command_timeout=5)
            await conn.close()
            print("✅ PostgreSQL готов!")
            return True
        except Exception as e:
            print(f"Попытка {attempt + 1}/30: {e}")
            await asyncio.sleep(2)
    
    print("❌ PostgreSQL не запустился")
    return False

async def create_database():
    """Создаем базу данных и таблицы"""
    
    print("🚀 Создание локальной базы данных...")
    
    # Ждем PostgreSQL
    if not await wait_for_db():
        return False
    
    url = "postgresql://postgres:password@localhost:5432/cloverdash_bot"
    
    try:
        conn = await asyncpg.connect(url)
        
        # Создаем таблицы
        print("📋 Создание таблиц...")
        
        # Таблица пользователей
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(255) PRIMARY KEY,
                username VARCHAR(255),
                email VARCHAR(255),
                full_name VARCHAR(255),
                hashed_password VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица описаний БД
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS database_descriptions (
                id SERIAL PRIMARY KEY,
                database_name VARCHAR(255) NOT NULL,
                schema_name VARCHAR(255) NOT NULL DEFAULT 'public',
                table_name VARCHAR(255) NOT NULL,
                object_type VARCHAR(50) NOT NULL DEFAULT 'table',
                table_description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица маппинга пользователей к ролям
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users_role_bd_mapping (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                role_name VARCHAR(255) NOT NULL,
                database_name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица прав пользователей
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_permissions (
                id SERIAL PRIMARY KEY,
                role_name VARCHAR(255) NOT NULL,
                database_name VARCHAR(255) NOT NULL,
                schema_name VARCHAR(255) NOT NULL DEFAULT 'public',
                table_name VARCHAR(255) NOT NULL,
                permission_type VARCHAR(50) NOT NULL DEFAULT 'SELECT',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("✅ Таблицы созданы!")
        
        # Добавляем тестовые данные
        print("📊 Добавление тестовых данных...")
        
        # Тестовые пользователи
        await conn.executemany("""
            INSERT INTO users (id, username, email, full_name) 
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO NOTHING
        """, [
            ("demo_user", "demo", "demo@example.com", "Demo User"),
            ("admin", "admin", "admin@example.com", "Admin User"),
            ("test_user", "test", "test@example.com", "Test User")
        ])
        
        # Роли пользователей
        await conn.executemany("""
            INSERT INTO users_role_bd_mapping (user_id, role_name, database_name)
            VALUES ($1, $2, $3)
            ON CONFLICT DO NOTHING
        """, [
            ("demo_user", "user", "cloverdash_bot"),
            ("admin", "admin", "cloverdash_bot"),
            ("test_user", "readonly", "cloverdash_bot")
        ])
        
        # Описания таблиц
        await conn.executemany("""
            INSERT INTO database_descriptions (database_name, table_name, table_description, object_type)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT DO NOTHING
        """, [
            ("cloverdash_bot", "users", "Таблица пользователей системы", "table"),
            ("cloverdash_bot", "user_permissions", "Права доступа пользователей к таблицам", "table"),
            ("cloverdash_bot", "users_role_bd_mapping", "Маппинг пользователей к ролям в БД", "table"),
            ("cloverdash_bot", "database_descriptions", "Описания таблиц и представлений БД", "table"),
            ("cloverdash_bot", "sales", "Таблица продаж и заказов", "table"),
            ("cloverdash_bot", "products", "Каталог товаров", "table"),
            ("cloverdash_bot", "customers", "Информация о клиентах", "table")
        ])
        
        # Права доступа
        await conn.executemany("""
            INSERT INTO user_permissions (role_name, database_name, table_name, permission_type)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT DO NOTHING
        """, [
            # Админ видит все
            ("admin", "cloverdash_bot", "users", "SELECT"),
            ("admin", "cloverdash_bot", "user_permissions", "SELECT"),
            ("admin", "cloverdash_bot", "users_role_bd_mapping", "SELECT"),
            ("admin", "cloverdash_bot", "database_descriptions", "SELECT"),
            ("admin", "cloverdash_bot", "sales", "SELECT"),
            ("admin", "cloverdash_bot", "products", "SELECT"),
            ("admin", "cloverdash_bot", "customers", "SELECT"),
            
            # Обычный пользователь видит основные таблицы
            ("user", "cloverdash_bot", "sales", "SELECT"),
            ("user", "cloverdash_bot", "products", "SELECT"),
            ("user", "cloverdash_bot", "customers", "SELECT"),
            
            # Только чтение для readonly
            ("readonly", "cloverdash_bot", "products", "SELECT")
        ])
        
        print("✅ Тестовые данные добавлены!")
        
        # Проверяем результат
        users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        tables_count = await conn.fetchval("SELECT COUNT(*) FROM database_descriptions")
        permissions_count = await conn.fetchval("SELECT COUNT(*) FROM user_permissions")
        
        print(f"📊 Статистика:")
        print(f"   - Пользователей: {users_count}")
        print(f"   - Описаний таблиц: {tables_count}")
        print(f"   - Прав доступа: {permissions_count}")
        
        await conn.close()
        print("🎉 Локальная база данных готова!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания БД: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(create_database())
    sys.exit(0 if success else 1)
