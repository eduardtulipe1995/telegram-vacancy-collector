#!/usr/bin/env python3
"""
Тест API credentials перед генерацией сессии
"""

import sys

print("=" * 80)
print("Проверка API Credentials")
print("=" * 80)

# Запрашиваем credentials
api_id = input("\nВведите ваш API_ID с my.telegram.org: ").strip()
api_hash = input("Введите ваш API_HASH с my.telegram.org: ").strip()
phone = input("Введите номер телефона (например, +79261282279): ").strip()

if not api_id or not api_hash or not phone:
    print("❌ Все поля обязательны!")
    sys.exit(1)

print("\n" + "=" * 80)
print("Проверяем подключение к Telegram...")
print("=" * 80)

try:
    from pyrogram import Client

    # Создаем временный клиент для проверки
    app = Client(
        "test_session",
        api_id=int(api_id),
        api_hash=api_hash,
        phone_number=phone,
        in_memory=True  # Не сохраняем сессию на диск
    )

    print("\n✅ API credentials выглядят корректно")
    print(f"API_ID: {api_id}")
    print(f"API_HASH: {api_hash[:10]}...")
    print(f"Phone: {phone}")

    print("\n" + "=" * 80)
    print("Сейчас попробуем подключиться к Telegram...")
    print("Telegram должен отправить вам код подтверждения")
    print("=" * 80)

    # Пробуем подключиться
    with app:
        session_string = app.export_session_string()

        print("\n" + "=" * 80)
        print("🎉 УСПЕШНО! SESSION_STRING сгенерирован:")
        print("=" * 80)
        print(session_string)
        print("=" * 80)

        # Обновляем .env файл
        print("\nОбновить .env файл автоматически? (y/n): ", end="")
        update = input().strip().lower()

        if update == 'y':
            import os
            from pathlib import Path

            env_file = Path(".env")
            if env_file.exists():
                content = env_file.read_text()

                # Обновляем значения
                lines = []
                for line in content.split('\n'):
                    if line.startswith('API_ID='):
                        lines.append(f'API_ID={api_id}')
                    elif line.startswith('API_HASH='):
                        lines.append(f'API_HASH={api_hash}')
                    elif line.startswith('SESSION_STRING='):
                        lines.append(f'SESSION_STRING={session_string}')
                    else:
                        lines.append(line)

                env_file.write_text('\n'.join(lines))
                print("✅ .env файл обновлен!")
            else:
                print("⚠️  .env файл не найден")

        print("\n" + "=" * 80)
        print("Готово! Теперь можно запускать бота")
        print("=" * 80)

except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    print("\nВозможные причины:")
    print("1. Неправильный API_ID или API_HASH")
    print("2. Номер телефона в неправильном формате")
    print("3. Проблемы с интернет соединением")
    print("\nПопробуйте:")
    print("- Проверьте credentials на https://my.telegram.org")
    print("- Убедитесь что номер в международном формате (+79261282279)")
    sys.exit(1)
