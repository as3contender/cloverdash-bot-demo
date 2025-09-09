#!/usr/bin/env python3
"""
Скрипт для мониторинга логов входа пользователей в базу данных через Telegram в реальном времени
"""

import sys
import os
import time
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

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

def get_recent_logins(minutes=5):
    """Получение недавних входов пользователей"""
    engine = get_db_connection()
    if not engine:
        return []
    
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    ulh.*,
                    u.username,
                    u.full_name,
                    u.telegram_username
                FROM user_login_history ulh
                LEFT JOIN users u ON ulh.user_id = u.id
                WHERE ulh.login_time >= NOW() - INTERVAL ':minutes minutes'
                ORDER BY ulh.login_time DESC
            """)
            
            result = conn.execute(query, {'minutes': minutes})
            return result.fetchall()
            
    except Exception as e:
        print(f"Ошибка при получении недавних входов: {e}")
        return []

def get_recent_activity(minutes=5):
    """Получение недавней активности пользователей"""
    engine = get_db_connection()
    if not engine:
        return []
    
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    ua.*,
                    u.username,
                    u.full_name,
                    u.telegram_username
                FROM user_activity ua
                LEFT JOIN users u ON ua.user_id = u.id
                WHERE ua.activity_time >= NOW() - INTERVAL ':minutes minutes'
                ORDER BY ua.activity_time DESC
            """)
            
            result = conn.execute(query, {'minutes': minutes})
            return result.fetchall()
            
    except Exception as e:
        print(f"Ошибка при получении недавней активности: {e}")
        return []

def get_recent_database_access(minutes=5):
    """Получение недавнего доступа к базе данных"""
    engine = get_db_connection()
    if not engine:
        return []
    
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    dal.*,
                    u.username,
                    u.full_name,
                    u.telegram_username
                FROM database_access_log dal
                LEFT JOIN users u ON dal.user_id = u.id
                WHERE dal.access_time >= NOW() - INTERVAL ':minutes minutes'
                ORDER BY dal.access_time DESC
            """)
            
            result = conn.execute(query, {'minutes': minutes})
            return result.fetchall()
            
    except Exception as e:
        print(f"Ошибка при получении недавнего доступа к БД: {e}")
        return []

def get_active_connections():
    """Получение активных подключений к БД"""
    engine = get_db_connection()
    if not engine:
        return []
    
    try:
        with engine.connect() as conn:
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
                AND usename != 'postgres'
                ORDER BY query_start DESC
            """)
            
            result = conn.execute(query)
            return result.fetchall()
            
    except Exception as e:
        print(f"Ошибка при получении активных подключений: {e}")
        return []

def display_recent_logins(logins):
    """Отображение недавних входов"""
    if logins:
        print(f"🔐 Недавние входы ({len(logins)}):")
        for login in logins:
            status = "✅" if login.success else "❌"
            print(f"   {status} {login.username or login.telegram_username or 'Неизвестно'}")
            print(f"      📱 Telegram: @{login.telegram_username or 'не указан'}")
            print(f"      🕐 Время: {login.login_time}")
            print(f"      🌐 IP: {login.ip_address or 'не указан'}")
            if not login.success and login.error_message:
                print(f"      ❌ Ошибка: {login.error_message}")
            print()

def display_recent_activity(activities):
    """Отображение недавней активности"""
    if activities:
        print(f"📊 Недавняя активность ({len(activities)}):")
        for activity in activities:
            print(f"   🎯 {activity.username or activity.telegram_username or 'Неизвестно'}")
            print(f"      📱 Telegram: @{activity.telegram_username or 'не указан'}")
            print(f"      🕐 Время: {activity.activity_time}")
            print(f"      🔧 Действие: {activity.action}")
            if activity.details:
                print(f"      📝 Детали: {activity.details}")
            print()

def display_recent_database_access(access_logs):
    """Отображение недавнего доступа к БД"""
    if access_logs:
        print(f"🗄️ Недавний доступ к БД ({len(access_logs)}):")
        for access in access_logs:
            status = "✅" if access.success else "❌"
            print(f"   {status} {access.username or access.telegram_username or 'Неизвестно'}")
            print(f"      📱 Telegram: @{access.telegram_username or 'не указан'}")
            print(f"      🕐 Время: {access.access_time}")
            print(f"      🗄️ БД: {access.database_name}.{access.schema_name}.{access.table_name}")
            print(f"      🔧 Операция: {access.operation}")
            if access.query_text:
                query_preview = access.query_text[:50] + "..." if len(access.query_text) > 50 else access.query_text
                print(f"      📝 Запрос: {query_preview}")
            if not access.success and access.error_message:
                print(f"      ❌ Ошибка: {access.error_message}")
            print()

