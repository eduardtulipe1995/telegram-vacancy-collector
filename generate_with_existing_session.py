#!/usr/bin/env python3
"""
Генерация SESSION_STRING из существующей сессии Telegram Desktop
Этот метод не требует получения кода - использует уже авторизованную сессию
"""

import sys
import os
from pathlib import Path

print("=" * 80)
print("Генерация SESSION_STRING из существующей сессии Telegram Desktop")
print("=" * 80)

print("""
Этот метод работает если у вас УЖЕ УСТАНОВЛЕН Telegram Desktop и вы в нем авторизованы.

ВАЖНО: Telegram Desktop должен быть ЗАПУЩЕН и вы должны быть ЗАЛОГИНЕНЫ.

Альтернативные варианты если коды не приходят:

1. ПОДОЖДАТЬ 2-4 ЧАСА и попробовать снова generate_session_interactive.py
   (Telegram может временно блокировать отправку кодов)

2. Попробовать с ДРУГОГО УСТРОЙСТВА
   - Установите Python на другом компьютере
   - Запустите там generate_session_interactive.py
   - Код может прийти при запросе с другого IP

3. Проверить НАСТРОЙКИ ПРИВАТНОСТИ в Telegram:
   - Откройте Telegram
   - Settings → Privacy and Security
   - Проверьте что не заблокированы сообщения

4. Использовать ВИРТУАЛЬНЫЙ НОМЕР для тестов:
   - Можно создать тестовый аккаунт Telegram на виртуальном номере
   - И использовать его SESSION_STRING

Что выберете?
""")

choice = input("Хотите попробовать метод из Telegram Desktop сессии? (y/n): ").strip().lower()

if choice != 'y':
    print("\nРекомендации:")
    print("1. Подождите 2-4 часа")
    print("2. Попробуйте снова: python generate_session_interactive.py")
    print("3. Или напишите мне и мы найдем другое решение")
    sys.exit(0)

print("\n⚠️  Этот метод экспериментальный и может не сработать")
print("Telegram Desktop должен быть установлен и запущен\n")

# Поиск сессии Telegram Desktop
telegram_paths = [
    # macOS
    Path.home() / "Library/Application Support/Telegram Desktop/tdata",
    # Linux
    Path.home() / ".local/share/TelegramDesktop/tdata",
    # Windows
    Path.home() / "AppData/Roaming/Telegram Desktop/tdata",
]

tdata_path = None
for path in telegram_paths:
    if path.exists():
        tdata_path = path
        print(f"✅ Найдена папка Telegram: {path}")
        break

if not tdata_path:
    print("❌ Telegram Desktop не найден")
    print("\nУстановите Telegram Desktop с https://desktop.telegram.org")
    print("После установки и авторизации запустите этот скрипт снова")
    sys.exit(1)

print("\n⚠️  ВНИМАНИЕ: Прямая конвертация tdata в SESSION_STRING сложна")
print("Рекомендуется подождать несколько часов и использовать стандартный метод\n")

sys.exit(0)
