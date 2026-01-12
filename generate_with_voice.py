#!/usr/bin/env python3
"""
Генерация SESSION_STRING с запросом кода через ГОЛОСОВОЙ ЗВОНОК
Если SMS коды не приходят - Telegram может позвонить и продиктовать код
"""

import asyncio
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid

API_ID = 35427090
API_HASH = "8e51f69d6828552c2f5acc303dd83743"

async def generate_with_call():
    print("=" * 80)
    print("Генерация SESSION_STRING через ГОЛОСОВОЙ ВЫЗОВ")
    print("=" * 80)

    phone = input("\nВведите номер телефона (+79261282279): ").strip()

    if not phone.startswith("+"):
        phone = "+" + phone.replace(" ", "")

    print(f"\nИспользуется: {phone}")

    app = Client("my_session", api_id=API_ID, api_hash=API_HASH, phone_number=phone)

    try:
        await app.connect()
        print("\n✅ Подключились к Telegram")

        # Отправляем код
        sent_code = await app.send_code(phone)

        print("\n" + "=" * 80)
        print("📱 Запрос кода отправлен")
        print("=" * 80)

        print("\n⏳ ПОДОЖДИТЕ 1-2 МИНУТЫ")
        print("Если код в Telegram не пришел, Telegram ПОЗВОНИТ вам на телефон")
        print("и автоответчик ПРОДИКТУЕТ код цифрами")
        print("\nПослушайте все до конца - код будет в конце сообщения")
        print("=" * 80)

        code = input("\nВведите код (из Telegram или из звонка): ").strip().replace(" ", "")

        try:
            await app.sign_in(phone, sent_code.phone_code_hash, code)
        except SessionPasswordNeeded:
            password = input("\nВведите пароль 2FA: ")
            await app.check_password(password)
        except PhoneCodeInvalid:
            print("\n❌ Неверный код")
            await app.disconnect()
            return

        session_string = await app.export_session_string()

        print("\n" + "=" * 80)
        print("🎉 УСПЕШНО!")
        print("=" * 80)
        print(session_string)
        print("=" * 80)

        # Сохраняем в .env
        with open('.env', 'r') as f:
            lines = f.readlines()

        with open('.env', 'w') as f:
            for line in lines:
                if line.startswith('SESSION_STRING='):
                    f.write(f'SESSION_STRING={session_string}\n')
                else:
                    f.write(line)

        print("\n✅ .env обновлен!")

        await app.disconnect()

        import os
        try:
            os.remove("my_session.session")
        except:
            pass

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        await app.disconnect()

if __name__ == "__main__":
    asyncio.run(generate_with_call())
