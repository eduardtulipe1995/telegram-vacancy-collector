#!/usr/bin/env python3
"""
Интерактивная генерация SESSION_STRING с детальной диагностикой
"""

import sys
import asyncio
from pyrogram import Client
from pyrogram.errors import (
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    FloodWait
)

# Credentials из my.telegram.org
API_ID = 35427090
API_HASH = "8e51f69d6828552c2f5acc303dd83743"

async def generate_session():
    print("=" * 80)
    print("Генерация SESSION_STRING для Pyrogram")
    print("=" * 80)

    # Запрашиваем номер телефона
    print("\nВведите номер телефона в международном формате.")
    print("Примеры правильного формата:")
    print("  +79261282279")
    print("  +7 926 128 2279")
    print("  79261282279")
    phone = input("\nВаш номер: ").strip()

    # Нормализуем номер
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not phone.startswith("+"):
        if phone.startswith("7") or phone.startswith("8"):
            phone = "+" + phone if phone.startswith("7") else "+7" + phone[1:]
        else:
            phone = "+" + phone

    print(f"\nИспользуется номер: {phone}")
    print("\n" + "=" * 80)
    print("Подключаемся к Telegram...")
    print("=" * 80)

    app = Client(
        "my_session",
        api_id=API_ID,
        api_hash=API_HASH,
        phone_number=phone,
        workdir="."
    )

    try:
        await app.connect()

        print("\n✅ Успешно подключились к Telegram!")
        print("\nОтправляем запрос на код подтверждения...")

        # Отправляем код
        sent_code = await app.send_code(phone)

        print("\n" + "=" * 80)
        print("📱 КОД ОТПРАВЛЕН!")
        print("=" * 80)
        print(f"\nПроверьте Telegram на номере {phone}")
        print("Код должен прийти от официального аккаунта Telegram")
        print("\nГде искать код:")
        print("  1. Saved Messages (Избранное)")
        print("  2. От аккаунта 'Telegram'")
        print("  3. В уведомлениях")
        print("\nКод выглядит как 5-значное число (например: 12345)")
        print("=" * 80)

        # Запрашиваем код
        code = input("\nВведите код из Telegram: ").strip().replace(" ", "").replace("-", "")

        print("\nПроверяем код...")

        try:
            await app.sign_in(phone, sent_code.phone_code_hash, code)
            print("✅ Код принят!")

        except SessionPasswordNeeded:
            print("\n🔐 Требуется пароль двухфакторной аутентификации (2FA)")
            password = input("Введите пароль 2FA: ").strip()
            await app.check_password(password)
            print("✅ Пароль принят!")

        except PhoneCodeInvalid:
            print("❌ Неверный код! Попробуйте еще раз.")
            await app.disconnect()
            return

        except PhoneCodeExpired:
            print("❌ Код истек! Запустите скрипт заново.")
            await app.disconnect()
            return

        # Получаем session string
        session_string = await app.export_session_string()

        print("\n" + "=" * 80)
        print("🎉 УСПЕШНО! SESSION_STRING сгенерирован:")
        print("=" * 80)
        print(session_string)
        print("=" * 80)

        # Обновляем .env
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
            print("\nСкопируйте SESSION_STRING выше и вставьте в .env файл вручную")

        await app.disconnect()

        # Удаляем временный файл сессии
        import os
        try:
            os.remove("my_session.session")
        except:
            pass

    except PhoneNumberInvalid:
        print(f"\n❌ Неверный формат номера: {phone}")
        print("Попробуйте в формате: +79261282279")
        await app.disconnect()

    except FloodWait as e:
        print(f"\n⏳ Слишком много запросов. Подождите {e.value} секунд и попробуйте снова.")
        await app.disconnect()

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print("\nПопробуйте:")
        print("  1. Проверить интернет соединение")
        print("  2. Убедиться что номер телефона правильный")
        print("  3. Подождать несколько минут и попробовать снова")
        await app.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(generate_session())
    except KeyboardInterrupt:
        print("\n\nОтменено пользователем")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        sys.exit(1)
