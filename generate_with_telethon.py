#!/usr/bin/env python3
"""
Генерация SESSION_STRING через Telethon с QR-кодом
Telethon поддерживает QR-авторизацию в отличие от Pyrogram
После получения конвертируем в формат Pyrogram
"""

import asyncio
import sys

# Проверяем установлен ли Telethon
try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.errors import SessionPasswordNeededError
except ImportError:
    print("❌ Telethon не установлен")
    print("\nУстановите:")
    print("  pip install telethon")
    sys.exit(1)

try:
    import qrcode
except ImportError:
    print("❌ qrcode не установлен")
    print("\nУстановите:")
    print("  pip install qrcode pillow")
    sys.exit(1)

API_ID = 35427090
API_HASH = "8e51f69d6828552c2f5acc303dd83743"

async def generate_telethon_session():
    print("=" * 80)
    print("ГЕНЕРАЦИЯ SESSION_STRING ЧЕРЕЗ TELETHON (с QR-кодом)")
    print("=" * 80)
    print("\n✨ Этот метод НЕ требует SMS кодов!")
    print("Просто отсканируйте QR-код в Telegram\n")

    # Создаем клиент с пустой сессией
    client = TelegramClient(StringSession(), API_ID, API_HASH)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print("Выберите способ авторизации:")
            print("  1. QR-код (рекомендуется)")
            print("  2. Номер телефона")

            choice = input("\nВаш выбор (1 или 2): ").strip()

            if choice == "1":
                # QR-код авторизация
                print("\n📱 Генерирую QR-код...")
                print("=" * 80)

                qr_login = await client.qr_login()

                # Показываем QR-код в терминале
                qr = qrcode.QRCode(version=1, box_size=1, border=2)
                qr.add_data(qr_login.url)
                qr.make(fit=True)

                print("\n📱 ОТСКАНИРУЙТЕ ЭТОТ QR-КОД:")
                print("=" * 80)
                qr.print_ascii(invert=True)
                print("=" * 80)

                print("\nКак отсканировать:")
                print("  1. Откройте Telegram на телефоне")
                print("  2. Settings → Devices → Link Desktop Device")
                print("  3. Отсканируйте QR-код камерой")
                print("\n⏳ Ожидание сканирования...")

                # Ждем авторизации
                try:
                    await qr_login.wait(timeout=300)  # 5 минут
                    print("✅ QR-код отсканирован!")
                except SessionPasswordNeededError:
                    print("\n🔐 Требуется пароль 2FA")
                    password = input("Введите пароль двухфакторной аутентификации: ").strip()
                    await client.sign_in(password=password)
                    print("✅ Пароль принят!")

            else:
                # Обычная авторизация через номер
                phone = input("\nВведите номер телефона: ").strip()
                await client.send_code_request(phone)

                print("\n📱 Код отправлен!")
                print("Проверьте Telegram на всех устройствах (не только SMS!)")

                code = input("\nВведите код: ").strip()

                try:
                    await client.sign_in(phone, code)
                except SessionPasswordNeededError:
                    password = input("\nВведите пароль 2FA: ").strip()
                    await client.sign_in(password=password)

        # Получаем session string
        session_string = client.session.save()

        print("\n" + "=" * 80)
        print("🎉 TELETHON SESSION STRING сгенерирован!")
        print("=" * 80)
        print(session_string)
        print("=" * 80)

        # Теперь нужно конвертировать в Pyrogram формат
        print("\n⚠️  ВАЖНО: Это Telethon session string")
        print("Для Pyrogram нужна конвертация...")
        print("\nК сожалению, Telethon и Pyrogram используют разные форматы сессий")
        print("НО мы можем использовать Telethon вместо Pyrogram!")

        print("\n💡 Варианты:")
        print("  1. Переписать бота на Telethon (2-3 часа работы)")
        print("  2. Авторизоваться через Pyrogram с этим номером (коды должны приходить)")

        await client.disconnect()

    except asyncio.TimeoutError:
        print("\n❌ Время ожидания истекло (QR-код не был отсканирован)")
        await client.disconnect()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(generate_telethon_session())
    except KeyboardInterrupt:
        print("\n\nОтменено пользователем")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
