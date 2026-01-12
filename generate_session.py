#!/usr/bin/env python3
"""
Скрипт для генерации Session String для Pyrogram
Запустите этот скрипт локально для получения SESSION_STRING
"""

from pyrogram import Client

# Ваши данные из .env файла
API_ID = 35427090
API_HASH = "8e51f69d6828552c2f5acc303dd83743"

# Ваш номер телефона в международном формате
# Например: "+79123456789" для российского номера
PHONE_NUMBER = input("Введите ваш номер телефона (в формате +79123456789): ")

print("\nЗапуск Pyrogram клиента...")
print("Telegram отправит вам код подтверждения.")
print("Введите код когда получите его.\n")

# Создаем клиент и получаем session string
with Client("my_account", api_id=API_ID, api_hash=API_HASH, phone_number=PHONE_NUMBER) as app:
    session_string = app.export_session_string()

    print("\n" + "=" * 80)
    print("УСПЕШНО! Session String сгенерирован:")
    print("=" * 80)
    print(session_string)
    print("=" * 80)
    print("\nСкопируйте строку выше и вставьте её в .env файл как значение SESSION_STRING")
    print("=" * 80)
