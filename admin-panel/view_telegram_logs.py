#!/usr/bin/env python3
"""
Скрипт для просмотра логов входа пользователей в базу данных через Telegram
"""

import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import re

# Добавляем путь к модулям
sys.path.append('.')

def get_db_connection():
    """Получение подключения к БД"""
    try:
        # Добавляем путь к backend
        backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        # Импортируем конфигурацию
        from config.settings import settings
        db_url = settings.get_app_database_url()
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        print(f"Ошибка получения конфигурации: {e}")
        # Fallback - попробуем через переменные окружения
        from dotenv import load_dotenv
        load_dotenv()
        
        db_url = os.getenv('DATABASE_URL') or os.getenv('APP_DATABASE_URL')
        if db_url:
            engine = create_engine(db_url)
            return engine
        else:
            print("Не удалось получить URL базы данных")
            return None

def get_telegram_users():
    """Получение пользователей с Telegram ID"""
    print("=== Пользователи с Telegram ID ===")
    
    engine = get_db_connection()
    if not engine:
        return
    
    try:
        with engine.connect() as conn:
            # Получаем пользователей с Telegram ID
            query = text("""
                SELECT 
                    id,
                    username,
                    full_name,
                    telegram_id,
                    telegram_username,
                    is_active,
                    created_at,
                    updated_at
                FROM users 
                WHERE telegram_id IS NOT NULL 
                ORDER BY created_at DESC
            """)
            
            result = conn.execute(query)
            users = result.fetchall()
            
            if users:
                print(f"📱 Найдено {len(users)} пользователей с Telegram ID:")
                print()
                
                for user in users:
                    status = "активен" if user.is_active else "неактивен"
                    print(f"👤 {user.username or 'Без имени'}")
                    print(f"   📱 Telegram ID: {user.telegram_id}")
                    print(f"   📛 Telegram username: @{user.telegram_username or 'не указан'}")
                    print(f"   👨‍💼 Полное имя: {user.full_name or 'не указано'}")
                    print(f"   ✅ Статус: {status}")
                    print(f"   📅 Создан: {user.created_at}")
                    print(f"   🔄 Обновлен: {user.updated_at}")
                    print()
            else:
                print("❌ Пользователи с Telegram ID не найдены")
                
    except Exception as e:
        print(f"❌ Ошибка при получении пользователей: {e}")

def get_user_login_history():
    """Получение истории входов пользователей"""
    print("=== История входов пользователей ===")
    
    engine = get_db_connection()
    if not engine:
        return
    
    try:
        with engine.connect() as conn:
            # Проверяем, есть ли таблица для истории входов
            query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_login_history'
                )
            """)
            result = conn.execute(query)
            table_exists = result.scalar()
            
            if table_exists:
                # Получаем историю входов
                query = text("""
                    SELECT 
                        ulh.*,
                        u.username,
                        u.telegram_id,
                        u.telegram_username
                    FROM user_login_history ulh
                    LEFT JOIN users u ON ulh.user_id = u.id
                    ORDER BY ulh.login_time DESC
                    LIMIT 50
                """)
                
                result = conn.execute(query)
                logins = result.fetchall()
                
                if logins:
                    print(f"📊 Найдено {len(logins)} записей о входах:")
                    print()
                    
                    for login in logins:
                        print(f"👤 Пользователь: {login.username or 'Неизвестно'}")
                        print(f"   📱 Telegram ID: {login.telegram_id or 'не указан'}")
                        print(f"   📛 Telegram username: @{login.telegram_username or 'не указан'}")
                        print(f"   🕐 Время входа: {login.login_time}")
                        print(f"   🌐 IP адрес: {login.ip_address or 'не указан'}")
                        print(f"   📱 User Agent: {login.user_agent or 'не указан'}")
                        print(f"   ✅ Успешность: {'Да' if login.success else 'Нет'}")
                        if login.error_message:
                            print(f"   ❌ Ошибка: {login.error_message}")
                        print()
                else:
                    print("❌ Записи о входах не найдены")
            else:
                print("ℹ️ Таблица user_login_history не существует")
                print("💡 Создайте таблицу для отслеживания истории входов")
                
    except Exception as e:
        print(f"❌ Ошибка при получении истории входов: {e}")

def get_recent_activity():
    """Получение недавней активности пользователей"""
    print("=== Недавняя активность пользователей ===")
    
    engine = get_db_connection()
    if not engine:
        return
    
    try:
        with engine.connect() as conn:
            # Проверяем, есть ли таблица для активности
            query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_activity'
                )
            """)
            result = conn.execute(query)
            table_exists = result.scalar()
            
            if table_exists:
                # Получаем недавнюю активность
                query = text("""
                    SELECT 
                        ua.*,
                        u.username,
                        u.telegram_id,
                        u.telegram_username
                    FROM user_activity ua
                    LEFT JOIN users u ON ua.user_id = u.id
                    WHERE ua.activity_time >= NOW() - INTERVAL '24 hours'
                    ORDER BY ua.activity_time DESC
                    LIMIT 50
                """)
                
                result = conn.execute(query)
                activities = result.fetchall()
                
                if activities:
                    print(f"📊 Найдено {len(activities)} записей активности за последние 24 часа:")
                    print()
                    
                    for activity in activities:
                        print(f"👤 Пользователь: {activity.username or 'Неизвестно'}")
                        print(f"   📱 Telegram ID: {activity.telegram_id or 'не указан'}")
                        print(f"   📛 Telegram username: @{activity.telegram_username or 'не указан'}")
                        print(f"   🕐 Время активности: {activity.activity_time}")
                        print(f"   🎯 Действие: {activity.action or 'не указано'}")
                        print(f"   📝 Детали: {activity.details or 'не указаны'}")
                        print()
                else:
                    print("❌ Активность за последние 24 часа не найдена")
            else:
                print("ℹ️ Таблица user_activity не существует")
                print("💡 Создайте таблицу для отслеживания активности пользователей")
                
    except Exception as e:
        print(f"❌ Ошибка при получении активности: {e}")

