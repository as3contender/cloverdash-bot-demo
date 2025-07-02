#!/usr/bin/env python3
"""
Генератор секретного ключа для JWT аутентификации
"""

import secrets
import string
import base64
import os


def generate_secret_key(length: int = 32) -> str:
    """
    Генерация криптографически стойкого секретного ключа

    Args:
        length: Длина ключа в байтах (по умолчанию 32 байта = 256 бит)

    Returns:
        str: Секретный ключ в формате base64
    """
    # Генерируем случайные байты
    random_bytes = secrets.token_bytes(length)

    # Кодируем в base64 для удобства использования
    secret_key = base64.urlsafe_b64encode(random_bytes).decode("utf-8")

    return secret_key


def generate_alphanumeric_key(length: int = 64) -> str:
    """
    Генерация секретного ключа из букв и цифр

    Args:
        length: Длина ключа в символах

    Returns:
        str: Секретный ключ из букв и цифр
    """
    alphabet = string.ascii_letters + string.digits
    secret_key = "".join(secrets.choice(alphabet) for _ in range(length))

    return secret_key


def main():
    """Основная функция генерации ключей"""
    print("🔐 Генератор секретных ключей для JWT аутентификации")
    print("=" * 60)

    # Генерируем несколько вариантов ключей
    print("\n1️⃣ Base64 ключ (рекомендуется):")
    base64_key = generate_secret_key(32)
    print(f"SECRET_KEY={base64_key}")

    print("\n2️⃣ Более длинный Base64 ключ (повышенная безопасность):")
    long_base64_key = generate_secret_key(64)
    print(f"SECRET_KEY={long_base64_key}")

    print("\n3️⃣ Алфавитно-цифровой ключ:")
    alphanumeric_key = generate_alphanumeric_key(64)
    print(f"SECRET_KEY={alphanumeric_key}")

    print("\n" + "=" * 60)
    print("📝 Инструкции:")
    print("1. Выберите один из ключей выше")
    print("2. Добавьте строку SECRET_KEY=... в ваш .env файл")
    print("3. Никогда не делитесь этим ключом!")
    print("4. Используйте разные ключи для разработки и продакшена")

    print("\n⚠️  ВАЖНО:")
    print("- Ключ должен быть уникальным для каждого окружения")
    print("- Смена ключа аннулирует все существующие токены")
    print("- Храните ключ в безопасности!")


if __name__ == "__main__":
    main()
