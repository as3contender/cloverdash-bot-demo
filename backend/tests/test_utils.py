"""
Утилиты для тестирования backend
"""

import pytest
import asyncio
import subprocess
import sys
from pathlib import Path


def run_tests_by_type(test_type: str = None, coverage: bool = True, verbose: bool = True):
    """
    Запуск тестов по типу

    Args:
        test_type: Тип тестов ('unit', 'integration', 'database', 'llm', 'api')
        coverage: Включить coverage отчет
        verbose: Подробный вывод
    """
    cmd = ["python", "-m", "pytest"]

    if test_type:
        cmd.extend(["-m", test_type])

    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])

    if verbose:
        cmd.append("-v")

    cmd.extend(["--tb=short", "--strict-markers"])

    print(f"Запуск команды: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


def run_unit_tests():
    """Запуск только unit тестов"""
    return run_tests_by_type("unit")


def run_integration_tests():
    """Запуск только integration тестов"""
    return run_tests_by_type("integration")


def run_database_tests():
    """Запуск только database тестов"""
    return run_tests_by_type("database")


def run_llm_tests():
    """Запуск только LLM тестов"""
    return run_tests_by_type("llm")


def run_api_tests():
    """Запуск только API тестов"""
    return run_tests_by_type("api")


def run_all_tests():
    """Запуск всех тестов"""
    return run_tests_by_type()


def check_test_coverage():
    """Проверка покрытия тестами"""
    cmd = ["python", "-m", "pytest", "--cov=.", "--cov-report=html", "--cov-report=term-missing", "--cov-fail-under=80"]

    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


# Функции для быстрого запуска из командной строки
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Запуск тестов backend")
    parser.add_argument(
        "--type", choices=["unit", "integration", "database", "llm", "api"], help="Тип тестов для запуска"
    )
    parser.add_argument("--no-coverage", action="store_true", help="Отключить coverage")
    parser.add_argument("--quiet", action="store_true", help="Тихий режим")

    args = parser.parse_args()

    success = run_tests_by_type(test_type=args.type, coverage=not args.no_coverage, verbose=not args.quiet)

    if success:
        print("✅ Все тесты прошли успешно!")
        sys.exit(0)
    else:
        print("❌ Некоторые тесты провалились!")
        sys.exit(1)
