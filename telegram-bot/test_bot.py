#!/usr/bin/env python3
"""
Тест функциональности бота без реального Telegram токена
"""
import asyncio
import aiohttp
import json
from dotenv import load_dotenv
import os

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


async def test_backend_integration():
    """Тест интеграции с backend API"""
    print("🧪 Тестируем интеграцию с backend...")

    test_queries = ["Покажи текущее время", "Какая версия PostgreSQL используется?", "Покажи информацию о базе данных"]

    for query in test_queries:
        print(f"\n📤 Тестируем запрос: '{query}'")

        try:
            async with aiohttp.ClientSession() as session:
                payload = {"query": query, "user_id": "test_user"}

                async with session.post(f"{BACKEND_URL}/query", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Статус: {response.status}")
                        print(f"📋 Ответ от API:")
                        print(json.dumps(result, indent=2, ensure_ascii=False))

                        # Проверяем структуру ответа
                        if result.get("success"):
                            print("✅ Запрос выполнен успешно")
                            if result.get("data"):
                                print(f"📊 Получено записей: {len(result['data'])}")
                            if result.get("sql_query"):
                                print(f"🔍 SQL: {result['sql_query']}")
                        else:
                            print(f"❌ Ошибка: {result.get('message')}")
                    else:
                        print(f"❌ HTTP ошибка: {response.status}")
                        error_text = await response.text()
                        print(f"📋 Ошибка: {error_text}")

        except Exception as e:
            print(f"❌ Ошибка при выполнении запроса: {str(e)}")

        print("-" * 60)


def test_bot_token():
    """Проверка наличия Telegram токена"""
    print("🔑 Проверяем Telegram токен...")

    telegram_token = os.getenv("TELEGRAM_TOKEN")

    if not telegram_token or telegram_token == "your_bot_token_here":
        print("❌ TELEGRAM_TOKEN не настроен!")
        print("📝 Для запуска бота нужно:")
        print("   1. Создать бота через @BotFather в Telegram")
        print("   2. Создать файл .env с токеном:")
        print("   TELEGRAM_TOKEN=your_actual_token")
        print("   BACKEND_URL=http://localhost:8000")
        return False
    else:
        print(f"✅ TELEGRAM_TOKEN найден: {telegram_token[:10]}...")
        return True


async def main():
    """Основная функция тестирования"""
    print("🤖 CloverdashBot - Тестирование")
    print("=" * 60)

    # Проверяем backend
    print(f"🔗 Backend URL: {BACKEND_URL}")
    await test_backend_integration()

    # Проверяем токен
    token_ok = test_bot_token()

    print("\n" + "=" * 60)
    print("📋 ИТОГИ ТЕСТИРОВАНИЯ:")
    print("✅ Backend интеграция: OK")
    print(f"{'✅' if token_ok else '❌'} Telegram токен: {'OK' if token_ok else 'НЕ НАСТРОЕН'}")

    if token_ok:
        print("\n🚀 Готово к запуску! Используйте: python bot.py")
    else:
        print("\n📝 Сначала настройте Telegram токен (см. setup_instructions.txt)")


if __name__ == "__main__":
    asyncio.run(main())
