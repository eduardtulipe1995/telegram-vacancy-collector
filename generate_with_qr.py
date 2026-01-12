#!/usr/bin/env python3
"""
Генерация SESSION_STRING через QR-КОД
НЕ ТРЕБУЕТСЯ номер телефона и SMS коды!
"""

import asyncio
import qrcode
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded

API_ID = 35427090
API_HASH = "8e51f69d6828552c2f5acc303dd83743"

async def generate_with_qr():
    print("=" * 80)
    print("ГЕНЕРАЦИЯ SESSION_STRING ЧЕРЕЗ QR-КОД")
    print("=" * 80)
    print("\nЭтот метод НЕ требует SMS кодов!")
    print("Просто отсканируйте QR-код в Telegram приложении\n")

    app = Client(
        "qr_session",
        api_id=API_ID,
        api_hash=API_HASH,
        workdir="."
    )

    try:
        await app.connect()
        print("✅ Подключились к Telegram\n")

        # Запрашиваем QR-код для авторизации
        print("Генерируем QR-код для авторизации...")
        print("=" * 80)

        # Используем метод авторизации через QR
        qr_code = await app.qr_login()

        # Получаем URL для QR-кода
        qr_url = qr_code.url

        # Генерируем QR-код в терминале
        qr = qrcode.QRCode(version=1, box_size=1, border=2)
        qr.add_data(qr_url)
        qr.make(fit=True)

        print("\n📱 ОТСКАНИРУЙТЕ ЭТОТ QR-КОД В TELEGRAM:")
        print("=" * 80)
        qr.print_ascii(invert=True)
        print("=" * 80)

        print("\nКак отсканировать:")
        print("  1. Откройте Telegram на телефоне")
        print("  2. Перейдите в Settings → Devices → Link Desktop Device")
        print("  3. Отсканируйте QR-код выше")
        print("\nИли на Desktop:")
        print("  1. Откройте Telegram Desktop")
        print("  2. Settings → Devices → Link Desktop Device")
        print("  3. Отсканируйте камерой телефона")

        print("\n⏳ Ожидаю сканирования QR-кода...")
        print("(QR-код действителен 30 секунд, после обновится)")

        # Ждем авторизации
        while not await qr_code.wait(timeout=30):
            # QR-код истек, генерируем новый
            await qr_code.recreate()
            qr_url = qr_code.url

            qr = qrcode.QRCode(version=1, box_size=1, border=2)
            qr.add_data(qr_url)
            qr.make(fit=True)

            print("\n🔄 QR-код обновлен (старый истек):")
            print("=" * 80)
            qr.print_ascii(invert=True)
            print("=" * 80)

        print("\n✅ QR-код отсканирован!")

        # Проверяем нужен ли пароль 2FA
        try:
            await app.sign_in_qr(qr_code)
        except SessionPasswordNeeded:
            print("\n🔐 Требуется пароль двухфакторной аутентификации")
            password = input("Введите пароль 2FA: ").strip()
            await app.check_password(password)
            print("✅ Пароль принят!")

        # Получаем session string
        session_string = await app.export_session_string()

        print("\n" + "=" * 80)
        print("🎉 УСПЕШНО! SESSION_STRING сгенерирован:")
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

            print("\n✅ Файл .env автоматически обновлен!")
            print("\nТеперь можно запустить бота:")
            print("  python verify_setup.py  # проверка")
            print("  python main.py --test   # тестовый запуск")

        except Exception as e:
            print(f"\n⚠️  Не удалось обновить .env: {e}")
            print("\nСкопируйте SESSION_STRING выше и вставьте в .env файл вручно")

        await app.disconnect()

        # Удаляем временный файл сессии
        import os
        try:
            os.remove("qr_session.session")
        except:
            pass

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print("\nВозможные причины:")
        print("  1. Проблемы с интернет соединением")
        print("  2. API credentials неверны")
        print("  3. Telegram API недоступен")
        await app.disconnect()
        return

if __name__ == "__main__":
    try:
        # Проверяем что qrcode установлен
        import qrcode
    except ImportError:
        print("❌ Библиотека qrcode не установлена")
        print("\nУстановите её:")
        print("  pip install qrcode[pil]")
        exit(1)

    try:
        asyncio.run(generate_with_qr())
    except KeyboardInterrupt:
        print("\n\nОтменено пользователем")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        exit(1)