def analyze_log_files():
    """Анализ лог-файлов"""
    print("=== Анализ лог-файлов ===")
    
    # Список лог-файлов для анализа
    log_files = [
        "admin_panel.log",
        "../backend/test_real_user.log",
        "../backend/schema_validation.log",
        "../backend/test_execute_query_with_user.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\n📄 Анализ файла: {log_file}")
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # Ищем записи о Telegram пользователях
                telegram_entries = []
                auth_entries = []
                user_entries = []
                
                for line in lines:
                    if 'telegram' in line.lower():
                        telegram_entries.append(line.strip())
                    elif 'auth' in line.lower() or 'login' in line.lower():
                        auth_entries.append(line.strip())
                    elif 'user' in line.lower() and ('found' in line.lower() or 'executing' in line.lower()):
                        user_entries.append(line.strip())
                
                if telegram_entries:
                    print(f"   📱 Найдено {len(telegram_entries)} записей о Telegram:")
                    for entry in telegram_entries[-5:]:  # Последние 5 записей
                        print(f"      {entry}")
                
                if auth_entries:
                    print(f"   🔐 Найдено {len(auth_entries)} записей об аутентификации:")
                    for entry in auth_entries[-5:]:  # Последние 5 записей
                        print(f"      {entry}")
                
                if user_entries:
                    print(f"   👤 Найдено {len(user_entries)} записей о пользователях:")
                    for entry in user_entries[-5:]:  # Последние 5 записей
                        print(f"      {entry}")
                
                if not telegram_entries and not auth_entries and not user_entries:
                    print("   ℹ️ Записи о Telegram пользователях не найдены")
                    
            except Exception as e:
                print(f"   ❌ Ошибка при чтении файла: {e}")
        else:
            print(f"❌ Файл {log_file} не найден")

def get_database_connections():
    """Получение информации о подключениях к БД"""
    print("=== Подключения к базе данных ===")
    
    engine = get_db_connection()
    if not engine:
        return
    
    try:
        with engine.connect() as conn:
            # Получаем активные подключения
            query = text("""
                SELECT 
                    pid,
                    usename,
                    application_name,
                    client_addr,
                    client_port,
                    backend_start,
                    state,
                    query_start,
                    query
                FROM pg_stat_activity 
                WHERE state = 'active' 
                AND query NOT LIKE '%pg_stat_activity%'
                ORDER BY query_start DESC
            """)
            
            result = conn.execute(query)
            connections = result.fetchall()
            
            if connections:
                print(f"🔌 Найдено {len(connections)} активных подключений:")
                print()
                
                for conn_info in connections:
                    print(f"🆔 PID: {conn_info.pid}")
                    print(f"   👤 Пользователь: {conn_info.usename}")
                    print(f"   📱 Приложение: {conn_info.application_name or 'не указано'}")
                    print(f"   🌐 IP: {conn_info.client_addr}:{conn_info.client_port}")
                    print(f"   🕐 Начало: {conn_info.backend_start}")
                    print(f"   📊 Состояние: {conn_info.state}")
                    print(f"   🔍 Запрос: {conn_info.query[:100]}..." if conn_info.query else "   🔍 Запрос: не выполняется")
                    print()
            else:
                print("ℹ️ Активные подключения не найдены")
                
    except Exception as e:
        print(f"❌ Ошибка при получении подключений: {e}")

def main():
    """Основная функция"""
    print("🔍 Просмотр логов входа пользователей в базу данных через Telegram")
    print("=" * 70)
    
    # 1. Пользователи с Telegram ID
    get_telegram_users()
    
    # 2. История входов
    get_user_login_history()
    
    # 3. Недавняя активность
    get_recent_activity()
    
    # 4. Анализ лог-файлов
    analyze_log_files()
    
    # 5. Подключения к БД
    get_database_connections()
    
    print("\n" + "=" * 70)
    print("✅ Анализ завершен")
    print("\n💡 Для более детального мониторинга:")
    print("   1. Создайте таблицы user_login_history и user_activity")
    print("   2. Настройте логирование в Telegram боте")
    print("   3. Используйте мониторинг подключений к БД")

if __name__ == "__main__":
    main()
