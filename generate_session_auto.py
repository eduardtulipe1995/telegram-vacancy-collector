#!/usr/bin/env python3
"""
Автоматический скрипт генерации Session String для Pyrogram
Запуск: python generate_session_auto.py +79123456789
"""

import sys
from pyrogram import Client

# Ваши данные из .env файла
API_ID = 35427090
API_HASH = "8e51f69d6828552c2f5acc303dd83743"

if len(sys.argv) < 2:
    print("Использование: python generate_session_auto.py +79123456789")
    print("Укажите ваш номер телефона в международном формате")
    sys.exit(1)

PHONE_NUMBER = sys.argv[1]

print(f"\nГенерация SESSION_STRING для номера {PHONE_NUMBER}...")
print("Telegram отправит вам код подтверждения.")
print("\n" + "=" * 80)

# Создаем клиент и получаем session string
with Client("my_account", api_id=API_ID, api_hash=API_HASH, phone_number=PHONE_NUMBER) as app:
    session_string = app.export_session_string()

    print("\n" + "=" * 80)
    print("УСПЕШНО! Session String сгенерирован:")
    print("=" * 80)
    print(session_string)
    print("=" * 80)
    print("\nСкопируйте строку выше и выполните:")
    print(f"\nsed -i '' 's/SESSION_STRING=.*/SESSION_STRING={session_string}/' .env")
    print("\nИли вручную замените SESSION_STRING в .env файле")
    print("=" * 80)
