#!/usr/bin/env python3
"""
Проверка готовности к запуску бота
Показывает что готово, а что нужно доделать
"""

import os
from pathlib import Path

def check_ready():
    print("=" * 80)
    print("ПРОВЕРКА ГОТОВНОСТИ TELEGRAM VACANCY BOT")
    print("=" * 80)
    print()

    checks = {
        "✅ Готово": [],
        "⏳ Ждет SESSION_STRING": [],
        "❌ Требует действий": []
    }

    # 1. Структура проекта
    required_files = [
        'main.py', 'requirements.txt', '.env', '.env.example',
        'config/settings.py', 'database/connection.py',
        'notifiers/telegram_bot.py', 'collectors/channel_reader.py'
    ]

    all_files_exist = True
    for file in required_files:
        if not Path(file).exists():
            all_files_exist = False
            checks["❌ Требует действий"].append(f"Файл отсутствует: {file}")

    if all_files_exist:
        checks["✅ Готово"].append("Структура проекта")

    # 2. Виртуальное окружение
    if Path('venv').exists():
        checks["✅ Готово"].append("Виртуальное окружение")
    else:
        checks["❌ Требует действий"].append("Создать venv: python3 -m venv venv")

    # 3. Зависимости
    try:
        import pyrogram
        import telegram
        import sqlalchemy
        checks["✅ Готово"].append("Python зависимости")
    except ImportError as e:
        checks["❌ Требует действий"].append(f"Установить зависимости: pip install -r requirements.txt")

    # 4. CSV с каналами
    csv_files = list(Path('.').glob('*.csv'))
    if csv_files:
        checks["✅ Готово"].append(f"CSV файл с каналами ({csv_files[0].name})")
    else:
        checks["❌ Требует действий"].append("CSV файл с каналами не найден")

    # 5. Переменные окружения
    env_vars = {}
    if Path('.env').exists():
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value

    required_env = ['API_ID', 'API_HASH', 'BOT_TOKEN', 'TARGET_USERNAME', 'DATABASE_URL']

    for var in required_env:
        if var in env_vars and env_vars[var]:
            if var == 'SESSION_STRING':
                if 'PLACEHOLDER' in env_vars[var]:
                    checks["⏳ Ждет SESSION_STRING"].append("SESSION_STRING (нужно сгенерировать завтра)")
                else:
                    checks["✅ Готово"].append("SESSION_STRING")
            else:
                checks["✅ Готово"].append(f"{var}")
        else:
            if var == 'SESSION_STRING':
                checks["⏳ Ждет SESSION_STRING"].append("SESSION_STRING (нужно сгенерировать завтра)")
            else:
                checks["❌ Требует действий"].append(f"{var} не установлен в .env")

    # Проверка SESSION_STRING отдельно
    if 'SESSION_STRING' in env_vars:
        if 'PLACEHOLDER' in env_vars['SESSION_STRING']:
            checks["⏳ Ждет SESSION_STRING"].append("SESSION_STRING (есть placeholder)")
        elif not env_vars['SESSION_STRING']:
            checks["⏳ Ждет SESSION_STRING"].append("SESSION_STRING (пустой)")
        else:
            checks["✅ Готово"].append("SESSION_STRING настроен!")

    # 6. Git репозиторий
    if Path('.git').exists():
        checks["✅ Готово"].append("Git репозиторий")
    else:
        checks["❌ Требует действий"].append("Инициализировать git")

    # 7. Целевые пользователи
    if 'TARGET_USERNAME' in env_vars:
        usernames = env_vars['TARGET_USERNAME'].split(',')
        if len(usernames) >= 2:
            checks["✅ Готово"].append(f"Получатели: {', '.join('@' + u.strip() for u in usernames)}")
        else:
            checks["✅ Готово"].append(f"Получатель: @{env_vars['TARGET_USERNAME']}")

    # Вывод результатов
    print()
    for status, items in checks.items():
        if items:
            print(f"{status}:")
            for item in items:
                print(f"  • {item}")
            print()

    # Итоговый статус
    print("=" * 80)
    if checks["❌ Требует действий"]:
        print("⚠️  ТРЕБУЮТСЯ ДЕЙСТВИЯ")
        print("=" * 80)
        print("\nВыполните указанные действия и запустите проверку снова")
        return 1
    elif checks["⏳ Ждет SESSION_STRING"]:
        print("🎯 ПОЧТИ ГОТОВО!")
        print("=" * 80)
        print("\nОсталось только сгенерировать SESSION_STRING завтра:")
        print("  1. Откройте терминал")
        print("  2. cd /Users/eduardepstejn/claude_code/telegram_jobs")
        print("  3. source venv/bin/activate")
        print("  4. python generate_session_interactive.py")
        print("\nПосле этого бот готов к запуску!")
        return 0
    else:
        print("🎉 ВСЁ ГОТОВО К ЗАПУСКУ!")
        print("=" * 80)
        print("\nМожно запускать:")
        print("  python main.py --test   # тестовый запуск")
        print("  python main.py          # обычный запуск")
        return 0


if __name__ == "__main__":
    import sys
    sys.exit(check_ready())