def display_active_connections(connections):
    """Отображение активных подключений"""
    if connections:
        print(f"🔌 Активные подключения ({len(connections)}):")
        for conn in connections:
            print(f"   🆔 PID: {conn.pid}")
            print(f"      👤 Пользователь: {conn.usename}")
            print(f"      📱 Приложение: {conn.application_name or 'не указано'}")
            print(f"      🌐 IP: {conn.client_addr}:{conn.client_port}")
            print(f"      🕐 Начало: {conn.backend_start}")
            if conn.query:
                query_preview = conn.query[:50] + "..." if len(conn.query) > 50 else conn.query
                print(f"      🔍 Запрос: {query_preview}")
            print()

def monitor_telegram_logs(interval=30, duration=300):
    """
    Мониторинг логов Telegram в реальном времени
    
    Args:
        interval: интервал обновления в секундах (по умолчанию 30)
        duration: продолжительность мониторинга в секундах (по умолчанию 300 = 5 минут)
    """
    print("🔍 Мониторинг логов входа пользователей в базу данных через Telegram")
    print("=" * 70)
    print(f"⏱️ Интервал обновления: {interval} секунд")
    print(f"⏰ Продолжительность: {duration} секунд")
    print("🛑 Нажмите Ctrl+C для остановки")
    print("=" * 70)
    
    start_time = time.time()
    last_check_time = datetime.now()
    
    try:
        while time.time() - start_time < duration:
            current_time = datetime.now()
            
            print(f"\n🕐 {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 50)
            
            # Получаем данные за последние 5 минут
            recent_logins = get_recent_logins(5)
            recent_activity = get_recent_activity(5)
            recent_db_access = get_recent_database_access(5)
            active_connections = get_active_connections()
            
            # Отображаем данные
            display_recent_logins(recent_logins)
            display_recent_activity(recent_activity)
            display_recent_database_access(recent_db_access)
            display_active_connections(active_connections)
            
            # Если нет активности, показываем сообщение
            if not recent_logins and not recent_activity and not recent_db_access:
                print("ℹ️ Активность не обнаружена за последние 5 минут")
            
            print(f"⏳ Следующая проверка через {interval} секунд...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n🛑 Мониторинг остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка мониторинга: {e}")
    
    print("\n✅ Мониторинг завершен")

def show_summary():
    """Показать сводку по всем логам"""
    print("📊 Сводка по логам Telegram пользователей")
    print("=" * 50)
    
    # Получаем данные за последний час
    recent_logins = get_recent_logins(60)
    recent_activity = get_recent_activity(60)
    recent_db_access = get_recent_database_access(60)
    
    print(f"🔐 Входы за последний час: {len(recent_logins)}")
    print(f"📊 Активность за последний час: {len(recent_activity)}")
    print(f"🗄️ Доступ к БД за последний час: {len(recent_db_access)}")
    
    # Статистика по пользователям
    if recent_logins:
        unique_users = set()
        for login in recent_logins:
            user = login.username or login.telegram_username or 'Неизвестно'
            unique_users.add(user)
        print(f"👥 Уникальных пользователей: {len(unique_users)}")
    
    # Статистика по операциям
    if recent_db_access:
        operations = {}
        for access in recent_db_access:
            op = access.operation
            operations[op] = operations.get(op, 0) + 1
        print("🔧 Операции с БД:")
        for op, count in operations.items():
            print(f"   {op}: {count}")

def main():
    """Основная функция"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "monitor":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            duration = int(sys.argv[3]) if len(sys.argv) > 3 else 300
            monitor_telegram_logs(interval, duration)
        elif command == "summary":
            show_summary()
        else:
            print("❌ Неизвестная команда")
            print("💡 Использование:")
            print("   python monitor_telegram_logs.py monitor [interval] [duration]")
            print("   python monitor_telegram_logs.py summary")
    else:
        # По умолчанию показываем сводку
        show_summary()
        print("\n💡 Для мониторинга в реальном времени используйте:")
        print("   python monitor_telegram_logs.py monitor")

if __name__ == "__main__":
    main()
