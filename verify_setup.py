#!/usr/bin/env python3
"""
Скрипт проверки настройки проекта перед запуском
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Проверка наличия и корректности .env файла"""
    print("Проверка .env файла...")

    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env файл не найден!")
        print("   Создайте .env файл на основе .env.example")
        return False

    # Проверка основных переменных
    required_vars = {
        'API_ID': False,
        'API_HASH': False,
        'BOT_TOKEN': False,
        'SESSION_STRING': False,
        'TARGET_USERNAME': False,
        'DATABASE_URL': False,
    }

    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key = line.split('=')[0].strip()
                value = line.split('=', 1)[1].strip()
                if key in required_vars:
                    required_vars[key] = bool(value)

    all_set = True
    for var, is_set in required_vars.items():
        if is_set:
            # Проверка placeholder для SESSION_STRING
            if var == 'SESSION_STRING':
                with open('.env', 'r') as f:
                    content = f.read()
                    if 'PLACEHOLDER' in content:
                        print(f"⚠️  {var} содержит placeholder - запустите generate_session.py")
                        all_set = False
                    else:
                        print(f"✅ {var} установлен")
            else:
                print(f"✅ {var} установлен")
        else:
            print(f"❌ {var} не установлен!")
            all_set = False

    return all_set


def check_csv_file():
    """Проверка наличия CSV файла с каналами"""
    print("\nПроверка CSV файла с каналами...")

    csv_files = list(Path(".").glob("*.csv"))
    if not csv_files:
        print("❌ CSV файл с каналами не найден!")
        return False

    print(f"✅ Найден CSV файл: {csv_files[0].name}")
    return True


def check_dependencies():
    """Проверка установленных зависимостей"""
    print("\nПроверка зависимостей...")

    required_packages = [
        'pyrogram',
        'telegram',
        'apscheduler',
        'sqlalchemy',
        'dotenv',
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} не установлен")
            missing.append(package)

    if missing:
        print("\nУстановите зависимости: pip install -r requirements.txt")
        return False

    return True


def check_project_structure():
    """Проверка структуры проекта"""
    print("\nПроверка структуры проекта...")

    required_dirs = ['config', 'database', 'collectors', 'processors', 'notifiers', 'scheduler', 'utils']
    required_files = ['main.py', 'requirements.txt', 'Procfile']

    all_good = True

    for dir_name in required_dirs:
        if Path(dir_name).is_dir():
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ не найден")
            all_good = False

    for file_name in required_files:
        if Path(file_name).is_file():
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} не найден")
            all_good = False

    return all_good


def main():
    """Главная функция"""
    print("=" * 80)
    print("Проверка настройки Telegram Vacancy Collector Bot")
    print("=" * 80)
    print()

    checks = [
        ("Структура проекта", check_project_structure),
        ("Зависимости", check_dependencies),
        ("CSV файл", check_csv_file),
        (".env файл", check_env_file),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Ошибка при проверке {name}: {e}")
            results.append((name, False))
        print()

    # Итоги
    print("=" * 80)
    print("ИТОГИ ПРОВЕРКИ")
    print("=" * 80)

    all_passed = all(result for _, result in results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print()

    if all_passed:
        print("🎉 Все проверки пройдены! Можно запускать бота.")
        print("\nДля тестового запуска: python main.py --test")
        print("Для обычного запуска: python main.py")
        return 0
    else:
        print("⚠️  Некоторые проверки не прошли. Исправьте проблемы перед запуском.")
        if not any(result for name, result in results if name == ".env файл"):
            print("\n💡 Подсказка: Сначала запустите generate_session.py для получения SESSION_STRING")
        return 1


if __name__ == '__main__':
    sys.exit(main())
