#!/usr/bin/env python3
"""
Диагностика проблем с получением кодов от Telegram
"""

import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait, PhoneNumberInvalid
import time

API_ID = 35427090
API_HASH = "8e51f69d6828552c2f5acc303dd83743"

async def diagnose():
    print("=" * 80)
    print("ДИАГНОСТИКА ПРОБЛЕМ С TELEGRAM")
    print("=" * 80)

    phone = input("\nВведите номер телефона: ").strip()
    if not phone.startswith("+"):
        phone = "+" + phone.replace(" ", "")

    print(f"\nТестируем: {phone}")
    print("\n1. Проверка подключения к Telegram API...")

    app = Client("test_diag", api_id=API_ID, api_hash=API_HASH, phone_number=phone)

    try:
        await app.connect()
        print("   ✅ Подключение успешно\n")

        print("2. Проверка API credentials...")
        me = await app.get_me()
        if me:
            print(f"   ⚠️  Аккаунт уже авторизован: {me.first_name}")
            print("   Это значит SESSION уже существует!")

            session_string = await app.export_session_string()
            print("\n" + "=" * 80)
            print("🎉 SESSION_STRING найден (аккаунт уже был авторизован!):")
            print("=" * 80)
            print(session_string)
            print("=" * 80)

            # Сохраняем
            with open('.env', 'r') as f:
                lines = f.readlines()

            with open('.env', 'w') as f:
                for line in lines:
                    if line.startswith('SESSION_STRING='):
                        f.write(f'SESSION_STRING={session_string}\n')
                    else:
                        f.write(line)

            print("\n✅ .env обновлен! Можно запускать бота!")
            await app.disconnect()
            return

        print("   ✅ API credentials корректны\n")

        print("3. Отправка запроса кода...")
        start_time = time.time()

        try:
            sent_code = await app.send_code(phone)
            elapsed = time.time() - start_time

            print(f"   ✅ Запрос отправлен за {elapsed:.2f}s")
            print(f"   📱 Тип кода: {sent_code.type}")
            print(f"   ⏱️  Таймаут: {sent_code.timeout if hasattr(sent_code, 'timeout') else 'не указан'}")

            print("\n" + "=" * 80)
            print("ДИАГНОСТИКА ЗАВЕРШЕНА")
            print("=" * 80)
            print("\nРезультат:")
            print("  ✅ Технически всё работает")
            print("  ✅ Запрос кода отправлен в Telegram")
            print("  ❌ НО код не приходит пользователю")

            print("\nВероятные причины:")
            print("  1. 🔥 FLOOD WAIT - слишком много запросов за короткое время")
            print("     Решение: Подождите 12-24 часа и попробуйте снова")
            print("\n  2. 📱 Проблема с номером телефона")
            print("     Решение: Попробуйте другой номер")
            print("\n  3. 🌐 IP-адрес заблокирован Telegram")
            print("     Решение: Попробуйте с другой сети (мобильный интернет)")
            print("\n  4. ⚙️  Настройки аккаунта Telegram")
            print("     Решение: Проверьте Privacy Settings в Telegram")

        except FloodWait as e:
            print(f"   ❌ FLOOD WAIT: Telegram блокирует запросы на {e.value} секунд")
            print(f"      Это {e.value/3600:.1f} часов")
            print("\n   Вы запрашивали коды слишком часто.")
            print(f"   Подождите до {time.strftime('%H:%M', time.localtime(time.time() + e.value))}")

    except PhoneNumberInvalid:
        print(f"   ❌ Неверный формат номера: {phone}")

    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    finally:
        await app.disconnect()

        # Удаляем тестовую сессию
        import os
        try:
            os.remove("test_diag.session")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(diagnose())
