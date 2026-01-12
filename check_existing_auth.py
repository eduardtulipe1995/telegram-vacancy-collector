#!/usr/bin/env python3
"""
Проверка существующих авторизованных сессий
"""

import asyncio
from pyrogram import Client
import os

API_ID = 35427090
API_HASH = "8e51f69d6828552c2f5acc303dd83743"

async def check_auth():
    print("=" * 80)
    print("ПОИСК СУЩЕСТВУЮЩИХ АВТОРИЗОВАННЫХ СЕССИЙ")
    print("=" * 80)

    # Проверяем все возможные файлы сессий
    session_files = [
        'my_account.session',
        'my_session.session',
        'test_session.session',
        'qr_session.session',
        'test_diag.session',
    ]

    print("\n1. Поиск .session файлов...")
    for session_file in session_files:
        if os.path.exists(session_file):
            print(f"   ✅ Найден: {session_file}")

            # Пробуем подключиться
            session_name = session_file.replace('.session', '')
            client = Client(session_name, api_id=API_ID, api_hash=API_HASH)

            try:
                await client.start()

                me = await client.get_me()
                print(f"\n🎉 СЕССИЯ АВТОРИЗОВАНА!")
                print(f"   Пользователь: {me.first_name} (@{me.username})")
                print(f"   Телефон: {me.phone_number}")

                # Экспортируем SESSION_STRING
                session_string = await client.export_session_string()

                print("\n" + "=" * 80)
                print("SESSION_STRING:")
                print("=" * 80)
                print(session_string)
                print("=" * 80)

                # Сохраняем в .env
                try:
                    with open('.env', 'r') as f:
                        lines = f.readlines()

                    with open('.env', 'w') as f:
                        for line in lines:
                            if line.startswith('SESSION_STRING='):
                                f.write(f'SESSION_STRING={session_string}\n')
                            else:
                                f.write(line)

                    print("\n✅ .env файл обновлен!")
                    print("\nМожно запускать бота:")
                    print("  python verify_setup.py")
                    print("  python main.py --test")

                except Exception as e:
                    print(f"\n⚠️  Не удалось обновить .env: {e}")

                await client.stop()
                return True

            except Exception as e:
                print(f"   ❌ Сессия не авторизована или повреждена: {e}")
                await client.stop()
        else:
            print(f"   ⚠️  Не найден: {session_file}")

    print("\n2. Проверка Telegram Desktop...")

    # Проверяем пути Telegram Desktop
    from pathlib import Path

    tdata_paths = [
        Path.home() / "Library/Application Support/Telegram Desktop/tdata",  # macOS
        Path.home() / ".local/share/TelegramDesktop/tdata",  # Linux
        Path.home() / "AppData/Roaming/Telegram Desktop/tdata",  # Windows
    ]

    for path in tdata_paths:
        if path.exists():
            print(f"   ✅ Найден Telegram Desktop: {path}")
            print("   ⚠️  Конвертация tdata в SESSION_STRING сложна")
            print("   Рекомендуется использовать Telethon с QR-кодом")
            break
    else:
        print("   ❌ Telegram Desktop не найден")

    print("\n" + "=" * 80)
    print("РЕЗУЛЬТАТ")
    print("=" * 80)
    print("\n❌ Авторизованные сессии Pyrogram не найдены")
    print("\nВарианты:")
    print("  1. Попробуйте Telethon с QR-кодом: python3 generate_with_telethon.py")
    print("  2. Подождите до завтра и попробуйте снова с Pyrogram")
    print("  3. Попробуйте с мобильного интернета (раздайте WiFi с телефона)")

    return False

if __name__ == "__main__":
    asyncio.run(check_auth())
