#!/usr/bin/env python3
"""
Скрипт для быстрого запуска системы логирования схем.

Использование:
    python run_schema_logging.py --user user1 --database demo_db
    python run_schema_logging.py --test
    python run_schema_logging.py --monitor
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime
from typing import List, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('schema_logging_run.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def run_single_user_validation(user_id: str, database_name: str):
    """Запускает валидацию схем для одного пользователя"""
    logger.info(f"🔍 Запуск валидации схем для пользователя {user_id}")
    
    try:
        from schema_validation_logger import SchemaValidationLogger
        
        validator = SchemaValidationLogger()
        result = await validator.validate_schema_access(user_id, database_name)
        
        if "error" in result:
            logger.error(f"❌ Ошибка валидации: {result['error']}")
            return False
        else:
            logger.info(f"✅ Валидация завершена успешно")
            logger.info(f"📊 Найдено схем: {len(result.get('schemas_info', {}))}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка при валидации: {str(e)}")
        return False


async def run_multiple_users_validation(user_ids: List[str], database_name: str):
    """Запускает валидацию схем для нескольких пользователей"""
    logger.info(f"🔍 Запуск валидации схем для {len(user_ids)} пользователей")
    
    try:
        from schema_validation_logger import SchemaValidationLogger
        
        validator = SchemaValidationLogger()
        results = await validator.validate_multiple_users(user_ids, database_name)
        
        # Сохраняем результаты
        validator.save_results_to_file(results)
        
        # Подсчитываем успешные валидации
        successful = sum(1 for result in results.values() if "error" not in result)
        total = len(results)
        
        logger.info(f"📊 Результат: {successful}/{total} пользователей успешно валидированы")
        return successful == total
        
    except Exception as e:
        logger.error(f"❌ Ошибка при валидации нескольких пользователей: {str(e)}")
        return False


async def run_tests():
    """Запускает тесты системы логирования"""
    logger.info("🧪 Запуск тестов системы логирования схем")
    
    try:
        from test_schema_logging import run_all_tests
        success = await run_all_tests()
        
        if success:
            logger.info("🎉 Все тесты пройдены успешно!")
        else:
            logger.error("💥 Некоторые тесты провалены!")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске тестов: {str(e)}")
        return False


async def run_monitoring():
    """Запускает мониторинг схем в реальном времени"""
    logger.info("🔄 Запуск мониторинга схем в реальном времени")
    
    try:
        from schema_monitoring import start_schema_monitoring
        await start_schema_monitoring()
        
    except KeyboardInterrupt:
        logger.info("⏹️  Мониторинг остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка при мониторинге: {str(e)}")


async def run_integration_test():
    """Запускает тест интеграции с существующими сервисами"""
    logger.info("🔗 Запуск теста интеграции")
    
    try:
        from schema_logging_integration import initialize_schema_logging, generate_schema_report
        
        # Инициализируем логирование
        initialize_schema_logging()
        logger.info("✅ Интеграция инициализирована")
        
        # Генерируем отчет
        report = await generate_schema_report()
        
        if "error" in report:
            logger.warning(f"⚠️  Отчет содержит ошибку: {report['error']}")
            logger.info("ℹ️  Это может быть нормально, если база данных недоступна")
        else:
            logger.info(f"📊 Отчет сгенерирован: {report.get('summary', {})}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тесте интеграции: {str(e)}")
        return False


async def run_demo():
    """Запускает демонстрацию функциональности"""
    logger.info("🎭 Запуск демонстрации функциональности")
    
    try:
        from schema_monitoring import schema_monitor
        
        # Демонстрируем различные сценарии
        demo_scenarios = [
            ("user1", "public", "users", "read", True),
            ("user1", "demo1", "bills_view", "read", True),
            ("user2", "public", "orders", "read", False),
            ("user1", "analytics", "reports", "write", True),
            ("user3", "public", "products", "read", True),
        ]
        
        logger.info("📋 Демонстрация логирования доступа к схемам:")
        
        for user_id, schema_name, table_name, access_type, success in demo_scenarios:
            schema_monitor.log_schema_access(
                user_id=user_id,
                schema_name=schema_name,
                table_name=table_name,
                access_type=access_type,
                success=success
            )
            await asyncio.sleep(0.5)  # Небольшая пауза для наглядности
        
        # Показываем статистику
        logger.info("📊 Статистика пользователей:")
        for user_id in ["user1", "user2", "user3"]:
            stats = schema_monitor.get_user_schema_stats(user_id)
            logger.info(f"👤 {user_id}: {stats['total_access_count']} обращений, "
                       f"{len(stats['schemas_accessed'])} схем")
        
        # Генерируем отчет
        schema_monitor.log_daily_schema_report()
        
        logger.info("✅ Демонстрация завершена")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при демонстрации: {str(e)}")
        return False


def parse_arguments():
    """Парсит аргументы командной строки"""
    parser = argparse.ArgumentParser(
        description="Система логирования схем базы данных",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python run_schema_logging.py --user user1 --database demo_db
  python run_schema_logging.py --users user1,user2,user3 --database demo_db
  python run_schema_logging.py --test
  python run_schema_logging.py --monitor
  python run_schema_logging.py --demo
  python run_schema_logging.py --integration
        """
    )
    
    # Основные опции
    parser.add_argument("--user", type=str, help="ID пользователя для валидации")
    parser.add_argument("--users", type=str, help="Список ID пользователей через запятую")
    parser.add_argument("--database", type=str, default="demo_db", help="Имя базы данных")
    
    # Режимы работы
    parser.add_argument("--test", action="store_true", help="Запустить тесты")
    parser.add_argument("--monitor", action="store_true", help="Запустить мониторинг")
    parser.add_argument("--demo", action="store_true", help="Запустить демонстрацию")
    parser.add_argument("--integration", action="store_true", help="Тест интеграции")
    
    # Дополнительные опции
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")
    parser.add_argument("--quiet", "-q", action="store_true", help="Тихий режим")
    
    return parser.parse_args()


async def main():
    """Основная функция"""
    args = parse_arguments()
    
    # Настройка уровня логирования
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    logger.info("🚀 Запуск системы логирования схем")
    logger.info(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    success = True
    
    try:
        if args.test:
            # Запуск тестов
            success = await run_tests()
            
        elif args.monitor:
            # Запуск мониторинга
            await run_monitoring()
            
        elif args.demo:
            # Запуск демонстрации
            success = await run_demo()
            
        elif args.integration:
            # Тест интеграции
            success = await run_integration_test()
            
        elif args.user:
            # Валидация одного пользователя
            success = await run_single_user_validation(args.user, args.database)
            
        elif args.users:
            # Валидация нескольких пользователей
            user_ids = [uid.strip() for uid in args.users.split(",")]
            success = await run_multiple_users_validation(user_ids, args.database)
            
        else:
            # По умолчанию запускаем демонстрацию
            logger.info("ℹ️  Режим не указан, запускаем демонстрацию")
            success = await run_demo()
        
    except KeyboardInterrupt:
        logger.info("⏹️  Выполнение прервано пользователем")
        success = False
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {str(e)}")
        success = False
    
    # Результат
    logger.info("=" * 80)
    if success:
        logger.info("🎉 Выполнение завершено успешно!")
        return 0
    else:
        logger.error("💥 Выполнение завершено с ошибками!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
